import streamlit as st
import requests
import time
import re
import random
import string
from datetime import datetime

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="RoyPlay HUD v14",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "AURORA HUD" (DISEÑO SUPREMO) ---
st.markdown("""
    <style>
    /* IMPORTAR FUENTES FUTURISTAS */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Fira+Code:wght@400;600&display=swap');
    
    :root {
        --primary: #00f3ff;
        --secondary: #bc13fe;
        --bg-dark: #020204;
        --panel-bg: rgba(10, 10, 14, 0.85);
        --success: #0aff68;
        --danger: #ff003c;
    }

    /* --- FONDO CIBERNÉTICO --- */
    .stApp {
        background-color: var(--bg-dark);
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px);
        background-size: 40px 40px;
        background-position: center top;
        font-family: 'Fira Code', monospace;
    }
    
    /* Efecto Viñeta Oscura */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at 50% 50%, transparent 20%, #000 90%);
        pointer-events: none;
        z-index: 0;
    }

    /* --- SIDEBAR TECH --- */
    section[data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #1f1f1f;
        box-shadow: 10px 0 30px rgba(0,0,0,0.5);
    }

    /* --- INPUTS ESTILIZADOS --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: #0a0a0a !important;
        color: var(--primary) !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
        font-family: 'Fira Code', monospace !important;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        transition: 0.3s;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0,0,0,0.8);
    }

    /* --- BOTONES NEÓN --- */
    div.stButton > button {
        background: transparent;
        border: 1px solid var(--primary);
        color: var(--primary);
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-radius: 0px;
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
    }
    div.stButton > button:hover {
        background: var(--primary);
        color: #000;
        box-shadow: 0 0 20px var(--primary);
        font-weight: 900;
    }
    /* Botón Detener (Rojo) */
    div.stButton > button:nth-child(1) {
        /* Streamlit no deja seleccionar por nth-child fiable, así que usamos el estilo general para todos */
        /* y confiamos en la lógica visual */
    }

    /* --- LOGO FRAME --- */
    .logo-frame {
        border: 1px solid #333;
        padding: 10px;
        background: #000;
        text-align: center;
        margin-bottom: 20px;
        position: relative;
    }
    .logo-frame::before {
        content: ""; position: absolute; top: -1px; left: -1px; width: 10px; height: 10px;
        border-top: 2px solid var(--primary); border-left: 2px solid var(--primary);
    }
    .logo-frame::after {
        content: ""; position: absolute; bottom: -1px; right: -1px; width: 10px; height: 10px;
        border-bottom: 2px solid var(--primary); border-right: 2px solid var(--primary);
    }

    /* --- TERMINAL HUD --- */
    .hud-container {
        border: 1px solid #333;
        background: var(--panel-bg);
        padding: 2px;
        position: relative;
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
    }
    
    /* Header Terminal */
    .hud-header {
        background: rgba(0, 243, 255, 0.05);
        padding: 10px 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #333;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        color: var(--primary);
        text-shadow: 0 0 5px var(--primary);
    }
    
    /* Cuerpo Terminal */
    .hud-body {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        font-family: 'Fira Code', monospace;
        font-size: 13px;
        color: #ddd;
        display: flex;
        flex-direction: column-reverse;
        background: 
            linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
            linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        background-size: 100% 2px, 3px 100%;
        position: relative;
    }
    
    /* Scrollbar Hacker */
    .hud-body::-webkit-scrollbar { width: 8px; }
    .hud-body::-webkit-scrollbar-track { background: #000; }
    .hud-body::-webkit-scrollbar-thumb { background: #333; border: 1px solid var(--primary); }

    /* LOGS */
    .log-entry {
        border-left: 2px solid #333;
        padding-left: 10px;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        transition: border-color 0.3s;
    }
    .log-entry:hover { border-left-color: var(--primary); background: rgba(0, 243, 255, 0.05); }
    
    .ts { color: #555; font-size: 10px; margin-right: 10px; min-width: 60px; }
    
    .c-info { color: #888; }
    .c-succ { color: var(--success); text-shadow: 0 0 5px var(--success); }
    .c-warn { color: #ffbd2e; }
    .c-sys { color: var(--primary); font-style: italic; }

    /* DECORACIÓN CÓDIGO */
    .glitch-box {
        background: rgba(0, 255, 100, 0.1);
        border: 1px solid var(--success);
        color: var(--success);
        padding: 2px 8px;
        font-weight: bold;
        margin-left: 8px;
        font-family: 'Orbitron';
        letter-spacing: 1px;
    }

    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DEL MOTOR (ROBUSTA) ---
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
        if c not in ["2023", "2024", "2025", "2026"]: return c, "CODE 🔢"
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

def log(msg, type="c-info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {"t": t, "m": msg, "c": type})

# --- 6. UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    # Logo Frame
    st.markdown('<div class="logo-frame">', unsafe_allow_html=True)
    # URL de imagen que parece un logo táctico
    default_logo = "https://cdn-icons-png.flaticon.com/512/1036/1036066.png"
    logo_in = st.text_input("URL LOGO", value=default_logo)
    if logo_in: st.image(logo_in, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ SYSTEM CONTROL")
    u_base = st.text_input("TARGET USER", value="cine")
    
    try: idx = st.session_state.dom_cache.index("virgilian.com")
    except: idx = 0
    dom_sel = st.selectbox("NETWORK NODE", st.session_state.dom_cache, index=idx)
    
    pwd = st.text_input("ACCESS KEY", value="123456", type="password")
    
    st.markdown("---")
    
    if st.button("INITIALIZE"):
        if "OFFLINE" in dom_sel: st.error("NETWORK ERROR")
        else:
            ok, final_email, msg = st.session_state.core.connect_smart(u_base, dom_sel, pwd)
            if ok:
                st.session_state.active = True
                st.session_state.current_email = final_email
                st.session_state.logs = []
                log(f"UPLINK SECURE: {final_email}", "c-sys")
                st.rerun()
            else:
                st.error(msg)
                
    if st.button("TERMINATE"):
        st.session_state.active = False
        log("CONNECTION CLOSED", "c-warn")
        st.rerun()
        
    if st.button("FLUSH LOGS"):
        st.session_state.logs = []
        st.rerun()

# MAIN AREA
status_text = f"// TARGET: {st.session_state.current_email}" if st.session_state.active else "// STANDBY MODE"
status_color = "#0aff68" if st.session_state.active else "#ff003c"

st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px; margin-bottom:20px;">
    <div style="font-family:'Orbitron'; font-size:24px; color:#fff;">ROYPLAY <span style="color:var(--primary)">V14</span></div>
    <div style="font-family:'Fira Code'; font-size:12px; color:{status_color}; border:1px solid {status_color}; padding:5px 10px;">{status_text}</div>
</div>
""", unsafe_allow_html=True)

