import streamlit as st
import requests
import pandas as pd
import time
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA (FULL WIDTH) ---
st.set_page_config(
    page_title="RoyPlay Monitor Enterprise",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PROFESIONAL (GLASSMORPHISM & NEON) ---
st.markdown("""
    <style>
    /* Tipografía */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');
    
    :root {
        --bg-color: #09090b;
        --card-bg: rgba(255, 255, 255, 0.03);
        --border-color: rgba(255, 255, 255, 0.1);
        --accent-color: #00f2ea; /* Cian Neón */
        --success-color: #00ff9d;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
    }

    .stApp {
        background-color: var(--bg-color);
        background-image: 
            radial-gradient(at 0% 0%, rgba(0, 242, 234, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(37, 99, 235, 0.05) 0px, transparent 50%);
        font-family: 'Inter', sans-serif;
    }

    /* Tarjetas Glassmorphism */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.2);
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 15px;
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: var(--accent-color);
    }

    /* Botones */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    /* Botón Primario (Start) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #00f2ea 100%);
        color: #000;
        font-weight: 800;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 20px rgba(0, 242, 234, 0.4);
    }

    /* Terminal Logs */
    .terminal-window {
        font-family: 'JetBrains Mono', monospace;
        background: #000;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        height: 250px;
        overflow-y: auto;
        font-size: 12px;
        color: #00ff9d;
    }
    .log-entry { margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px; }
    .log-time { color: #666; margin-right: 8px; }

    /* Inputs */
    .stTextInput input {
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid var(--border-color) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE SCRAPER PROFESIONAL ---
class YopScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://yopmail.com/en/",
            "Connection": "keep-alive"
        })
        self.is_initialized = False

    def initialize(self):
        """Visita la home para obtener cookies de sesión"""
        try:
            self.session.get("https://yopmail.com/en/", timeout=10)
            self.session.cookies.set('consent', 'yes') # Cookie de consentimiento
            self.is_initialized = True
            return True, "Sesión inicializada correctamente."
        except Exception as e:
            return False, f"Error de conexión inicial: {e}"

    def get_inbox(self, user):
        """Obtiene mensajes de la bandeja"""
        if not self.is_initialized:
            self.initialize()
            
        clean_user = user.split('@')[0]
        # URL Específica que usa Yopmail internamente para cargar correos
        url = f"https://yopmail.com/en/inbox?login={clean_user}&p=1&d=&ctrl=&scrl=&spam=true&v=3.1&r_c=&id="
        
        try:
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'lxml') # lxml es más rápido
                emails = []
                # Los divs 'm' contienen los mensajes
                for msg in soup.find_all('div', class_='m'):
                    try:
                        mid = msg['id']
                        sender = msg.find('span', class_='lmf').text.strip()
                        subject = msg.find('div', class_='lms').text.strip()
                        emails.append({'id': mid, 'sender': sender, 'subject': subject})
                    except:
                        continue
                return emails
        except Exception:
            pass
        return []

    def get_body(self, user, msg_id):
        """Lee el contenido de un mensaje"""
        clean_user = user.split('@')[0]
        url = f"https://yopmail.com/en/mail?b={clean_user}&id={msg_id}"
        try:
            r = self.session.get(url, timeout=5)
            soup = BeautifulSoup(r.text, 'lxml')
            # El cuerpo suele estar en #mailmillieu
            body = soup.find('div', id='mailmillieu')
            return body.get_text(separator=' ', strip=True) if body else ""
        except:
            return ""

# --- GESTIÓN DE ESTADO ---
if 'scraper' not in st.session_state: st.session_state.scraper = YopScraper()
if 'running' not in st.session_state: st.session_state.running = False
if 'history' not in st.session_state: st.session_state.history = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'logs' not in st.session_state: st.session_state.logs = []

# --- FUNCIONES UI ---
def log_msg(msg, type="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    entry = f'<div class="log-entry"><span class="log-time">[{t}]</span> <b>{type}:</b> {msg}</div>'
    st.session_state.logs.insert(0, entry)
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

def toggle_monitor():
    if not st.session_state.target_user:
        st.toast("⚠️ Por favor escribe un usuario primero.", icon="🚫")
        return
    
    st.session_state.running = not st.session_state.running
    if st.session_state.running:
        status, msg = st.session_state.scraper.initialize()
        if status:
            log_msg(f"Monitor iniciado para: {st.session_state.target_user}", "SYSTEM")
            log_msg(msg, "NETWORK")
        else:
            st.session_state.running = False
            st.error(msg)
    else:
        log_msg("Monitor detenido por usuario.", "SYSTEM")

# --- LAYOUT DE LA APP ---

# 1. SIDEBAR CONFIG
with st.sidebar:
    st.title("🛡️ RoyPlay Config")
    st.caption("v3.0 Enterprise Edition")
    st.markdown("---")
    
    st.markdown("### 🎯 Objetivo")
    st.session_state.target_user = st.text_input("Usuario Objetivo", placeholder="ej: prueba1", help="Solo el nombre")
    
    st.markdown("### ⚡ Filtros")
    filter_mode = st.radio("Modo de Extracción", ["Inteligente (Auto)", "Solo Códigos", "Solo Enlaces", "Todo el Texto"])
    
    st.markdown("---")
    if st.session_state.history:
        # Botón de descarga CSV
        df = pd.DataFrame(st.session_state.history)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_royplay.csv", "text/csv")

# 2. HEADER Y MÉTRICAS
st.markdown("## 📡 Panel de Control **Codigos**")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Estado", "ACTIVO" if st.session_state.running else "INACTIVO")
m2.metric("Capturas Totales", len(st.session_state.history))
m3.metric("Última Actividad", st.session_state.history[0]['Hora'] if st.session_state.history else "--:--")
m4.metric("Cuenta", f"{st.session_state.target_user}@yopmail.com" if st.session_state.target_user else "---")

# 3. ÁREA PRINCIPAL
col_main, col_logs = st.columns([2, 1])

with col_main:
    st.markdown("### 🎮 Control de Misión")
    
    # Botón Principal
    btn_label = "⏹ DETENER MONITOR" if st.session_state.running else "▶ INICIAR MONITOR"
    st.button(btn_label, on_click=toggle_monitor)
    
    # Tabla de Resultados (Glass Card)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Resultados en Vivo")
    if st.session_state.history:
        df_hist = pd.DataFrame(st.session_state.history)
        st.data_editor(
            df_hist,
            column_config={
                "Dato": st.column_config.TextColumn("Dato (Click para copiar)", width="large"),
                "Tipo": st.column_config.Column("Tipo", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )
    else:
        st.info("El sistema está esperando nuevos correos...")
    st.markdown('</div>', unsafe_allow_html=True)

with col_logs:
    st.markdown("### 📟 Terminal")
    log_content = "".join(st.session_state.logs)
    st.markdown(f'<div class="terminal-window">{log_content}</div>', unsafe_allow_html=True)

# --- BUCLE DE PROCESAMIENTO (HIDDEN LOOP) ---
if st.session_state.running:
    with st.spinner("Escaneando red Yopmail..."):
        time.sleep(3) # Delay ético
        
        # 1. Obtener Inbox
        emails = st.session_state.scraper.get_inbox(st.session_state.target_user)
        
        if not emails:
            # log_msg("Sin cambios en la bandeja...", "SCAN") # Comentado para no spamear log
            pass
        
        for email in emails:
            mid = email['id']
            if mid not in st.session_state.processed:
                # ¡Nuevo correo!
                sender = email['sender']
                subject = email['subject']
                
                log_msg(f"Correo detectado de: {sender}", "NEW MSG")
                
                # 2. Obtener Cuerpo
                body = st.session_state.scraper.get_body(st.session_state.target_user, mid)
                
                # 3. Extracción
                extracted = "Texto base"
                tipo = "TXT"
                
                code_match = re.search(r'\b\d{4,8}\b', body)
                link_match = re.search(r'https://www\.(netflix|disneyplus|amazon)\.com/[^\s"]+', body)
                
                save = False
                
                # Lógica de Filtros
                if filter_mode == "Inteligente (Auto)":
                    if link_match and ("hogar" in body.lower() or "household" in body.lower()):
                        extracted = link_match.group(0)
                        tipo = "LINK 🏠"
                        save = True
                    elif code_match:
                        extracted = code_match.group(0)
                        tipo = "CODE 🔢"
                        save = True
                
                elif filter_mode == "Solo Códigos" and code_match:
                    extracted = code_match.group(0)
                    tipo = "CODE 🔢"
                    save = True
                    
                elif filter_mode == "Solo Enlaces" and link_match:
                    extracted = link_match.group(0)
                    tipo = "LINK 🔗"
                    save = True
                
                elif filter_mode == "Todo el Texto":
                    extracted = body[:100] + "..."
                    tipo = "TEXT"
                    save = True

                if save:
                    new_record = {
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Remitente": sender,
                        "Dato": extracted,
                        "Tipo": tipo
                    }
                    st.session_state.history.insert(0, new_record)
                    st.toast(f"¡Dato Encontrado! {tipo}", icon="🎉")
                    log_msg(f"Extracción exitosa: {tipo}", "SUCCESS")
                
                st.session_state.processed.append(mid)
        
        st.rerun()