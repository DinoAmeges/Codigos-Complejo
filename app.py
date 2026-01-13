import streamlit as st
import requests
import time
import re
import random
import string
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="RoyPlay NEON v15",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "NEON GLASS" (DISEÑO SUPREMO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --glass: rgba(255, 255, 255, 0.05);
        --border: rgba(255, 255, 255, 0.1);
        --primary: #00f2ea;
        --secondary: #ff0050;
        --bg-deep: #050510;
    }

    /* --- FONDO ANIMADO --- */
    .stApp {
        background-color: var(--bg-deep);
        background-image: 
            radial-gradient(at 0% 0%, rgba(118, 75, 255, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(0, 242, 234, 0.15) 0px, transparent 50%);
        font-family: 'Outfit', sans-serif;
    }

    /* --- SIDEBAR DE LUJO --- */
    section[data-testid="stSidebar"] {
        background-color: rgba(5, 5, 16, 0.8);
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--border);
    }

    /* --- MARCO DEL LOGO --- */
    .logo-container {
        display: flex; justify-content: center; margin-bottom: 20px;
    }
    .logo-glow {
        padding: 5px;
        background: linear-gradient(45deg, var(--primary), #764bff);
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(0, 242, 234, 0.2);
    }
    .logo-img {
        border-radius: 12px; background: #000; display: block; width: 100%;
    }

    /* --- INPUTS FLOTANTES --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: var(--glass) !important;
        border: 1px solid var(--border) !important;
        color: #fff !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px);
        transition: 0.3s;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 15px rgba(0, 242, 234, 0.3);
        transform: scale(1.02);
    }

    /* --- BOTONES HOLOGRÁFICOS --- */
    div.stButton > button {
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%);
        border: 1px solid var(--border);
        color: #fff;
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 8px;
        transition: all 0.4s;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background: var(--primary);
        color: #000;
        box-shadow: 0 0 25px var(--primary);
        border-color: var(--primary);
    }
    
    /* Botón Detener (Rojo) */
    div.stButton > button:nth-of-type(1):hover {
        /* Nota: Streamlit aplica estilos en orden, confiamos en la posición */
    }

    /* --- TERMINAL DE VIDRIO --- */
    .glass-terminal {
        background: rgba(10, 10, 20, 0.6);
        border: 1px solid var(--border);
        border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        backdrop-filter: blur(12px);
        overflow: hidden;
        margin-top: 20px;
        position: relative;
    }

    /* HEADER TERMINAL */
    .glass-header {
        background: rgba(255,255,255,0.03);
        padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid var(--border);
    }
    .pulse-dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: var(--primary);
        box-shadow: 0 0 10px var(--primary);
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.5; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1.2); } }
    
    .status-text { font-family: 'JetBrains Mono'; font-size: 10px; color: var(--primary); letter-spacing: 2px; }

    /* CUERPO TERMINAL */
    .glass-body {
        height: 500px;
        padding: 20px;
        overflow-y: auto;
        display: flex; flex-direction: column-reverse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        position: relative;
    }
    
    /* EFECTO SCANLINE (LÍNEA DE LUZ QUE BAJA) */
    .glass-body::after {
        content: " ";
        display: block;
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 2;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
    }

    /* LOGS */
    .log-item {
        padding: 8px 12px;
        margin-bottom: 6px;
        border-radius: 6px;
        background: rgba(255,255,255,0.02);
        border-left: 2px solid transparent;
        display: flex; align-items: center;
        transition: transform 0.2s;
    }
    .log-item:hover { transform: translateX(5px); background: rgba(255,255,255,0.05); }
    
    .t-stamp { color: #666; font-size: 10px; margin-right: 15px; min-width: 60px; }
    
    /* COLORES DE LOG */
    .l-info { border-left-color: #764bff; color: #a5b4fc; }
    .l-succ { border-left-color: var(--primary); color: #fff; text-shadow: 0 0 10px var(--primary); font-weight: bold; background: rgba(0, 242, 234, 0.05); }
    .l-warn { border-left-color: #ffbd2e; color: #fde047; }
    .l-sys { border-left-color: #333; color: #666; font-style: italic; }

    /* DATA BADGE */
    .data-badge {
        background: var(--primary); color: #000;
        padding: 2px 8px; border-radius: 4px; font-weight: 800; margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA (MOTOR v12 STABLE) ---
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
        r_create = requests.post(f"{self.api}/accounts", json=payload, headers=self.headers)
        
        if r_create.status_code in [201, 422]:
            r_token = requests.post(f"{self.api}/token", json=payload, headers=self.headers)
            if r_token.status_code == 200:
                self.token = r_token.json()['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True, target, "LINK ESTABLISHED"
            elif r_token.status_code == 401:
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                new_user = f"{user}_{suffix}"
                return self.connect_smart(new_user, domain, password)
        return False, None, f"API ERROR: {r_create.status_code}"

# --- 4. ANALIZADOR ---
def analyze(html, text):
    content = (html or "") + " " + (text or "")
    if "hogar" in content.lower() or "household" in content.lower() or "update" in content.lower():
        match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"\'<>]+', content)
        if match: return match.group(0), "LINK 🏠"
    codes = re.findall(r'\b\d{4,6}\b', content)
    for c in codes:
        if c not in ["2023", "2024", "2025", "2026"]: return c, "CÓDIGO 🔢"
    return None, None

# --- 5. STATE ---
if 'core' not in st.session_state: st.session_state.core = MailCore()
if 'active' not in st.session_state: st.session_state.active = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'current_email' not in st.session_state: st.session_state.current_email = ""
if 'dom_cache' not in st.session_state:
    doms = st.session_state.core.get_domains()
    st.session_state.dom_cache = doms if doms else ["OFFLINE"]

def log(msg, type="l-info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- 6. UI LAYOUT ---

with st.sidebar:
    # --- LOGO AREA ---
    logo_url = st.text_input("URL LOGO (Opcional)", value="https://cdn-icons-png.flaticon.com/512/3655/3655589.png")
    if logo_url:
        st.markdown(f"""
        <div class="logo-container">
            <div class="logo-glow">
                <img src="{logo_url}" class="logo-img">
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 💠 SYSTEM CONTROL")
    u_base = st.text_input("TARGET ALIAS", value="cine")
    
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("SECURE NODE", st.session_state.dom_cache, index=idx)
    
    pwd = st.text_input("AUTH KEY", value="123456", type="password")
    
    st.markdown("---")
    
    if st.button("🚀 INICIAR ENLACE"):
        if "OFFLINE" in dom_sel: st.error("NETWORK ERROR")
        else:
            ok, final_email, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = final_email
                st.session_state.logs = []
                log(f"ENLACE SEGURO: {final_email}", "l-sys")
                st.rerun()
            else:
                st.error(msg)
                
    if st.button("⛔ CORTAR SEÑAL"):
        st.session_state.active = False
        log("DESCONECTADO", "l-warn")
        st.rerun()
        
    if st.button("🧹 LIMPIAR"):
        st.session_state.logs = []
        st.rerun()

# MAIN PANEL
status_dot = "pulse-dot" if st.session_state.active else ""
status_txt = f"MONITOREANDO: {st.session_state.current_email}" if st.session_state.active else "ESPERANDO CONEXIÓN..."

st.markdown(f"""
<div style="font-family:'Orbitron'; font-size:30px; font-weight:900; color:#fff; text-shadow:0 0 20px rgba(255,255,255,0.5); margin-bottom:10px;">
    ROYPLAY <span style="color:var(--primary)">PRO</span>
</div>
""", unsafe_allow_html=True)

# LOGS RENDER
log_html = ""
if st.session_state.active:
    log_html += f"<div class='log-item l-info'><span class='t-stamp'>LIVE</span>Escaneando red en tiempo real...</div>"

for l in st.session_state.logs:
    msg_txt = l['m']
    if "CÓDIGO" in msg_txt or "LINK" in msg_txt:
        p = msg_txt.split(": ")
        if len(p)>1: msg_txt = f"{p[0]}: <span class='data-badge'>{p[1]}</span>"
    
    log_html += f"<div class='log-item {l['c']}'><span class='t-stamp'>{l['t']}</span>{msg_txt}</div>"

st.markdown(f"""
<div class="glass-terminal">
    <div class="glass-header">
        <div class="{status_dot}"></div>
        <div class="status-text">{status_txt}</div>
        <div style="color:#555">v15.0</div>
    </div>
    <div class="glass-body">
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
                log(f"Recibido: {frm} | {sub}", "l-info")
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                if dato:
                    log(f"¡ENCONTRADO! {tipo}: {dato}", "l-succ")
                    st.toast(f"DATA: {dato}", icon="💎")
                else:
                    log("Mensaje procesado (Sin datos)", "l-sys")
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    time.sleep(3)
    st.rerun()