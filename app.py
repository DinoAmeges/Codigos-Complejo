import streamlit as st
import requests
import time
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
from bs4 import BeautifulSoup
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="RoyPlay Yopmail Suite",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS "YOPMAIL ENTERPRISE" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');
    
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    
    /* Header Estilo Yopmail Moderno */
    h1 {
        font-family: 'Inter', sans-serif;
        color: #FFD700; /* Amarillo Yopmail */
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }
    
    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1e1e1e;
        border-left: 5px solid #FFD700;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Terminal Logs */
    .console-log {
        font-family: 'JetBrains Mono', monospace;
        background-color: #000;
        color: #0f0;
        padding: 10px;
        border-radius: 5px;
        height: 150px;
        overflow-y: scroll;
        font-size: 12px;
        border: 1px solid #333;
    }
    
    /* Botón Principal */
    div.stButton > button:first-child {
        background: #FFD700;
        color: #000;
        font-weight: 800;
        border-radius: 6px;
        border: none;
        text-transform: uppercase;
    }
    div.stButton > button:first-child:hover {
        background: #e6c200;
        box-shadow: 0 0 15px #FFD700;
    }
    
    /* Alerta de Éxito */
    .success-msg {
        background: rgba(0, 255, 128, 0.1);
        border: 1px solid #00ff80;
        color: #00ff80;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 128, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 128, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 128, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE LA SESIÓN ---
if 'active' not in st.session_state: st.session_state.active = False
if 'history' not in st.session_state: st.session_state.history = []
if 'processed_ids' not in st.session_state: st.session_state.processed_ids = []
if 'logs' not in st.session_state: st.session_state.logs = ["Sistema listo. Esperando usuario..."]
if 'target_user' not in st.session_state: st.session_state.target_user = ""

# --- MOTOR DE SCRAPING YOPMAIL ---
def get_yopmail_headers():
    """Simula un navegador real para evitar bloqueos"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    ]
    return {
        "User-Agent": random.choice(agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def fetch_yopmail_inbox(user):
    """Extrae la lista de correos de Yopmail"""
    session = requests.Session()
    # Yopmail usa una estructura compleja, accedemos a la versión 'm' (móvil) o inbox directo
    # Usamos la URL base que devuelve el HTML del inbox
    url = f"https://yopmail.com/en/inbox?login={user}&p=1&d=&ctrl=&scrl=&spam=true&v=3.1&r_c=&id="
    
    try:
        r = session.get(url, headers=get_yopmail_headers(), timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Los correos en Yopmail suelen estar en divs con clase 'm'
            messages = []
            for div in soup.find_all('div', class_='m'):
                msg_id = div.get('id')
                sender = div.find('span', class_='lmf').text if div.find('span', class_='lmf') else "Desconocido"
                subject = div.find('div', class_='lms').text if div.find('div', class_='lms') else "Sin Asunto"
                messages.append({'id': msg_id, 'sender': sender, 'subject': subject})
            return messages, session
    except Exception as e:
        log_system(f"Error de conexión: {e}")
    return [], session

def fetch_yopmail_body(session, user, msg_id):
    """Lee el contenido de un correo específico"""
    # URL para ver el correo individual
    url = f"https://yopmail.com/en/mail?b={user}&id={msg_id}"
    try:
        r = session.get(url, headers=get_yopmail_headers(), timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # El cuerpo suele estar en div id='mailmillieu'
        body_div = soup.find('div', id='mailmillieu')
        return body_div.get_text(separator=' ', strip=True) if body_div else ""
    except:
        return ""

def log_system(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{timestamp}] {msg}")
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🟡 Yopmail Suite")
    st.caption("Advanced Code Scraper")
    
    st.markdown("### 🎯 Objetivo")
    user_input = st.text_input("Usuario", placeholder="ej: netflix-hogar", help="Solo el nombre, sin @yopmail.com")
    st.session_state.target_user = user_input
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Filtros")
    filter_option = st.radio("Buscar:", ["Todo", "Netflix", "Disney+", "Códigos Numéricos", "Enlaces Hogar"])
    
    st.info("ℹ️ Este sistema usa scraping avanzado. Si no detecta correos, Yopmail podría estar bloqueando temporalmente la IP.")

# --- PANEL PRINCIPAL ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 📡 RoyPlay / Yopmail Enterprise")
with col2:
    st.markdown(f"**Dominio Fijo:**\n`@yopmail.com`")

# Métricas
m1, m2, m3 = st.columns(3)
m1.metric("Estado", "ONLINE" if st.session_state.active else "ESPERA", border=True)
m2.metric("Capturas", len(st.session_state.history), border=True)
m3.metric("Usuario", f"{st.session_state.target_user}" if st.session_state.target_user else "---", border=True)

# Botón de Control
if st.session_state.active:
    if st.button("⏹ DETENER ESCANEO", use_container_width=True):
        st.session_state.active = False
        st.rerun()
else:
    if st.button("▶ INICIAR ESCANEO DE YOPMAIL", use_container_width=True):
        if not st.session_state.target_user:
            st.error("Por favor ingresa un usuario en la barra lateral.")
        else:
            st.session_state.active = True
            log_system(f"Iniciando conexión a {st.session_state.target_user}@yopmail.com")
            st.rerun()

# --- LÓGICA PRINCIPAL (LOOP) ---
col_log, col_res = st.columns([1, 2])

with col_log:
    st.markdown("### 📟 Terminal")
    log_text = "\n".join(st.session_state.logs)
    st.text_area("Logs", log_text, height=300, disabled=True, label_visibility="collapsed", key="log_area")

with col_res:
    st.markdown("### 📥 Resultados en Tiempo Real")
    
    if st.session_state.active:
        # Barra de progreso visual
        with st.spinner(f"Analizando bandeja de entrada de {st.session_state.target_user}..."):
            
            # 1. Obtener lista
            msgs, session = fetch_yopmail_inbox(st.session_state.target_user)
            
            if not msgs:
                log_system("Bandeja vacía o sin cambios...")
            
            for msg in msgs:
                msg_id = msg['id']
                
                # Procesar solo nuevos
                if msg_id not in st.session_state.processed_ids:
                    sender = msg['sender']
                    subject = msg['subject']
                    
                    log_system(f"Nuevo correo detectado de: {sender}")
                    
                    # 2. Obtener cuerpo
                    body = fetch_yopmail_body(session, st.session_state.target_user, msg_id)
                    
                    # 3. Analizar Contenido
                    extracted = None
                    tipo = "Info"
                    
                    # Detectar Link Hogar
                    link_match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"]+', body)
                    # Detectar Código
                    code_match = re.search(r'\b\d{4,8}\b', body)
                    
                    if link_match and ("hogar" in body.lower() or "update" in body.lower()):
                        extracted = link_match.group(0)
                        tipo = "🔗 LINK HOGAR"
                    elif code_match:
                        extracted = code_match.group(0)
                        tipo = "🔢 CÓDIGO"
                    
                    # Guardar si hay algo relevante o si el filtro es "Todo"
                    should_save = False
                    if filter_option == "Todo": should_save = True
                    if filter_option == "Netflix" and "netflix" in sender.lower(): should_save = True
                    if filter_option == "Disney+" and "disney" in sender.lower(): should_save = True
                    if extracted: should_save = True

                    if should_save:
                        # Alerta Visual
                        if extracted:
                            st.markdown(f"""
                            <div class="success-msg">
                                <b>¡DATO ENCONTRADO!</b><br>
                                {tipo}: {extracted}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Sonido
                            st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"></audio>""", unsafe_allow_html=True)

                        new_record = {
                            "Hora": datetime.now().strftime("%H:%M:%S"),
                            "De": sender,
                            "Asunto": subject,
                            "Dato Extraído": extracted if extracted else "Solo Texto"
                        }
                        st.session_state.history.insert(0, new_record)
                        log_system(f"Guardado: {subject}")
                    
                    st.session_state.processed_ids.append(msg_id)
            
            # Anti-ban delay (Importante para Yopmail)
            time.sleep(3)
            st.rerun()

    # Tabla de Historial
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.data_editor(
            df,
            column_config={
                "Dato Extraído": st.column_config.TextColumn("Dato Clave (Copiar)", width="large"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Esperando capturas...")