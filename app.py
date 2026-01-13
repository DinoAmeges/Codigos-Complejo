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
    page_title="Terminal Monitor v9.2",
    page_icon="🍏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ESTILO MAC OS TERMINAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;600&display=swap');
    
    .stApp { background-color: #0d1117; font-family: 'Inter', sans-serif; }

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

    .traffic-lights { display: flex; gap: 8px; margin-right: 15px; }
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
        max-height: 600px;
        overflow-y: auto;
        line-height: 1.6;
        display: flex;
        flex-direction: column-reverse; /* Hace que lo nuevo salga arriba siempre */
    }

    /* FILAS DE LOG */
    .log-row {
        border-bottom: 1px dashed #2f3549;
        padding: 6px 0;
        display: flex;
        align-items: center;
    }
    .time-tag { color: #565f89; margin-right: 10px; font-size: 11px; }
    .success { color: #9ece6a; font-weight: bold; }
    .error { color: #f7768e; font-weight: bold; }
    .info { color: #7dcfff; }
    .warn { color: #e0af68; }
    
    .code-box { 
        background: #16161e; 
        border: 1px solid #7aa2f7; 
        color: #7aa2f7; 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-weight: bold; 
        margin-left: 10px;
        box-shadow: 0 0 10px rgba(122, 162, 247, 0.2);
    }

    /* INPUTS & UI */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #24283b !important;
        color: #c0caf5 !important;
        border: 1px solid #414868 !important;
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #3d59a1, #7aa2f7);
        border: none;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENTE API ---
class MailClient:
    def __init__(self):
        self.api = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.token = None

    def get_domains(self):
        try:
            r = requests.get(f"{self.api}/domains", timeout=5)
            if r.status_code == 200:
                return [d['domain'] for d in r.json()['hydra:member']]
            return []
        except: return []

    def register_and_login(self, address, password):
        payload = {"address": address, "password": password}
        try:
            requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
            # Intentar Login
            r = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            if r.status_code == 200:
                self.token = r.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, "Conectado"
            return False, f"Error Login: {r.status_code}"
        except Exception as e:
            return False, str(e)

    def fetch_messages(self):
        if not self.token: return []
        try:
            # Pedimos la página 1 de mensajes
            r = requests.get(f"{self.api}/messages?page=1", headers=self.headers)
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

# --- LOGICA ---
def find_secrets(html, text):
    content = (html or "") + " " + (text or "")
    if "hogar" in content.lower() or "household" in content.lower() or "update" in content.lower():
        if match := re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content):
            return match.group(0), "LINK 🏠"
    
    # Busca cualquier número de 4 a 6 dígitos
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]:
            return c, "CÓDIGO 🔢"
    return None, None

# --- ESTADO ---
if 'client' not in st.session_state: st.session_state.client = MailClient()
if 'run' not in st.session_state: st.session_state.run = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'msg_count' not in st.session_state: st.session_state.msg_count = 0

# Carga de dominios
if 'domain_list' not in st.session_state:
    doms = st.session_state.client.get_domains()
    st.session_state.domain_list = doms if doms else ["Error API"]

def log(msg, type="info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "type": type})

# --- UI ---
with st.sidebar:
    st.title("🖥️ CONFIG")
    st.session_state.u_in = st.text_input("Usuario", placeholder="netflix")
    
    # Auto-selección virgilian
    d_idx = 0
    if "virgilian.com" in st.session_state.domain_list:
        d_idx = st.session_state.domain_list.index("virgilian.com")
    st.session_state.d_in = st.selectbox("Dominio", st.session_state.domain_list, index=d_idx)
    
    # Pass
    if 'pass' not in st.session_state:
        st.session_state.pass_val = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    st.session_state.p_in = st.text_input("Pass", value=st.session_state.pass_val, type="password")
    
    if st.button("LIMPIAR"):
        st.session_state.logs = []
        st.session_state.processed = []
        st.rerun()

# --- HEADER Y BOTONES ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"### 🍏 Terminal Pro | Bandeja: **{st.session_state.msg_count}** msgs")
with c2:
    if st.session_state.run:
        if st.button("DETENER", type="primary", use_container_width=True):
            st.session_state.run = False
            st.rerun()
    else:
        if st.button("INICIAR", type="primary", use_container_width=True):
            full = f"{st.session_state.u_in}@{st.session_state.d_in}"
            ok, msg = st.session_state.client.register_and_login(full, st.session_state.p_in)
            if ok:
                st.session_state.run = True
                log(f"Conectado a {full}", "success")
                st.rerun()
            else:
                st.error(msg)

# --- CONTENEDOR DE TERMINAL (PLACEHOLDER) ---
# Esto es vital: creamos un espacio vacío que llenaremos dinámicamente
terminal_placeholder = st.empty()

def render_terminal():
    log_html = ""
    for l in st.session_state.logs:
        css = l['type']
        msg = l['m']
        if "CÓDIGO" in msg or "LINK" in msg:
            parts = msg.split(": ")
            if len(parts) > 1: msg = f"{parts[0]}: <span class='code-box'>{parts[1]}</span>"
        log_html += f"<div class='log-row'><span class='time-tag'>[{l['t']}]</span> <span class='{css}'>{msg}</span></div>"

    terminal_placeholder.markdown(f"""
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

# Renderizar estado inicial
render_terminal()

# --- LOOP PRINCIPAL ---
if st.session_state.run:
    # 1. Obtener mensajes
    msgs = st.session_state.client.fetch_messages()
    st.session_state.msg_count = len(msgs) # Actualizar contador visual
    
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                sender = m['from']['address']
                subj = m['subject']
                
                # AVISAR QUE LLEGÓ ALGO
                log(f"📨 Llegó correo de: {sender}", "info")
                render_terminal() # Actualizar pantalla YA
                
                # LEER CONTENIDO
                html, text = st.session_state.client.get_full_content(m['id'])
                dato, tipo = find_secrets(html, text)
                
                if dato:
                    log(f"🔥 {tipo}: {dato}", "success")
                    st.toast(f"Clave: {dato}", icon="🔥")
                else:
                    log(f"Leído: {subj} (Sin códigos)", "warn")
                
                st.session_state.processed.append(m['id'])
                render_terminal()
    
    # 2. Latido visual (para saber que no está congelado)
    # time.sleep(4)
    # st.rerun()
    
    # TRUCO PRO: Usamos sleep y rerun para bucle continuo
    time.sleep(3)
    st.rerun()