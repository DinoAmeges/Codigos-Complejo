import streamlit as st
import requests
import time
import re
import random
import string
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="Terminal Ops v12",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTÉTICA "MAC OS PRO" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');
    
    /* RESET GENERAL */
    .stApp { background-color: #0d1117; font-family: 'Inter', sans-serif; }

    /* CONTENEDOR TIPO VENTANA */
    .terminal-window {
        background-color: #1e1e1e;
        border-radius: 12px;
        box-shadow: 0 30px 60px rgba(0,0,0,0.5);
        border: 1px solid #333;
        margin-bottom: 20px;
        font-family: 'JetBrains Mono', monospace;
        overflow: hidden;
        animation: slideUp 0.5s ease-out;
    }

    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

    /* BARRA SUPERIOR */
    .terminal-header {
        background: #252526;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #1e1e1e;
    }

    .buttons { display: flex; gap: 8px; margin-right: 15px; }
    .btn { width: 12px; height: 12px; border-radius: 50%; }
    .close { background: #ff5f56; } .min { background: #ffbd2e; } .max { background: #27c93f; }

    .title {
        color: #888; font-size: 12px; width: 100%; text-align: center; margin-right: 50px; font-weight: 600;
    }

    /* CUERPO DE LA TERMINAL */
    .terminal-body {
        padding: 20px;
        height: 450px;
        overflow-y: auto;
        color: #d4d4d4;
        font-size: 13px;
        line-height: 1.6;
        display: flex;
        flex-direction: column-reverse; /* Logs nuevos arriba */
        background: #1e1e1e;
    }

    /* LINEAS DE LOG */
    .line { display: flex; align-items: center; border-bottom: 1px dashed #333; padding: 4px 0; }
    .time { color: #569cd6; margin-right: 10px; font-size: 11px; min-width: 60px; }
    
    /* TIPOS DE MENSAJE */
    .msg-info { color: #9cdcfe; }
    .msg-succ { color: #b5cea8; font-weight: bold; }
    .msg-warn { color: #ce9178; }
    .msg-sys { color: #6a9955; font-style: italic; }
    
    /* DATOS RESALTADOS */
    .highlight {
        background: #264f78;
        color: #fff;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        margin-left: 8px;
        border: 1px solid #7aa2f7;
    }

    /* CURSOR PARPADEANTE */
    .cursor::after {
        content: '▋';
        color: #d4d4d4;
        animation: blink 1s infinite;
    }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

    /* UI DE STREAMLIT */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: #252526 !important; color: #fff !important; border: 1px solid #333 !important;
    }
    div.stButton > button {
        background: #007acc; color: white; border: none; font-weight: bold; transition: 0.2s;
    }
    div.stButton > button:hover { background: #005f9e; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CLASE MAESTRA DE CONEXIÓN ---
class MailCore:
    def __init__(self):
        self.api = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json"}
        self.token = None

    def get_domains(self):
        """Obtiene lista de dominios vivos. Retorna lista vacía si falla."""
        try:
            r = requests.get(f"{self.api}/domains", timeout=4)
            if r.status_code == 200:
                return [d['domain'] for d in r.json()['hydra:member']]
            return []
        except: return []

    def get_messages(self):
        """Descarga bandeja de entrada"""
        if not self.token: return []
        try:
            r = requests.get(f"{self.api}/messages?page=1", headers=self.headers)
            if r.status_code == 200:
                return r.json()['hydra:member']
            return []
        except: return []

    def get_content(self, msg_id):
        """Lee contenido HTML y Texto"""
        if not self.token: return "", ""
        try:
            r = requests.get(f"{self.api}/messages/{msg_id}", headers=self.headers)
            if r.status_code == 200:
                d = r.json()
                return d.get('html', [''])[0], d.get('text', '')
            return "", ""
        except: return "", ""

    def connect_smart(self, user, domain, password):
        """
        LÓGICA 'AUTO-RECOVER':
        1. Intenta crear cuenta.
        2. Si falla (422), intenta login.
        3. Si login falla (401), crea usuario alternativo automáticamente.
        """
        target = f"{user}@{domain}"
        payload = {"address": target, "password": password}

        # Paso 1: Intentar crear
        r_create = requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
        
        # Paso 2: Intentar Login si se creó o ya existía
        if r_create.status_code in [201, 422]:
            r_token = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            
            if r_token.status_code == 200:
                self.token = r_token.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, target, "Conexión exitosa."
            elif r_token.status_code == 401:
                # AQUÍ ESTÁ LA MAGIA: El usuario existe y la clave está mal.
                # Generamos uno nuevo.
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                new_user = f"{user}_{suffix}"
                return self.connect_smart(new_user, domain, password)
        
        return False, None, f"Error API: {r_create.status_code}"

# --- 4. MOTOR DE ANÁLISIS ---
def analyze(html, text):
    content = (html or "") + " " + (text or "")
    
    # Links Hogar
    if "hogar" in content.lower() or "household" in content.lower() or "update" in content.lower():
        match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content)
        if match: return match.group(0), "LINK 🏠"

    # Códigos 4-6 dígitos
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]:
            return c, "CÓDIGO 🔢"
    return None, None

# --- 5. GESTIÓN DE ESTADO ---
if 'core' not in st.session_state: st.session_state.core = MailCore()
if 'active' not in st.session_state: st.session_state.active = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'current_email' not in st.session_state: st.session_state.current_email = ""

# Cache de dominios al iniciar
if 'dom_cache' not in st.session_state:
    with st.spinner("Inicializando Kernel..."):
        doms = st.session_state.core.get_domains()
        st.session_state.dom_cache = doms if doms else ["Error de Red"]

def log(msg, type="msg-info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- 6. INTERFAZ DE USUARIO ---

# SIDEBAR
with st.sidebar:
    st.header("⚙️ CONFIGURACIÓN")
    
    # Usuario Base
    u_base = st.text_input("Usuario Base", value="cine")
    
    # Dominio
    try:
        idx = st.session_state.dom_cache.index("virgilian.com")
    except:
        idx = 0
    dom_sel = st.selectbox("Dominio", st.session_state.dom_cache, index=idx)
    
    # Password
    pwd = st.text_input("Password", value="123456", type="password")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    if c1.button("INICIAR"):
        if "Error" in dom_sel:
            st.error("Sin conexión a API")
        else:
            ok, final_email, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = final_email
                st.session_state.logs = [] # Limpiar logs anteriores
                log(f"Sesión iniciada: {final_email}", "msg-succ")
                log("Sistema de evasión de colisiones: ACTIVO", "msg-sys")
                st.rerun()
            else:
                st.error(msg)
                
    if c2.button("DETENER"):
        st.session_state.active = False
        log("Sesión finalizada.", "msg-warn")
        st.rerun()

    if st.button("LIMPIAR LOGS", type="primary"):
        st.session_state.logs = []
        st.rerun()

# PANEL PRINCIPAL
st.markdown(f"### 🖥️ TERMINAL OPS | ESTADO: {'🟢 ONLINE' if st.session_state.active else '🔴 OFFLINE'}")

# Renderizar Terminal
log_html = ""
# Agregar linea cursor
if st.session_state.active:
    log_html += f"<div class='line'><span class='time'>Now</span> <span class='msg-info cursor'>Escaneando...</span></div>"

for l in st.session_state.logs:
    msg_txt = l['m']
    # Resaltado automático
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        parts = msg_txt.split(": ")
        if len(parts) > 1:
            msg_txt = f"{parts[0]}: <span class='highlight'>{parts[1]}</span>"
            
    log_html += f"<div class='line'><span class='time'>[{l['t']}]</span> <span class='{l['c']}'>{msg_txt}</span></div>"

st.markdown(f"""
<div class="terminal-window">
    <div class="terminal-header">
        <div class="buttons">
            <div class="btn close"></div>
            <div class="btn min"></div>
            <div class="btn max"></div>
        </div>
        <div class="title">root @ {st.session_state.current_email if st.session_state.active else 'localhost'} — zsh</div>
    </div>
    <div class="terminal-body">
        {log_html}
    </div>
</div>
""", unsafe_allow_html=True)

# --- 7. BUCLE DE FONDO ---
if st.session_state.active:
    msgs = st.session_state.core.get_messages()
    
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                # Nuevo Email
                frm = m['from']['address']
                sub = m['subject']
                log(f"Entrante: {frm} | {sub}", "msg-info")
                
                # Análisis Profundo
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                
                if dato:
                    log(f"¡INTERCEPTADO! {tipo}: {dato}", "msg-succ")
                    # Sonido visual (Toast)
                    st.toast(f"CLAVE: {dato}", icon="🔥")
                else:
                    log("Contenido analizado. Sin claves.", "msg-sys")
                
                st.session_state.processed.append(m['id'])