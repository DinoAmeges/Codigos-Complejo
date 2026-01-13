import streamlit as st
import requests
import time
import re
import random
import string
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="RoyPlay Cyber-Exec v13",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "CYBER-EXECUTIVE" (DISEÑO PREMIUM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* --- FONDO Y BASE --- */
    .stApp {
        background-color: #050509;
        background-image: 
            radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.1) 0px, transparent 50%);
        font-family: 'Rajdhani', sans-serif;
    }

    /* --- LOGO AREA --- */
    .logo-container {
        text-align: center;
        margin-bottom: 20px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .logo-img {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 0 20px rgba(0, 198, 255, 0.2);
    }

    /* --- SIDEBAR PERSONALIZADO --- */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0c;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* INPUTS ESTILIZADOS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: rgba(0, 0, 0, 0.5) !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }

    /* --- TERMINAL WINDOW (LA JOYA DE LA CORONA) --- */
    .terminal-window {
        background: rgba(15, 15, 20, 0.85);
        border-radius: 12px;
        box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.2);
        margin-bottom: 20px;
        font-family: 'JetBrains Mono', monospace;
        overflow: hidden;
        backdrop-filter: blur(20px);
        animation: fadeIn 0.8s ease-out;
    }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

    /* HEADER TERMINAL */
    .terminal-header {
        background: rgba(255, 255, 255, 0.03);
        padding: 12px 20px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .status-dot {
        width: 10px; height: 10px; border-radius: 50%; margin-right: 8px;
    }
    .status-online {
        background-color: #00ff9d;
        box-shadow: 0 0 10px #00ff9d;
        animation: pulse 2s infinite;
    }
    .status-offline { background-color: #ff4757; }

    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    .terminal-title {
        color: #94a3b8; font-size: 12px; letter-spacing: 1px; flex-grow: 1; text-align: center; text-transform: uppercase;
    }

    /* CUERPO TERMINAL */
    .terminal-body {
        padding: 25px;
        height: 500px;
        overflow-y: auto;
        color: #e2e8f0;
        font-size: 13px;
        line-height: 1.8;
        display: flex;
        flex-direction: column-reverse;
        
        /* Scrollbar fina */
        scrollbar-width: thin;
        scrollbar-color: #334155 transparent;
    }
    
    /* LOGS */
    .log-row {
        display: flex; align-items: flex-start; border-bottom: 1px dashed rgba(255,255,255,0.05); padding: 5px 0;
    }
    .log-time { color: #64748b; margin-right: 15px; font-size: 11px; min-width: 65px; }
    
    /* COLORES DE TEXTO */
    .txt-info { color: #38bdf8; } /* Cyan */
    .txt-succ { color: #4ade80; font-weight: bold; text-shadow: 0 0 15px rgba(74, 222, 128, 0.4); } /* Green */
    .txt-warn { color: #fbbf24; } /* Amber */
    .txt-err { color: #f87171; } /* Red */
    .txt-sys { color: #94a3b8; font-style: italic; } /* Slate */

    /* CÓDIGO RESALTADO */
    .secret-badge {
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid #38bdf8;
        color: #fff;
        padding: 2px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 14px;
        margin-left: 10px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }

    /* BOTONES */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none;
        transition: all 0.3s;
        height: 45px;
    }
    
    /* Botón Iniciar (Gradiente Azul-Cian) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
        color: white;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.6);
    }

    </style>
    """, unsafe_allow_html=True)

# --- 3. CLASE MAESTRA DE CONEXIÓN (Mismo motor v12) ---
class MailCore:
    def __init__(self):
        self.api = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json"}
        self.token = None

    def get_domains(self):
        try:
            r = requests.get(f"{self.api}/domains", timeout=4)
            if r.status_code == 200:
                return [d['domain'] for d in r.json()['hydra:member']]
            return []
        except: return []

    def get_messages(self):
        if not self.token: return []
        try:
            r = requests.get(f"{self.api}/messages?page=1", headers=self.headers)
            if r.status_code == 200:
                return r.json()['hydra:member']
            return []
        except: return []

    def get_content(self, msg_id):
        if not self.token: return "", ""
        try:
            r = requests.get(f"{self.api}/messages/{msg_id}", headers=self.headers)
            if r.status_code == 200:
                d = r.json()
                return d.get('html', [''])[0], d.get('text', '')
            return "", ""
        except: return "", ""

    def connect_smart(self, user, domain, password):
        # SISTEMA AUTO-RECOVER (Si falla, crea uno nuevo)
        target = f"{user}@{domain}"
        payload = {"address": target, "password": password}

        r_create = requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
        
        if r_create.status_code in [201, 422]:
            r_token = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            if r_token.status_code == 200:
                self.token = r_token.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, target, "Conectado"
            elif r_token.status_code == 401:
                # OCUPADO -> GENERAR VARIANTE
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                new_user = f"{user}_{suffix}"
                return self.connect_smart(new_user, domain, password)
        
        return False, None, f"Error API: {r_create.status_code}"

# --- 4. MOTOR DE ANÁLISIS ---
def analyze(html, text):
    content = (html or "") + " " + (text or "")
    
    if "hogar" in content.lower() or "household" in content.lower() or "update" in content.lower():
        match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content)
        if match: return match.group(0), "LINK 🏠"

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

if 'dom_cache' not in st.session_state:
    with st.spinner("Iniciando Sistemas Criptográficos..."):
        doms = st.session_state.core.get_domains()
        st.session_state.dom_cache = doms if doms else ["Error Red"]

def log(msg, type="txt-info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- 6. INTERFAZ ---

# --- SIDEBAR (CON LOGO) ---
with st.sidebar:
    # ZONA DE LOGO
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    # URL de logo por defecto (Un escudo cybertech) - Puedes cambiar esta URL
    logo_url = st.text_input("URL del Logo", value="https://cdn-icons-png.flaticon.com/512/2316/2316680.png")
    if logo_url:
        st.image(logo_url, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ CONFIGURACIÓN")
    
    u_base = st.text_input("Usuario Base", value="cine")
    
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("Dominio", st.session_state.dom_cache, index=idx)
    
    pwd = st.text_input("Password", value="123456", type="password")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    if c1.button("▶ INICIAR"):
        if "Error" in dom_sel: st.error("Sin API")
        else:
            ok, final_email, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = final_email
                st.session_state.logs = []
                log(f"Enlace establecido: {final_email}", "txt-succ")
                st.rerun()
            else:
                st.error(msg)
                
    if c2.button("⏹ DETENER"):
        st.session_state.active = False
        log("Enlace terminado.", "txt-warn")
        st.rerun()

    if st.button("🗑️ LIMPIAR PANTALLA"):
        st.session_state.logs = []
        st.rerun()

# --- PANEL PRINCIPAL ---
status_class = "status-online" if st.session_state.active else "status-offline"
status_text = f"CONECTADO A: {st.session_state.current_email}" if st.session_state.active else "DESCONECTADO - ESPERANDO ORDEN"

# Renderizar Terminal
log_html = ""
if st.session_state.active:
    log_html += f"<div class='log-row'><span class='log-time'>NOW</span> <span class='txt-info'>Escaneando puerto 993 (IMAP Secure)...</span></div>"

for l in st.session_state.logs:
    msg_txt = l['m']
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        parts = msg_txt.split(": ")
        if len(parts) > 1:
            msg_txt = f"{parts[0]}: <span class='secret-badge'>{parts[1]}</span>"
            
    log_html += f"<div class='log-row'><span class='log-time'>[{l['t']}]</span> <span class='{l['c']}'>{msg_txt}</span></div>"

st.markdown(f"""
<div class="terminal-window">
    <div class="terminal-header">
        <div class="status-dot {status_class}"></div>
        <div class="terminal-title">{status_text}</div>
    </div>
    <div class="terminal-body">
        {log_html}
    </div>
</div>
""", unsafe_allow_html=True)

# --- BUCLE DE FONDO ---
if st.session_state.active:
    msgs = st.session_state.core.get_messages()
    
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                frm = m['from']['address']
                sub = m['subject']
                log(f"Paquete entrante: {frm} | {sub}", "txt-info")
                
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                
                if dato:
                    log(f"¡CLAVE DESCIFRADA! {tipo}: {dato}", "txt-succ")
                    st.toast(f"CLAVE: {dato}", icon="🔥")
                else:
                    log("Contenido seguro. Sin claves detectadas.", "txt-sys")
                
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    
    time.sleep(3)
    st.rerun()