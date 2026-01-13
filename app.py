import streamlit as st
import requests
import pandas as pd
import time
import re
import json
import random
import string
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Terminal Monitor v9",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ESTILO MAC OS TERMINAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;600&display=swap');
    
    /* Fondo General */
    .stApp {
        background-color: #0d1117;
        font-family: 'Inter', sans-serif;
    }

    /* VENTANA MAC OS */
    .mac-window {
        background-color: #1e1e1e;
        border-radius: 10px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        border: 1px solid #333;
        margin-bottom: 20px;
        overflow: hidden;
    }

    /* BARRA DE TÍTULO MAC */
    .mac-header {
        background: linear-gradient(to bottom, #3a3a3a, #2b2b2b);
        padding: 10px 15px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #000;
    }

    /* BOTONES SEMÁFORO */
    .traffic-lights {
        display: flex;
        gap: 8px;
        margin-right: 15px;
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .close { background-color: #ff5f56; border: 1px solid #e0443e; }
    .min { background-color: #ffbd2e; border: 1px solid #dea123; }
    .max { background-color: #27c93f; border: 1px solid #1aab29; }

    /* TÍTULO VENTANA */
    .mac-title {
        color: #999;
        font-family: sans-serif;
        font-size: 13px;
        font-weight: 600;
        text-align: center;
        width: 100%;
        margin-right: 50px; /* Compensar botones */
    }

    /* CONTENIDO TERMINAL */
    .terminal-body {
        padding: 20px;
        color: #fff;
        font-family: 'Fira Code', monospace;
        font-size: 14px;
        min-height: 200px;
    }

    /* MENSAJES */
    .msg-row {
        border-bottom: 1px solid #333;
        padding: 10px 0;
        animation: fadeIn 0.3s ease;
    }
    .highlight { color: #5af78e; font-weight: bold; }
    .warn { color: #f3f99d; }
    .err { color: #ff6b6b; }
    
    /* INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0d1117 !important;
        color: white !important;
        border: 1px solid #333 !important;
        font-family: 'Fira Code', monospace;
    }
    
    /* BOTONES */
    div.stButton > button:first-child {
        background: #2563eb;
        color: white;
        border-radius: 6px;
        border: none;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE DE CONEXIÓN: MAIL.TM (API PROFESIONAL) ---
class MailTmClient:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.token = None

    def get_domains(self):
        """Obtiene dominios activos que NO están bloqueados"""
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return [d['domain'] for d in data['hydra:member']]
            return []
        except:
            return []

    def create_account(self, address, password):
        """Crea una cuenta real en el servidor"""
        payload = {"address": address, "password": password}
        try:
            r = requests.post(f"{self.base_url}/accounts", json=payload, headers=self.headers)
            if r.status_code == 201:
                return True
            elif r.status_code == 422: # Ya existe
                return True
            return False
        except:
            return False

    def login(self, address, password):
        """Obtiene el Token JWT para leer correos"""
        payload = {"address": address, "password": password}
        try:
            r = requests.post(f"{self.base_url}/token", json=payload, headers=self.headers)
            if r.status_code == 200:
                self.token = r.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True
            return False
        except:
            return False

    def get_messages(self):
        """Descarga la bandeja de entrada"""
        if not self.token: return []
        try:
            r = requests.get(f"{self.base_url}/messages", headers=self.headers)
            if r.status_code == 200:
                return r.json()['hydra:member']
            return []
        except:
            return []

    def get_message_detail(self, msg_id):
        """Descarga el contenido completo (HTML)"""
        if not self.token: return None
        try:
            r = requests.get(f"{self.base_url}/messages/{msg_id}", headers=self.headers)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

# --- PARSER INTELIGENTE ---
def extract_code(html_content, text_content):
    """Busca códigos desesperadamente en HTML y Texto"""
    content = (html_content or "") + " " + (text_content or "")
    
    # 1. Buscar Links de Hogar (Prioridad Netflix)
    hogar_pat = r'https://www\.netflix\.com/account/update-household[^\s"]+'
    if match := re.search(hogar_pat, content):
        return match.group(0), "LINK HOGAR 🏠"

    # 2. Buscar Códigos de 4 a 6 dígitos (Amazon, Disney, HBO)
    # Ignoramos años comunes como 2023-2026 para evitar falsos positivos
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]:
            return c, "CÓDIGO 🔢"
            
    return None, "INFO"

# --- ESTADO ---
if 'mail_client' not in st.session_state: st.session_state.mail_client = MailTmClient()
if 'domains' not in st.session_state: st.session_state.domains = st.session_state.mail_client.get_domains()
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'full_email' not in st.session_state: st.session_state.full_email = ""

def log(msg, type="info"):
    icon = "ℹ️"
    css = ""
    if type == "success": icon = "✅"; css = "highlight"
    if type == "error": icon = "❌"; css = "err"
    if type == "warn": icon = "⚠️"; css = "warn"
    
    t = datetime.now().strftime("%H:%M:%S")
    entry = f"<div class='msg-row'><span style='color:#666'>[{t}]</span> {icon} <span class='{css}'>{msg}</span></div>"
    st.session_state.logs.insert(0, entry)

def start_system():
    user = st.session_state.user_in
    dom = st.session_state.dom_in
    pwd = st.session_state.pwd_in
    
    if not user or not dom:
        st.toast("Faltan datos", icon="🚫")
        return

    address = f"{user}@{dom}"
    st.session_state.full_email = address
    
    # 1. Crear Cuenta
    with st.spinner("Creando cuenta segura..."):
        ok_create = st.session_state.mail_client.create_account(address, pwd)
        
    if ok_create:
        # 2. Login
        ok_login = st.session_state.mail_client.login(address, pwd)
        if ok_login:
            st.session_state.is_running = True
            log(f"Sistema iniciado: {address}", "success")
            log("Esperando correos entrantes...", "info")
        else:
            st.error("Error al iniciar sesión en el servidor.")
    else:
        st.error("No se pudo registrar el correo. Intenta otro usuario.")

def stop_system():
    st.session_state.is_running = False
    log("Sistema detenido.", "warn")

# --- UI: SIDEBAR ---
with st.sidebar:
    st.title("⚙️ CONFIG")
    st.markdown("---")
    
    st.session_state.user_in = st.text_input("Usuario", placeholder="netflix-bby")
    
    # Selector de Dominios Vivos
    dom_options = st.session_state.domains if st.session_state.domains else ["cargando..."]
    st.session_state.dom_in = st.selectbox("Dominio (Mail.tm)", dom_options)
    
    # Contraseña generada automáticamente (pero editable)
    def_pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    st.session_state.pwd_in = st.text_input("Password (Auto)", value=def_pwd, type="password")
    
    st.markdown("---")
    st.caption("Estado del Servidor: **Mail.tm API**")
    if not st.session_state.domains:
        st.error("Error conectando a Mail.tm. Verifica tu internet.")

# --- UI: MAIN (MAC OS STYLE) ---

# 1. HEADER CON BOTONES
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("## 🖥️ Terminal Monitor Pro")
with c2:
    if st.session_state.is_running:
        st.button("🔴 DETENER", on_click=stop_system, use_container_width=True)
    else:
        st.button("🟢 INICIAR", on_click=start_system, use_container_width=True)

# 2. VENTANA TERMINAL (OUTPUT)
st.markdown(f"""
<div class="mac-window">
    <div class="mac-header">
        <div class="traffic-lights">
            <div class="dot close"></div>
            <div class="dot min"></div>
            <div class="dot max"></div>
        </div>
        <div class="mac-title">root @ {st.session_state.full_email if st.session_state.full_email else "localhost"} — -zsh</div>
    </div>
    <div class="terminal-body">
        {''.join(st.session_state.logs)}
    </div>
</div>
""", unsafe_allow_html=True)

# 3. VENTANA DE CÓDIGOS (RESULTADOS)
if st.session_state.is_running:
    
    # --- LOOP INVISIBLE ---
    with st.empty():
        # Consultamos mensajes
        msgs = st.session_state.mail_client.get_messages()
        
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                # Nuevo Correo Detectado
                sender = m['from']['address']
                subject = m['subject']
                
                log(f"Recibido de: {sender} | {subject}", "info")
                
                # Descargar detalle (HTML)
                full = st.session_state.mail_client.get_message_detail(m['id'])
                if full:
                    html_body = full.get('html', [''])[0] if full.get('html') else ""
                    text_body = full.get('text', '')
                    
                    # Extracción
                    dato, tipo = extract_code(html_body, text_body)
                    
                    if dato:
                        log(f"¡ENCONTRADO! {tipo}: {dato}", "success")
                        # Mostrar alerta visual grande
                        st.toast(f"Clave: {dato}", icon="🔥")
                    else:
                        log("Correo leído, sin códigos claros.", "warn")
                
                st.session_state.processed.append(m['id'])
        
        # Auto-refresh cada 5s
        time.sleep(5)
        st.rerun()

# Panel de Instrucciones
st.markdown("""
<div style="text-align:center; color:#444; font-size:12px; margin-top:20px;">
    System Status: Online | Protocol: JWT Auth | Provider: Mail.tm
</div>
""", unsafe_allow_html=True)