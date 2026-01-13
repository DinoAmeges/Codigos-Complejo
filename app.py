import streamlit as st
import requests
import time
import re
import random
import string
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="RoyPlay Dashboard v16",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "COMMAND CENTER" (ESTILO DASHBOARD) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400&display=swap');
    
    :root {
        --bg-app: #0e1015;
        --bg-panel: #161923;
        --border: #2b303b;
        --accent: #3b82f6; /* Azul Dashboard */
        --success: #10b981; /* Verde Éxito */
        --warning: #f59e0b; /* Naranja Alerta */
        --danger: #ef4444; /* Rojo Error */
        --text-main: #e2e8f0;
        --text-muted: #64748b;
    }

    /* --- FONDO LIMPIO --- */
    .stApp {
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }

    /* --- SIDEBAR ELEGANTE --- */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel);
        border-right: 1px solid var(--border);
    }
    
    /* --- TARJETAS DE MÉTRICAS (KPIs) --- */
    div[data-testid="stMetric"] {
        background-color: var(--bg-panel);
        border: 1px solid var(--border);
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] { font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 800; color: #fff; }

    /* --- CONTENEDOR PRINCIPAL DEL LOG (PANEL) --- */
    .dashboard-panel {
        background-color: var(--bg-panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-top: 20px;
        height: 550px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .panel-header {
        background-color: #1a1e29;
        padding: 15px 20px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .panel-title { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 10px; }
    .status-badge { 
        padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase;
    }
    .badge-online { background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); }
    .badge-offline { background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.2); }

    /* --- CUERPO DE LOGS (TABLA) --- */
    .panel-body {
        flex-grow: 1;
        overflow-y: auto;
        padding: 0;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }

    .log-row {
        display: grid;
        grid-template-columns: 80px 1fr;
        padding: 12px 20px;
        border-bottom: 1px solid var(--border);
        transition: background 0.1s;
    }
    .log-row:hover { background-color: rgba(255,255,255,0.02); }
    .log-time { color: var(--text-muted); font-size: 11px; font-family: 'JetBrains Mono'; }
    .log-content { color: var(--text-main); }

    /* ESTILOS DE TEXTO */
    .highlight-code {
        background: rgba(59, 130, 246, 0.15); color: #60a5fa;
        padding: 2px 8px; border-radius: 4px; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.3);
        font-family: 'JetBrains Mono';
    }
    .t-success { color: var(--success); font-weight: 600; }
    .t-info { color: var(--accent); }
    .t-dim { color: var(--text-muted); }

    /* --- INPUTS --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0e1015 !important;
        border: 1px solid var(--border) !important;
        color: #fff !important;
        border-radius: 6px !important;
    }
    
    /* --- BOTONES --- */
    div.stButton > button {
        border-radius: 6px; font-weight: 600; border: none; height: 42px; width: 100%;
    }
    /* Botón Primario (Azul Dashboard) */
    div.stButton > button:first-child { background: var(--accent); color: white; }
    div.stButton > button:first-child:hover { background: #2563eb; }
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC CORE ---
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
                return True, target, "Connected"
            elif r_t.status_code == 401:
                suffix = ''.join(random.choices(string.digits, k=4))
                return self.connect_smart(f"{user}{suffix}", domain, password)
        return False, None, "API Error"

def analyze(html, text):
    content = (html or "") + " " + (text or "")
    if "hogar" in content.lower() or "household" in content.lower():
        match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content)
        if match: return match.group(0), "LINK DE ACCESO"
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

def log(msg, type="t-dim"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- UI LAYOUT ---

with st.sidebar:
    # Logo
    logo_in = st.text_input("URL Logo", value="https://cdn-icons-png.flaticon.com/512/9070/9070895.png")
    if logo_in: st.image(logo_in, width=100)
    
    st.markdown("### Configuración")
    u_base = st.text_input("Usuario", value="cine")
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("Servidor", st.session_state.dom_cache, index=idx)
    pwd = st.text_input("Clave API", value="123456", type="password")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("Activar"):
        if "Error" in dom_sel: st.error("Sin Red")
        else:
            ok, mail, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = mail
                st.session_state.logs = []
                st.session_state.hits = 0
                log(f"Sistema iniciado en {mail}", "t-success")
                st.rerun()
            else: st.error(msg)
            
    if c2.button("Pausar"):
        st.session_state.active = False
        log("Sistema pausado", "t-dim")
        st.rerun()
        
    if st.button("Limpiar Registros"):
        st.session_state.logs = []
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("RoyPlay Command Center")

# KPI CARDS
k1, k2, k3, k4 = st.columns(4)
k1.metric("Estado del Sistema", "ONLINE" if st.session_state.active else "OFFLINE")
k2.metric("Cuenta Activa", st.session_state.current_email.split('@')[0])
k3.metric("Dominio", st.session_state.current_email.split('@')[-1] if '@' in st.session_state.current_email else "---")
k4.metric("Códigos Detectados", st.session_state.hits)

# PANEL PRINCIPAL
status_badge = "badge-online" if st.session_state.active else "badge-offline"
status_txt = "MONITOREANDO RED" if st.session_state.active else "SISTEMA INACTIVO"

log_html = ""
for l in st.session_state.logs:
    msg_txt = l['m']
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        p = msg_txt.split(": ")
        if len(p)>1: msg_txt = f"{p[0]}: <span class='highlight-code'>{p[1]}</span>"
    log_html += f"<div class='log-row'><div class='log-time'>{l['t']}</div><div class='log-content {l['c']}'>{msg_txt}</div></div>"

st.markdown(f"""
<div class="dashboard-panel">
    <div class="panel-header">
        <div class="panel-title">
            <span style="font-size:18px">📡</span> Registro de Actividad
        </div>
        <div class="status-badge {status_badge}">{status_txt}</div>
    </div>
    <div class="panel-body">
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
                log(f"Correo entrante de: {frm} | {sub}", "t-dim")
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                if dato:
                    st.session_state.hits += 1
                    log(f"¡DATO INTERCEPTADO! {tipo}: {dato}", "t-success")
                    st.toast(f"CLAVE: {dato}", icon="✅")
                else:
                    log("Correo analizado sin datos relevantes", "t-dim")
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    time.sleep(3)
    st.rerun()