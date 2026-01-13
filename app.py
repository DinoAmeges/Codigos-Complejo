import streamlit as st
import requests
import time
import re
import random
import string
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="RoyPlay Commander v17",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "COMMANDER" (DASHBOARD PURO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400&display=swap');
    
    :root {
        --bg-core: #09090b;
        --bg-card: #18181b;
        --border: #27272a;
        --primary: #3b82f6;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
    }

    .stApp { background-color: var(--bg-core); font-family: 'Inter', sans-serif; }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #121212;
        border-right: 1px solid var(--border);
    }

    /* LOGO CENTRADO */
    .logo-box {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }
    .logo-box img {
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        max-width: 150px; /* Ajusta esto según tu logo */
    }

    /* METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: var(--bg-card);
        border: 1px solid var(--border);
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricLabel"] { color: #71717a; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
    div[data-testid="stMetricValue"] { color: #f4f4f5; font-size: 26px; font-weight: 800; }

    /* BOTONERA CENTRAL */
    .stButton button {
        width: 100%;
        border-radius: 6px;
        font-weight: 700;
        height: 45px;
        border: 1px solid var(--border);
        transition: transform 0.1s, box-shadow 0.2s;
    }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }

    /* PANEL DE LOGS */
    .dashboard-console {
        background-color: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-top: 20px;
        height: 500px;
        display: flex; flex-direction: column; overflow: hidden;
    }
    .console-header {
        background: #202023; padding: 12px 20px; border-bottom: 1px solid var(--border);
        display: flex; justify-content: space-between; align-items: center;
        font-size: 13px; font-weight: 600; color: #a1a1aa;
    }
    .console-body {
        flex: 1; overflow-y: auto; padding: 0;
        font-family: 'JetBrains Mono', monospace; font-size: 12px;
    }
    
    /* FILAS DE LOG */
    .log-row {
        display: flex; padding: 8px 15px; border-bottom: 1px solid #202023; align-items: center;
    }
    .log-row:nth-child(even) { background: rgba(255,255,255,0.01); }
    .log-ts { color: #52525b; min-width: 70px; margin-right: 10px; }
    
    /* COLORES TEXTO */
    .c-dim { color: #71717a; }
    .c-blue { color: #60a5fa; }
    .c-green { color: #34d399; font-weight: bold; background: rgba(52, 211, 153, 0.1); padding: 2px 6px; border-radius: 4px; }
    .c-red { color: #f87171; }
    
    /* INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #09090b !important;
        border: 1px solid var(--border) !important;
        color: #fff !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA (CORE) ---
class MailCore:
    def __init__(self):
        self.api = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json"}
        self.token = None

    def get_domains(self):
        try:
            r = requests.get(f"{self.api}/domains", timeout=4)
            if r.status_code == 200: return [d['domain'] for d in r.json()['hydra:member']]
            return []
        except: return []

    def get_messages(self):
        if not self.token: return []
        try:
            r = requests.get(f"{self.api}/messages?page=1", headers=self.headers)
            if r.status_code == 200: return r.json()['hydra:member']
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
        target = f"{user}@{domain}"
        payload = {"address": target, "password": password}
        r_c = requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
        if r_c.status_code in [201, 422]:
            r_t = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            if r_t.status_code == 200:
                self.token = r_t.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, target, "Conexión Establecida"
            elif r_t.status_code == 401:
                suffix = ''.join(random.choices(string.digits, k=4))
                return self.connect_smart(f"{user}{suffix}", domain, password)
        return False, None, "Error de API"

def analyze(html, text):
    content = (html or "") + " " + (text or "")
    if "hogar" in content.lower() or "household" in content.lower():
        match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content)
        if match: return match.group(0), "LINK HOGAR"
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]: return c, "CÓDIGO DE ACCESO"
    return None, None

# --- STATE ---
if 'core' not in st.session_state: st.session_state.core = MailCore()
if 'active' not in st.session_state: st.session_state.active = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'current_email' not in st.session_state: st.session_state.current_email = "---"
if 'hits' not in st.session_state: st.session_state.hits = 0

if 'dom_cache' not in st.session_state:
    doms = st.session_state.core.get_domains()
    st.session_state.dom_cache = doms if doms else ["Error de Red"]

def log(msg, type="c-dim"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- UI LAYOUT ---

# 1. SIDEBAR (LOGO + CONFIG)
with st.sidebar:
    # Contenedor del Logo Local Centrado
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    
    # Busca 'logo.png' o 'logo.jpg' localmente
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        logo_path = "logo.jpg"
    
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.warning("⚠️ Sube tu 'logo.png' a la carpeta")
        # Fallback invisible para mantener estructura
        st.markdown(f'<div style="color:#444; font-size:12px">Sin logo.png</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### CONFIGURACIÓN")
    u_base = st.text_input("Usuario", value="cine")
    
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("Servidor", st.session_state.dom_cache, index=idx)
    pwd = st.text_input("Clave API", value="123456", type="password")

# 2. MAIN PANEL

st.markdown("## 🎛️ ROYPLAY COMMAND CENTER")

# MÉTRICAS (Fila 1)
k1, k2, k3, k4 = st.columns(4)
k1.metric("ESTADO", "ACTIVO" if st.session_state.active else "DETENIDO")
k2.metric("CUENTA", st.session_state.current_email.split('@')[0])
k3.metric("DOMINIO", st.session_state.current_email.split('@')[-1] if '@' in st.session_state.current_email else "---")
k4.metric("DETECTADOS", st.session_state.hits)

st.write("") # Espaciador

# BOTONERA CENTRAL (Fila 2 - Centrada)
# Usamos columnas vacías a los lados para centrar los 3 botones
# [Espacio] [Boton1] [Boton2] [Boton3] [Espacio]
c_spacer_L, btn1, btn2, btn3, c_spacer_R = st.columns([2, 2, 2, 2, 2])

with btn1:
    if st.button("▶ INICIAR"):
        if "Error" in dom_sel: st.error("Sin Red")
        else:
            ok, mail, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = mail
                st.session_state.logs = []
                st.session_state.hits = 0
                log(f"Sistema iniciado: {mail}", "c-green")
                st.rerun()
            else: st.error(msg)

with btn2:
    if st.button("⏸ PAUSAR"):
        st.session_state.active = False
        log("Sistema pausado por usuario", "c-dim")
        st.rerun()

with btn3:
    if st.button("🗑️ LIMPIAR"):
        st.session_state.logs = []
        st.rerun()

# CONSOLA DE REGISTROS (Fila 3)
status_txt = "MONITOREANDO TRÁFICO ENTRANTE" if st.session_state.active else "SISTEMA EN ESPERA"
status_color = "#34d399" if st.session_state.active else "#71717a"

log_html = ""
# Construir HTML de logs
for l in st.session_state.logs:
    msg_txt = l['m']
    # Resaltar códigos
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        p = msg_txt.split(": ")
        if len(p)>1: msg_txt = f"{p[0]}: <span style='color:#fff; font-weight:bold'>{p[1]}</span>"
    
    log_html += f"""
    <div class='log-row'>
        <div class='log-ts'>{l['t']}</div>
        <div class='{l['c']}'>{msg_txt}</div>
    </div>
    """

st.markdown(f"""
<div class="dashboard-console">
    <div class="console-header">
        <span>📠 REGISTRO DE ACTIVIDAD</span>
        <span style="color:{status_color}">● {status_txt}</span>
    </div>
    <div class="console-body">
        {log_html}
    </div>
</div>
""", unsafe_allow_html=True)

# LOOP BACKGROUND
if st.session_state.active:
    msgs = st.session_state.core.get_messages()
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                frm = m['from']['address']
                sub = m['subject']
                log(f"Entrante: {frm} | {sub}", "c-blue")
                
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                
                if dato:
                    st.session_state.hits += 1
                    log(f"¡CAPTURADO! {tipo}: {dato}", "c-green")
                    st.toast(f"CLAVE: {dato}", icon="✅")
                else:
                    log("Procesado sin datos clave", "c-dim")
                
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    time.sleep(3)
    st.rerun()