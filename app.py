import streamlit as st
import requests
import pandas as pd
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="RoyPlay 1SecMail Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PRO (TITANIUM NEON) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;700&family=Inter:wght@400;600&display=swap');
    
    :root {
        --bg-color: #050505;
        --card-bg: #111;
        --accent: #00e5ff; /* Cyan Neón */
        --success: #00ff41; /* Hacker Green */
    }

    .stApp {
        background-color: var(--bg-color);
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; text-transform: uppercase; letter-spacing: 1px; }

    /* Tarjetas */
    .titan-card {
        background: rgba(17, 17, 17, 0.95);
        border: 1px solid #333;
        border-top: 2px solid var(--accent);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: 15px;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background-color: #0e0e0e;
        border: 1px solid #222;
        border-radius: 6px;
        padding: 15px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { color: var(--accent); font-family: 'Chakra Petch'; }

    /* Botones */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #0061ff, #00e5ff);
        color: #000;
        font-weight: 800;
        border: none;
        border-radius: 4px;
        text-transform: uppercase;
        height: 50px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.6);
        transform: scale(1.02);
    }

    /* Terminal */
    .console-log {
        font-family: 'Courier New', monospace;
        background: #000;
        border: 1px solid #222;
        padding: 15px;
        height: 300px;
        overflow-y: auto;
        font-size: 11px;
        color: #ccc;
        border-left: 3px solid var(--success);
    }
    .log-success { color: var(--success); font-weight: bold; }
    .log-info { color: var(--accent); }
    .log-sys { color: #666; }
    
    /* Inputs */
    .stTextInput > div > div > input { background-color: #111; color: white; border: 1px solid #333; }
    .stSelectbox > div > div > div { background-color: #111; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE API CLIENT: 1SECMAIL ---
class OneSecMailClient:
    def __init__(self):
        self.base_url = "https://www.1secmail.com/api/v1/"
        self.session = requests.Session()

    def get_inbox(self, user, domain):
        """Consulta la API para obtener lista de mensajes"""
        try:
            url = f"{self.base_url}?action=getMessages&login={user}&domain={domain}"
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                return r.json() # Devuelve lista de dicts
            return []
        except:
            return []

    def read_message(self, user, domain, msg_id):
        """Descarga el contenido completo del mensaje"""
        try:
            url = f"{self.base_url}?action=readMessage&login={user}&domain={domain}&id={msg_id}"
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

# --- MOTOR DE EXTRACCIÓN UNIVERSAL ---
def extract_smart_data(sender, subject, text_body, html_body):
    """
    Analiza correos de Netflix, Disney, HBO, Prime, Paramount, ViX, etc.
    """
    sender = sender.lower()
    subject = subject.lower()
    
    # 1. Detectar Plataforma
    platform = "General"
    if "netflix" in sender: platform = "Netflix"
    elif "disney" in sender or "star+" in sender: platform = "Disney+"
    elif "hbo" in sender or "max" in sender: platform = "HBO Max"
    elif "amazon" in sender or "prime" in sender: platform = "Prime Video"
    elif "paramount" in sender: platform = "Paramount+"
    elif "vix" in sender: platform = "ViX"

    extracted = None
    tipo = "INFO"

    # 2. Extracción de LINK HOGAR / ACTUALIZAR
    # Prioridad alta: Links de Hogar Netflix/Disney
    if "hogar" in text_body.lower() or "household" in text_body.lower() or "update" in text_body.lower() or "actualizar" in text_body.lower():
        # Patrones de URL específicos
        patterns = [
            r'https://www\.netflix\.com/account/update-household[^\s"]+',
            r'https://www\.disneyplus\.com/travel[^\s"]+',
            r'https://www\.amazon\.com/ap/cvf[^\s"]+'
        ]
        
        # Buscar en HTML primero (más fiable para links)
        if html_body:
            for pat in patterns:
                match = re.search(pat, html_body)
                if match:
                    return match.group(0), "LINK 🏠", platform
        
        # Buscar en Texto si falla HTML
        for pat in patterns:
            match = re.search(pat, text_body)
            if match:
                return match.group(0), "LINK 🏠", platform

    # 3. Extracción de CÓDIGOS NUMÉRICOS
    # Busca códigos de 4 a 6 dígitos (ej: 1234, 123456)
    code_match = re.search(r'\b\d{4,6}\b', text_body)
    if code_match:
        return code_match.group(0), "CÓDIGO 🔢", platform

    return None, "INFO", platform

# --- GESTIÓN DE ESTADO ---
if 'api' not in st.session_state: st.session_state.api = OneSecMailClient()
if 'running' not in st.session_state: st.session_state.running = False
if 'history' not in st.session_state: st.session_state.history = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'logs' not in st.session_state: st.session_state.logs = []

def log(msg, type="info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] {type.upper()}: {msg}")

def toggle():
    if not st.session_state.user_input:
        st.toast("⚠️ Falta el usuario", icon="🚫")
        return
    st.session_state.running = not st.session_state.running
    if st.session_state.running:
        log(f"Iniciando API Monitor: {st.session_state.user_input}@{st.session_state.domain_input}", "success")
    else:
        log("Monitor detenido", "sys")

# --- UI LAYOUT ---
with st.sidebar:
    st.title("ROYPLAY API CORE")
    st.caption("v6.1 Titanium (Updated)")
    st.markdown("---")
    
    st.markdown("### 👤 CUENTA")
    col_u, col_d = st.columns([2, 1])
    st.session_state.user_input = col_u.text_input("Usuario", placeholder="ej: cine1")
    
    # LISTA DE DOMINIOS ACTUALIZADA INCLUYENDO GYMZZ.COM
    dominios_disponibles = [
        "gymzz.com",        # Solicitado
        "1secmail.com",
        "1secmail.net",
        "1secmail.org",
        "wwjmz.com",
        "esiix.com",
        "vardns.com",
        "yoggm.com",
        "vjuum.com",
        "laori.com"
    ]
    st.session_state.domain_input = col_d.selectbox("Dominio", dominios_disponibles)
    
    st.markdown("---")
    st.markdown("### 🧬 PLATAFORMAS")
    st.success("NETFLIX (Code/Hogar)")
    st.info("DISNEY+ / STAR+")
    st.warning("PRIME VIDEO")
    st.error("HBO MAX / VIX")
    
    st.markdown("---")
    if st.button("🗑️ LIMPIAR DATOS"):
        st.session_state.history = []
        st.session_state.processed = []
        st.rerun()

# MAIN SCREEN
st.markdown("## ⚡ INTERCEPTOR 1SECMAIL")

m1, m2, m3 = st.columns(3)
m1.metric("ESTADO", "ACTIVO" if st.session_state.running else "INACTIVO")
m2.metric("CAPTURAS", len(st.session_state.history))
m3.metric("OBJETIVO", f"{st.session_state.user_input}@{st.session_state.domain_input}" if st.session_state.user_input else "---")

c_main, c_log = st.columns([2, 1])

with c_main:
    btn_text = "⏹ ABORTAR SISTEMA" if st.session_state.running else "▶ INICIAR SISTEMA"
    st.button(btn_text, on_click=toggle, use_container_width=True)
    
    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(f"""
            <div class="titan-card">
                <div style="display:flex; justify-content:space-between; color:#666; font-size:12px; margin-bottom:5px;">
                    <span>{item['Hora']}</span>
                    <span style="color:#00e5ff; font-weight:bold;">{item['Plataforma']}</span>
                </div>
                <div style="font-size:14px; color:#ccc;">{item['Asunto']}</div>
                <div style="font-size:28px; font-weight:bold; color:#00ff41; margin:10px 0; letter-spacing:2px; text-shadow: 0 0 10px rgba(0,255,65,0.3);">
                    {item['Dato']}
                </div>
                <div style="font-size:11px; color:#444; border-top:1px solid #222; padding-top:5px; text-transform:uppercase;">
                    DETECTADO: {item['Tipo']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("El sistema está esperando señales de la API...")

with c_log:
    st.markdown("### 📟 SYSTEM LOG")
    log_text = "\n".join(st.session_state.logs)
    st.text_area("Console", log_text, height=450, disabled=True, label_visibility="collapsed")

# --- BUCLE DE PROCESAMIENTO ---
if st.session_state.running:
    with st.spinner("Sincronizando con API 1secmail..."):
        time.sleep(3) # Respeto a la API
        
        inbox = st.session_state.api.get_inbox(st.session_state.user_input, st.session_state.domain_input)
        
        for msg in inbox:
            msg_id = msg['id']
            if msg_id not in st.session_state.processed:
                # Nuevo Mensaje
                sender = msg['from']
                subject = msg['subject']
                log(f"Recibido: {sender}", "info")
                
                # Leer Contenido Completo
                full_msg = st.session_state.api.read_message(st.session_state.user_input, st.session_state.domain_input, msg_id)
                
                if full_msg:
                    text_body = full_msg.get('textBody', '')
                    html_body = full_msg.get('htmlBody', '') # Importante para links
                    
                    # Extraer Dato
                    dato, tipo, plat = extract_smart_data(sender, subject, text_body, html_body)
                    
                    if dato:
                        st.session_state.history.insert(0, {
                            "Hora": datetime.now().strftime("%H:%M:%S"),
                            "Plataforma": plat,
                            "Asunto": subject,
                            "Dato": dato,
                            "Tipo": tipo
                        })
                        st.toast(f"{plat}: {dato}", icon="🔥")
                        log(f"Extracción exitosa: {dato}", "success")
                    else:
                        log("Correo procesado sin datos relevantes.", "sys")
                
                st.session_state.processed.append(msg_id)
        
        st.rerun()