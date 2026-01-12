import streamlit as st
import requests
import pandas as pd
import time
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="RoyPlay Interceptor V5",
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
        --card-bg: #0f0f0f;
        --accent: #00ff41; /* Hacker Green */
        --accent-sec: #00f3ff; /* Cyan */
        --danger: #ff0055;
    }

    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(circle at 50% 0%, #111 0%, #000 70%);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; text-transform: uppercase; letter-spacing: 1px; }

    /* Tarjetas */
    .interceptor-card {
        background: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.05);
        margin-bottom: 15px;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background-color: #0a0a0a;
        border: 1px solid #222;
        border-radius: 6px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] { color: var(--accent); font-family: 'Chakra Petch'; }

    /* Botones */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #008f24, #00ff41);
        color: #000;
        font-weight: 800;
        border: none;
        border-radius: 4px;
        text-transform: uppercase;
        height: 50px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 15px var(--accent);
        transform: scale(1.02);
    }

    /* Consola */
    .console-log {
        font-family: 'Courier New', monospace;
        background: #000;
        border: 1px solid #222;
        padding: 10px;
        height: 250px;
        overflow-y: auto;
        font-size: 11px;
        color: #ccc;
    }
    .log-success { color: var(--accent); font-weight: bold; }
    .log-info { color: var(--accent-sec); }
    .log-warn { color: #ffaa00; }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #111;
        color: white;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE CORE: YOPMAIL SOCKET CLIENT ---
class YopmailSocket:
    def __init__(self):
        self.s = requests.Session()
        # Headers idénticos a un navegador real
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://yopmail.com/en/",
            "Origin": "https://yopmail.com",
            "Connection": "keep-alive"
        })
        self.cookies_ok = False

    def handshake(self):
        """Visita la home para obtener cookies de sesión (yp, consent)"""
        try:
            r = self.s.get("https://yopmail.com/en/", timeout=10)
            if r.status_code == 200:
                # Extraer token 'yj' si existe (a veces Yopmail lo pide)
                self.cookies_ok = True
                return True, "Conexión establecida con Yopmail."
            return False, f"Error Handshake: Status {r.status_code}"
        except Exception as e:
            return False, f"Error de red: {e}"

    def get_inbox(self, user):
        """Obtiene el HTML crudo de la bandeja"""
        if not self.cookies_ok:
            self.handshake()
            
        clean_user = user.split('@')[0]
        timestamp = int(time.time())
        
        # URL de la API interna que carga la lista
        url = f"https://yopmail.com/en/inbox?login={clean_user}&p=1&d=&ctrl=&scrl=&spam=true&v=3.1&r_c=&id="
        
        try:
            r = self.s.get(url, timeout=5)
            soup = BeautifulSoup(r.text, 'lxml')
            
            emails = []
            # Cada correo es un div con clase 'm'
            for msg in soup.find_all('div', class_='m'):
                try:
                    mid = msg['id']
                    sender = msg.find('span', class_='lmf').text.strip()
                    subject = msg.find('div', class_='lms').text.strip()
                    emails.append({'id': mid, 'sender': sender, 'subject': subject})
                except:
                    continue
            return emails
        except:
            return []

    def get_mail_body(self, user, msg_id):
        """Obtiene el contenido completo del correo"""
        clean_user = user.split('@')[0]
        url = f"https://yopmail.com/en/mail?b={clean_user}&id={msg_id}"
        
        try:
            r = self.s.get(url, timeout=5)
            soup = BeautifulSoup(r.text, 'lxml')
            # El cuerpo real está en el div 'mailmillieu'
            body_div = soup.find('div', id='mailmillieu')
            
            if body_div:
                # Obtenemos texto limpio, pero también buscamos en hrefs
                text_content = body_div.get_text(separator=' ', strip=True)
                html_content = str(body_div) # Para buscar enlaces en etiquetas <a>
                return text_content, html_content
            return "", ""
        except:
            return "", ""

