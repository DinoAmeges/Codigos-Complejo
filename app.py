import streamlit as st
import requests
import time
import re
import pandas as pd
import random
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DEL PROYECTO "CODIGOS" ---
st.set_page_config(
    page_title="Codigos - Yopmail Monitor",
    page_icon="🔓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ESTILO HACKER/PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #161b22;
        color: white;
        border: 1px solid #30363d;
    }
    
    /* Botones */
    div.stButton > button:first-child {
        background-color: #238636;
        color: white;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #2ea043;
        box-shadow: 0 0 10px #2ea043;
    }
    
    /* Tablas */
    div[data-testid="stDataFrame"] {
        border: 1px solid #30363d;
    }
    
    /* Alerta Personalizada */
    .found-box {
        background: rgba(0, 255, 65, 0.1);
        border: 1px solid #00ff41;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'monitoring' not in st.session_state: st.session_state.monitoring = False
if 'history' not in st.session_state: st.session_state.history = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'logs' not in st.session_state: st.session_state.logs = []

# --- MOTOR DE SCRAPING ROBUSTO (CORREGIDO) ---
def get_headers():
    """Simula ser un Chrome real en Windows para evitar bloqueos"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://yopmail.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

def init_session():
    """Inicializa sesión en Yopmail para obtener Cookies (Importante)"""
    s = requests.Session()
    s.headers.update(get_headers())
    try:
        # Visitamos la home primero para que nos den las cookies de sesión
        s.get("https://yopmail.com/en/", timeout=5)
    except Exception as e:
        log_msg(f"Error inicializando sesión: {e}")
    return s

def fetch_inbox(session, user):
    """Obtiene la lista de correos usando la ruta interna de Yopmail"""
    # Yopmail usa 'inbox' con parámetros específicos para cargar los mails
    # Limpiamos el usuario por si pusieron @yopmail.com
    clean_user = user.split('@')[0]
    
    # URL Mágica: Esta es la que usa el iframe interno de Yopmail
    url = f"https://yopmail.com/en/inbox?login={clean_user}&p=1&d=&ctrl=&scrl=&spam=true&v=3.1&r_c=&id="
    
    try:
        r = session.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Los correos están dentro de divs con clase 'm'
            emails = []
            divs = soup.find_all('div', class_='m')
            
            for div in divs:
                try:
                    msg_id = div['id'] # El ID es vital para leer el cuerpo
                    # Extraer remitente (clase 'lmf')
                    sender_tag = div.find('span', class_='lmf')
                    sender = sender_tag.text.strip() if sender_tag else "Desconocido"
                    # Extraer asunto (clase 'lms')
                    subject_tag = div.find('div', class_='lms')
                    subject = subject_tag.text.strip() if subject_tag else "Sin Asunto"
                    
                    emails.append({'id': msg_id, 'sender': sender, 'subject': subject})
                except:
                    continue
            return emails
    except Exception as e:
        log_msg(f"Error leyendo bandeja: {e}")
    return []

def fetch_body(session, user, msg_id):
    """Lee el cuerpo del mensaje individual"""
    clean_user = user.split('@')[0]
    # URL Mágica 2: Para leer el cuerpo del mail
    url = f"https://yopmail.com/en/mail?b={clean_user}&id={msg_id}"
    
    try:
        r = session.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # El cuerpo suele estar en un div con id 'mailmillieu'
        body_div = soup.find('div', id='mailmillieu')
        
        if body_div:
            return body_div.get_text(separator=' ', strip=True)
        return "No se pudo leer el cuerpo"
    except:
        return ""

def log_msg(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{timestamp}] {msg}")
    if len(st.session_state.logs) > 20: st.session_state.logs.pop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🔓 PROYECTO CODIGOS")
    st.markdown("Monitor de Yopmail en tiempo real.")
    
    st.markdown("### 👤 Configuración")
    target_user = st.text_input("Usuario Yopmail", placeholder="ej: micuenta123", help="Sin @yopmail.com")
    
    st.markdown("### 🔍 Filtros")
    filter_mode = st.radio("Buscar:", ["Todo", "Códigos (4-8 dígitos)", "Links (Netflix/Disney)"])
    
    st.markdown("---")
    st.markdown("### 🐛 Debug (Si falla)")
    show_debug = st.checkbox("Mostrar logs de conexión")

# --- PANEL PRINCIPAL ---
st.title(f"Codigos Monitor")
st.markdown(f"Vigilando: **{target_user}@yopmail.com**" if target_user else "Esperando configuración...")

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Estado", "EJECUTANDO" if st.session_state.monitoring else "DETENIDO")
col2.metric("Capturas", len(st.session_state.history))
col3.metric("Sesión", "Activa" if 'session' in st.session_state else "Inactiva")

# Botones de Control
if st.session_state.monitoring:
    if st.button("⏹ DETENER", type="primary", use_container_width=True):
        st.session_state.monitoring = False
        st.rerun()
else:
    if st.button("▶ INICIAR CAPTURA", type="primary", use_container_width=True):
        if not target_user:
            st.warning("⚠️ Escribe un usuario primero.")
        else:
            st.session_state.monitoring = True
            st.session_state.session = init_session() # Iniciar sesión nueva
            log_msg(f"Sesión iniciada para {target_user}")
            st.rerun()

# --- LÓGICA DE BUCLE ---
if st.session_state.monitoring:
    with st.spinner(f"Escaneando {target_user}@yopmail.com ..."):
        # 1. Obtener Bandeja
        emails = fetch_inbox(st.session_state.session, target_user)
        
        if not emails:
            # Si no hay emails, puede ser que la bandeja esté vacía O que Yopmail nos bloqueó
            pass # No llenamos el log para no saturar
            
        for email in emails:
            mid = email['id']
            if mid not in st.session_state.processed:
                # ¡NUEVO CORREO!
                sender = email['sender']
                subject = email['subject']
                
                log_msg(f"Detectado correo de: {sender}")
                
                # 2. Leer Cuerpo
                body = fetch_body(st.session_state.session, target_user, mid)
                
                # 3. Extraer Datos
                extracted = None
                tipo = "Info"
                
                # Regex
                code_match = re.search(r'\b\d{4,8}\b', body)
                link_match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"]+', body)
                
                # Lógica de Filtros
                save = False
                if filter_mode == "Todo":
                    extracted = code_match.group(0) if code_match else "Texto detectado"
                    save = True
                elif filter_mode == "Códigos (4-8 dígitos)" and code_match:
                    extracted = code_match.group(0)
                    tipo = "🔢 CÓDIGO"
                    save = True
                elif filter_mode == "Links (Netflix/Disney)" and link_match:
                    extracted = link_match.group(0)
                    tipo = "🔗 LINK"
                    save = True
                
                if save:
                    # Mostrar alerta visual
                    st.markdown(f"""
                    <div class="found-box">
                        <h3>¡{tipo} ENCONTRADO!</h3>
                        <p><b>De:</b> {sender}</p>
                        <p style="font-size: 20px; font-weight: bold;">{extracted}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Guardar en historial
                    st.session_state.history.insert(0, {
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "De": sender,
                        "Dato": extracted,
                        "Mensaje Original": subject
                    })
                
                st.session_state.processed.append(mid)
        
        # Espera para no ser bloqueado (Importante en Yopmail)
        time.sleep(4) 
        st.rerun()

# --- VISUALIZACIÓN ---
st.markdown("### 📋 Historial de Capturas")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Dato": st.column_config.TextColumn("Dato (Copiar)", width="large"),
        }
    )
else:
    st.info("Esperando correos...")

# --- DEBUGGING AREA ---
if show_debug:
    st.markdown("### 🐛 Logs del Sistema")
    st.text_area("Log Output", "\n".join(st.session_state.logs), height=200)