# LOG RENDERER
log_html = ""
if st.session_state.active:
    log_html += f"<div class='log-entry'><span class='ts'>LIVE</span> <span class='c-sys'>Escaneando frecuencias IMAP en puerto 993...</span></div>"

for l in st.session_state.logs:
    msg_txt = l['m']
    if "CODE" in msg_txt or "LINK" in msg_txt:
        p = msg_txt.split(": ")
        if len(p)>1: msg_txt = f"{p[0]}: <span class='glitch-box'>{p[1]}</span>"
    
    log_html += f"<div class='log-entry'><span class='ts'>{l['t']}</span> <span class='{l['c']}'>{msg_txt}</span></div>"

st.markdown(f"""
<div class="hud-container">
    <div class="hud-header">
        <span>CONSOLE OUTPUT</span>
        <span>SECURE CONNECTION</span>
    </div>
    <div class="hud-body">
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
                log(f"PACKET: {frm} | {sub}", "c-info")
                h, t = st.session_state.core.get_content(m['id'])
                dato, tipo = analyze(h, t)
                if dato:
                    log(f"DECRYPTED! {tipo}: {dato}", "c-succ")
                    st.toast(f"DATA: {dato}", icon="🟢")
                else:
                    log("NO DATA FOUND", "c-info")
                st.session_state.processed.append(m['id'])
                time.sleep(0.1)
                st.rerun()
    time.sleep(3)
    st.rerun()