# --- MOTOR DE EXTRACCIÓN INTELIGENTE ---
def extract_data(sender, subject, text_body, html_body):
    """
    Analiza el texto y decide qué es (Código o Link) basándose en la plataforma.
    Soporta: Netflix, Disney, HBO, Prime, Paramount, Vix, etc.
    """
    sender = sender.lower()
    subject = subject.lower()
    data_found = None
    data_type = "INFO"
    platform = "General"

    # 1. Identificar Plataforma
    if "netflix" in sender: platform = "Netflix"
    elif "disney" in sender or "star+" in sender: platform = "Disney+"
    elif "hbo" in sender or "max" in sender: platform = "HBO Max"
    elif "amazon" in sender or "prime" in sender: platform = "Prime Video"
    elif "paramount" in sender: platform = "Paramount+"
    elif "vix" in sender: platform = "ViX"
    
    # 2. Lógica de Extracción
    
    # A. Enlaces de Hogar / Actualización (Prioridad)
    if "hogar" in text_body.lower() or "household" in text_body.lower() or "update" in text_body.lower() or "actualizar" in text_body.lower():
        # Regex para buscar enlaces específicos en el HTML
        link_patterns = [
            r'https://www\.netflix\.com/account/update-household[^\s"]+',
            r'https://www\.disneyplus\.com/travel[^\s"]+',
            r'https://www\.amazon\.com/ap/cvf[^\s"]+' # Amazon verify
        ]
        
        for pattern in link_patterns:
            match = re.search(pattern, html_body)
            if match:
                return match.group(0), "LINK 🏠", platform

    # B. Códigos Numéricos
    # Buscamos números de 4 a 6 dígitos aislados
    # Excluimos años (2023, 2024) si es posible, pero regex simple suele bastar
    code_match = re.search(r'\b\d{4,6}\b', text_body)
    if code_match:
        return code_match.group(0), "CÓDIGO 🔢", platform

    return None, None, platform

# --- GESTIÓN DE ESTADO ---
if 'client' not in st.session_state: st.session_state.client = YopmailSocket()
if 'running' not in st.session_state: st.session_state.running = False
if 'history' not in st.session_state: st.session_state.history = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'logs' not in st.session_state: st.session_state.logs = []

def log(msg, type="info"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] {type.upper()}: {msg}")

def toggle():
    if not st.session_state.target:
        st.toast("⚠️ Faltó el usuario", icon="🚫")
        return
    st.session_state.running = not st.session_state.running
    if st.session_state.running:
        ok, msg = st.session_state.client.handshake()
        if ok:
            log(f"Iniciando escucha en: {st.session_state.target}", "success")
        else:
            st.error(msg)
            st.session_state.running = False

# --- UI LAYOUT ---
with st.sidebar:
    st.title("ROYPLAY V5")
    st.markdown("---")
    st.session_state.target = st.text_input("USUARIO YOPMAIL", placeholder="ej: cinecasa1")
    st.caption("No agregues @yopmail.com")
    
    st.markdown("### 📡 SOPORTE ACTIVO")
    st.success("NETFLIX (Code/Hogar)")
    st.info("DISNEY+ / STAR+")
    st.warning("PRIME VIDEO")
    st.error("HBO MAX")
    st.info("PARAMOUNT+ / VIX")
    
    if st.button("LIMPIAR DATOS"):
        st.session_state.history = []
        st.session_state.processed = []
        st.rerun()

# MAIN SCREEN
st.markdown("## ⚡ INTERCEPTOR DE CÓDIGOS")

m1, m2, m3 = st.columns(3)
m1.metric("ESTADO", "ACTIVO" if st.session_state.running else "INACTIVO")
m2.metric("CAPTURAS", len(st.session_state.history))
m3.metric("OBJETIVO", st.session_state.target if st.session_state.target else "---")

c_main, c_log = st.columns([2, 1])

with c_main:
    btn_text = "⏹ DETENER SISTEMA" if st.session_state.running else "▶ INICIAR SISTEMA"
    st.button(btn_text, on_click=toggle, use_container_width=True)
    
    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(f"""
            <div class="interceptor-card">
                <div style="display:flex; justify-content:space-between; color:#888; font-size:12px;">
                    <span>{item['Hora']}</span>
                    <span>{item['Plataforma']}</span>
                </div>
                <div style="font-size:14px; margin-top:5px; color:#fff;">{item['Asunto']}</div>
                <div style="font-size:24px; font-weight:bold; color:#00ff41; margin:10px 0; letter-spacing:2px;">
                    {item['Dato']}
                </div>
                <div style="font-size:12px; color:#00f3ff; border-top:1px solid #333; padding-top:5px;">
                    TIPO: {item['Tipo']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Esperando correos entrantes...")

with c_log:
    st.markdown("### 📟 LOGS")
    log_text = "\n".join(st.session_state.logs)
    st.text_area("Console", log_text, height=400, disabled=True, label_visibility="collapsed")

# --- LOOP EN SEGUNDO PLANO ---
if st.session_state.running:
    with st.spinner("Escaneando red..."):
        time.sleep(3) # Respetar rate-limit de Yopmail
        
        inbox = st.session_state.client.get_inbox(st.session_state.target)
        
        for mail in inbox:
            if mail['id'] not in st.session_state.processed:
                # NUEVO MENSAJE
                sender = mail['sender']
                subject = mail['subject']
                
                log(f"Interceptado: {sender}", "info")
                
                # Leer contenido
                txt_body, html_body = st.session_state.client.get_mail_body(st.session_state.target, mail['id'])
                
                # Extraer Dato
                dato, tipo, plat = extract_data(sender, subject, txt_body, html_body)
                
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
                    log("Correo analizado sin datos clave.", "warn")
                
                st.session_state.processed.append(mail['id'])
        
        st.rerun()