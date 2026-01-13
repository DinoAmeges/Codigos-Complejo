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
    page_title="Codigos - Complejo Alpha",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "NEON COMMANDER" (ESTILO VIBRANTE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-core: #050509;
        --bg-panel: rgba(20, 20, 30, 0.8);
        --primary: #00f3ff;   /* Cyan Neon */
        --secondary: #7000ff; /* Violeta */
        --success: #00ff9d;   /* Verde Hacker */
        --warning: #ffbd2e;   /* Amarillo */
        --danger: #ff005c;    /* Rojo Neon */
        --text: #e0e0e0;
    }

    /* FONDO */
    .stApp {
        background-color: var(--bg-core);
        background-image: 
            radial-gradient(at 10% 10%, rgba(112, 0, 255, 0.15) 0px, transparent 50%),
            radial-gradient(at 90% 90%, rgba(0, 243, 255, 0.1) 0px, transparent 50%);
        font-family: 'Rajdhani', sans-serif;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0f;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* LOGO BOX */
    .logo-box {
        display: flex; justify-content: center; align-items: center;
        padding: 20px 0; margin-bottom: 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .logo-box img {
        border-radius: 8px; filter: drop-shadow(0 0 10px rgba(0, 243, 255, 0.3));
        max-width: 140px;
    }

    /* TARJETAS DE MÉTRICAS (KPIs) CON GLOW */
    div[data-testid="stMetric"] {
        background-color: var(--bg-panel);
        border: 1px solid rgba(0, 243, 255, 0.2);
        padding: 15px; border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        transition: 0.3s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--primary);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] { color: var(--primary); font-size: 12px; letter-spacing: 1px; }
    div[data-testid="stMetricValue"] { color: #fff; font-size: 28px; font-weight: 700; text-shadow: 0 0 10px rgba(255,255,255,0.3); }

    /* --- BOTONERA CENTRAL --- */
    .stButton button {
        width: 100%; height: 45px; border-radius: 6px;
        font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
        border: none; color: white; transition: 0.3s;
    }
    
    /* Botón 1: INICIAR (Azul Neon) */
    div[data-testid="column"]:nth-of-type(2) .stButton button {
        background: linear-gradient(90deg, #0061ff, #00f3ff);
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
    }
    div[data-testid="column"]:nth-of-type(2) .stButton button:hover {
        box-shadow: 0 0 25px rgba(0, 243, 255, 0.6); transform: scale(1.02);
    }

    /* Botón 2: PAUSAR (Amarillo) */
    div[data-testid="column"]:nth-of-type(3) .stButton button {
        background: rgba(255, 189, 46, 0.1); border: 1px solid var(--warning); color: var(--warning);
    }
    div[data-testid="column"]:nth-of-type(3) .stButton button:hover {
        background: var(--warning); color: #000; box-shadow: 0 0 15px var(--warning);
    }

    /* Botón 3: LIMPIAR (Rojo) */
    div[data-testid="column"]:nth-of-type(4) .stButton button {
        background: rgba(255, 0, 92, 0.1); border: 1px solid var(--danger); color: var(--danger);
    }
    div[data-testid="column"]:nth-of-type(4) .stButton button:hover {
        background: var(--danger); color: #fff; box-shadow: 0 0 15px var(--danger);
    }

    /* CONSOLA DE LOGS */
    .dashboard-console {
        background-color: rgba(10, 10, 15, 0.9);
        border: 1px solid #333;
        border-top: 2px solid var(--secondary);
        border-radius: 8px;
        margin-top: 25px;
        height: 500px;
        display: flex; flex-direction: column; overflow: hidden;
    }
    .console-header {
        background: rgba(112, 0, 255, 0.1); padding: 10px 20px;
        border-bottom: 1px solid rgba(112, 0, 255, 0.2);
        display: flex; justify-content: space-between; align-items: center;
        font-family: 'Rajdhani', sans-serif; font-size: 14px; color: var(--text);
    }
    .console-body {
        flex: 1; overflow-y: auto; padding: 10px;
        font-family: 'JetBrains Mono', monospace; font-size: 12px;
        background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
        background-size: 100% 4px;
    }
    
    /* LOG ROWS (Corregido: sin espacios para evitar renderizado de código) */
    .log-row {
        display: flex; padding: 6px 10px; margin-bottom: 4px; border-radius: 4px;
        align-items: center; border-left: 2px solid transparent;
    }
    .log-row:hover { background: rgba(255,255,255,0.03); }
    .log-ts { color: #666; min-width: 70px; font-size: 11px; }
    
    /* COLORES TEXTO */
    .c-info { color: #a5b4fc; border-left-color: #6366f1; }
    .c-succ { color: var(--success); border-left-color: var(--success); font-weight: bold; text-shadow: 0 0 5px rgba(0,255,157,0.5); }
    .c-warn { color: var(--warning); border-left-color: var(--warning); }
    .c-dim { color: #555; border-left-color: #333; }
    
    /* INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0,0,0,0.5) !important;
        border: 1px solid #333 !important; color: var(--primary) !important;
        border-radius: 4px !important;
    }
    .stTextInput input:focus { border-color: var(--primary) !important; box-shadow: 0 0 10px rgba(0,243,255,0.2); }
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
                return True, target, "Enlace Establecido"
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
    st.session_state.dom_cache = doms if doms else ["Error"]

def log(msg, type="c-dim"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- UI LAYOUT ---

# 1. SIDEBAR
with st.sidebar:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    logo_path = "Logo.png"
    if not os.path.exists(logo_path): logo_path = "Logo.jpg"
    
    if os.path.exists(logo_path):
        st.image(logo_path)
    else:
        st.caption("⚠️ Sube 'logo.png' a la carpeta.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ CONFIGURACIÓN")
    u_base = st.text_input("Usuario Base", value="cine")
    
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("Servidor API", st.session_state.dom_cache, index=idx)
    pwd = st.text_input("Llave Maestra", value="123456", type="password")

# 2. MAIN PANEL

st.markdown("""
<div style="margin-bottom:20px; border-bottom:1px solid #333; padding-bottom:10px;">
    <span style="font-size:24px; font-weight:bold; color:#fff;">CODIGOS STREAMING - COMPLEJO ALPHA</span>
    <span style="font-size:24px; font-weight:bold; color:#00f3ff;"></span>
</div>
""", unsafe_allow_html=True)

# MÉTRICAS
k1, k2, k3, k4 = st.columns(4)
k1.metric("ESTADO", "ONLINE" if st.session_state.active else "OFFLINE")
k2.metric("CUENTA", st.session_state.current_email.split('@')[0])
k3.metric("DOMINIO", st.session_state.current_email.split('@')[-1] if '@' in st.session_state.current_email else "---")
k4.metric("CAPTURAS", st.session_state.hits)

st.write("") 

# BOTONERA CENTRAL (COLOREADA)
c_L, btn1, btn2, btn3, c_R = st.columns([1, 2, 2, 2, 1])

with btn1:
    if st.button("🚀 INICIAR"):
        if "Error" in dom_sel: st.error("Sin Red")
        else:
            ok, mail, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = mail
                st.session_state.logs = []
                st.session_state.hits = 0
                log(f"SISTEMA INICIADO: {mail}", "c-succ")
                st.rerun()
            else: st.error(msg)

with btn2:
    if st.button("⏸ PAUSAR"):
        st.session_state.active = False
        log("SISTEMA PAUSADO", "c-warn")
        st.rerun()

with btn3:
    if st.button("🔥 LIMPIAR"):
        st.session_state.logs = []
        st.rerun()

# CONSOLA
status_txt = "ESCUCHANDO..." if st.session_state.active else "ESPERANDO COMANDO"
status_col = "#00ff9d" if st.session_state.active else "#555"

log_html = ""
for l in st.session_state.logs:
    msg_txt = l['m']
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        p = msg_txt.split(": ")
        if len(p)>1: msg_txt = f"{p[0]}: <span style='background:#00f3ff; color:#000; padding:0 5px; font-weight:bold;'>{p[1]}</span>"
    
    # Generamos la línea HTML en una sola línea para evitar errores de renderizado
    log_html += f"<div class='log-row {l['c']}'><div class='log-ts'>{l['t']}</div><div>{msg_txt}</div></div>"

st.markdown(f"""
<div class="dashboard-console">
    <div class="console-header">
        <span>📠 TERMINAL DE REGISTRO</span>
        <span style="color:{status_col}; font-weight:bold;">● {status_txt}</span>
    </div>
    <div class="console-body">
        {log_html}
    </div>
</div>
""", unsafe_allow_html=True)

# LOOP
if st.session_state.active:
    msgs = st.session_state.core.get_messages()
    if msgs:
        for m in msgs:
            if m['id'] not in st.session_state.processed:
                frm = m['from']['address']
                sub = m['subject']
                log(f"Entrante: {frm} | {sub}", "c-info")
                
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                
                if dato:
                    st.session_state.hits += 1
                    log(f"¡ENCONTRADO! {tipo}: {dato}", "c-succ")
                    st.toast(f"CLAVE: {dato}", icon="💎")
                else:
                    log("Procesado sin datos.", "c-dim")
                
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    time.sleep(3)
    st.rerun()