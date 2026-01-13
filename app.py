import streamlit as st
import requests
import pandas as pd
import time
import re
import random
import string
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Terminal Virgilian Fix",
    page_icon="🍏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ESTILO MAC OS TERMINAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;600&display=swap');
    
    .stApp {
        background-color: #0d1117;
        font-family: 'Inter', sans-serif;
    }

    /* VENTANA MAC */
    .mac-window {
        background-color: #1a1b26;
        border-radius: 12px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        border: 1px solid #333;
        margin-bottom: 20px;
        overflow: hidden;
    }

    .mac-header {
        background: #24283b;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #16161e;
    }

    .traffic-lights {
        display: flex;
        gap: 8px;
        margin-right: 15px;
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .close { background-color: #ff5f56; }
    .min { background-color: #ffbd2e; }
    .max { background-color: #27c93f; }

    .mac-title {
        color: #7aa2f7;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 600;
        text-align: center;
        width: 100%;
        margin-right: 50px;
    }

    .terminal-body {
        padding: 20px;
        color: #a9b1d6;
        font-family: 'Fira Code', monospace;
        font-size: 13px;
        min-height: 400px;
        line-height: 1.6;
    }

    /* FILAS DE LOG */
    .log-row {
        border-bottom: 1px dashed #2f3549;
        padding: 8px 0;
        display: flex;
        align-items: center;
    }
    .time-tag { color: #565f89; margin-right: 10px; font-size: 11px; }
    .success { color: #9ece6a; font-weight: bold; }
    .error { color: #f7768e; font-weight: bold; }
    .info { color: #7dcfff; }
    .warn { color: #e0af68; }
    .sys { color: #bb9af7; }
    
    .code-box { 
        background: #16161e; 
        border: 1px solid #7aa2f7; 
        color: #7aa2f7; 
        padding: 5px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        margin-left: 10px;
        box-shadow: 0 0 10px rgba(122, 162, 247, 0.2);
    }

    /* INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #24283b !important;
        color: #c0caf5 !important;
        border: 1px solid #414868 !important;
    }
    
    /* BOTONES */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #3d59a1, #7aa2f7);
        border: none;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENTE MAIL.TM ROBUSTO ---
class MailClient:
    def __init__(self):
        self.api = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.token = None
        self.id = None

    def get_domains(self):
        """Obtiene solo dominios VIVOS"""
        try:
            r = requests.get(f"{self.api}/domains", timeout=5)
            if r.status_code == 200:
                return [d['domain'] for d in r.json()['hydra:member']]
            return []
        except: return []

    def register_and_login(self, address, password):
        # 1. Intentar Crear Cuenta
        payload = {"address": address, "password": password}
        try:
            r = requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
            
            # Si falla, devolvemos el error exacto para que el usuario sepa qué pasó
            if r.status_code not in [201, 422]: # 422 significa "Ya existe", lo cual es bueno
                error_msg = r.json().get('detail', 'Error desconocido')
                return False, f"Error API ({r.status_code}): {error_msg}"
                
        except Exception as e:
            return False, f"Error de Conexión: {e}"

        # 2. Intentar Login (Obtener Token)
        try:
            r = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            if r.status_code == 200:
                self.token = r.json()['token']
                self.id = r.json()['id']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, "Autenticación Exitosa"
            else:
                return False, "Login fallido: Credenciales inválidas"
        except Exception as e:
            return False, str(e)

    def fetch_messages(self):
        if not self.token: return []
        try:
            r = requests.get(f"{self.api}/messages", headers=self.headers)
            if r.status_code == 200:
                return r.json()['hydra:member']
            return []
        except: return []

    def get_full_content(self, msg_id):
        if not self.token: return "", ""
        try:
            r = requests.get(f"{self.api}/messages/{msg_id}", headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                html = data.get('html', [''])[0] if data.get('html') else ""
                text = data.get('text', '')
                return html, text
            return "", ""
        except: return "", ""

# --- PARSER ---
def find_secrets(html, text):
    content = (html or "") + " " + (text or "")
    
    # Links
    if "hogar" in content.lower() or "household" in content.lower() or "update" in content.lower():
        link_pat = r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+'
        match = re.search(link_pat, content)
        if match: return match.group(0), "LINK 🏠"

    # Códigos Numéricos
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]:
            return c, "CÓDIGO 🔢"
            
    return None, None

# --- STATE ---
if 'client' not in st.session_state: st.session_state.client = MailClient()
if 'run' not in st.session_state: st.session_state.run = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []

# Carga inicial de dominios (Solo una vez)
if 'domain_list' not in st.session_state:
    with st.spinner("Conectando con servidor Mail.tm..."):
        doms = st.session_state.client.get_domains()
        if not doms:
            doms = ["Error de conexión"]
        st.session_state.domain_list = doms

def log(msg, type="info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "type": type})

def start():
    usr = st.session_state.u_in
    dom = st.session_state.d_in
    pwd = st.session_state.p_in
    
    if not usr:
        st.toast("⚠️ Escribe un usuario", icon="🚫")
        return
    
    # Validar que no haya seleccionado "Error de conexión"
    if "Error" in dom:
        st.error("No hay dominios disponibles. Recarga la página.")
        return
        
    full = f"{usr}@{dom}"
    
    log(f"Intentando registrar: {full} ...", "sys")
    
    ok, status = st.session_state.client.register_and_login(full, pwd)
    
    if ok:
        st.session_state.run = True
        log(f"✅ {status}", "success")
        log(f"Esperando correos en {full}", "info")
    else:
        st.session_state.run = False
        log(f"❌ {status}", "error")
        st.error(status)

def stop():
    st.session_state.run = False
    log("Proceso detenido por usuario.", "warn")

# --- UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    st.title("🖥️ CONFIG")
    st.markdown("---")
    st.session_state.u_in = st.text_input("Usuario", placeholder="netflix")
    
    # Selector de Dominio
    # Intentamos seleccionar virgilian.com si existe, sino el primero de la lista
    dom_idx = 0
    if "virgilian.com" in st.session_state.domain_list:
        dom_idx = st.session_state.domain_list.index("virgilian.com")
    
    st.session_state.d_in = st.selectbox("Dominio Activo", st.session_state.domain_list, index=dom_idx)
    
    # Password
    if 'auto_pass' not in st.session_state:
        st.session_state.auto_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    st.session_state.p_in = st.text_input("Password", value=st.session_state.auto_pass, type="password")
    
    st.markdown("---")
    if st.button("Limpiar Pantalla"):
        st.session_state.logs = []
        st.rerun()

# MAIN
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("### 🍏 Terminal Monitor Pro")
with c2:
    if st.session_state.run:
        st.button("DETENER", on_click=stop, use_container_width=True)
    else:
        st.button("INICIAR", on_click=start, use_container_width=True)

# TERMINAL WINDOW
log_html = ""
for l in st.session_state.logs:
    css = l['type']
    msg = l['m']
    if "CÓDIGO" in msg or "LINK" in msg:
        parts = msg.split(": ")
        if len(parts) > 1:
            msg = f"{parts[0]}: <span class='code-box'>{parts[1]}</span>"
            
    log_html += f"<div class='log-row'><span class='time-tag'>[{l['t']}]</span> <span class='{css}'>{msg}</span></div>"

st.markdown(f"""
<div class="mac-window">
    <div class="mac-header">
        <div class="traffic-lights">
            <div class="dot close"></div>
            <div class="dot min"></div>
            <div class="dot max"></div>
        </div>
        <div class="mac-title">root @ mail-server — 80x24</div>
    </div>
    <div class="terminal-body">
        {log_html}
    </div>
</div>
""", unsafe_allow_html=True)

# --- BACKGROUND PROCESS ---
if st.session_state.run:
    msgs = st.session_state.client.fetch_messages()
    
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                sender = m['from']['address']
                subj = m['subject']
                log(f"Correo Nuevo: {sender} | {subj}", "info")
                
                html, text = st.session_state.client.get_full_content(m['id'])
                dato, tipo = find_secrets(html, text)
                
                if dato:
                    log(f"¡CAPTURADO! {tipo}: {dato}", "success")
                    st.toast(f"Clave: {dato}", icon="🔥")
                else:
                    log("Correo analizado (Sin datos clave).", "warn")
                
                st.session_state.processed.append(m['id'])
    
    time.sleep(4)
    st.rerun()