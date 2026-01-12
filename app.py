import streamlit as st
import requests
import time
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
import random

# --- CONFIGURACIÓN "FULL WIDTH" ---
st.set_page_config(
    page_title="RoyPlay SaaS Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS "CYBERPUNK / SAAS" ---
st.markdown("""
    <style>
    /* Importar fuente Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #050509;
        background-image: radial-gradient(circle at 50% 50%, #111 0%, #050509 70%);
    }
    
    /* Tarjetas Glass */
    div.css-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Header Métricas */
    div[data-testid="stMetric"] {
        background-color: #0f1116;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Botón Principal Animado */
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #2563eb, #9333ea);
        color: white;
        font-weight: 800;
        border: none;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }

    /* Tablas */
    .stDataFrame { border: 1px solid #333; }
    
    /* Alerta Personalizada */
    .custom-alert {
        padding: 15px;
        background: linear-gradient(90deg, #065f46 0%, #059669 100%);
        border-radius: 8px;
        color: white;
        margin-bottom: 10px;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'monitoring' not in st.session_state: st.session_state.monitoring = False
if 'targets' not in st.session_state: st.session_state.targets = [] # Lista de cuentas
if 'history' not in st.session_state: st.session_state.history = []
if 'processed_ids' not in st.session_state: st.session_state.processed_ids = []
if 'telegram_cfg' not in st.session_state: st.session_state.telegram_cfg = {"token": "", "chat_id": ""}

# --- FUNCIONES AVANZADAS ---

def send_telegram(msg):
    """Envía notificación al móvil si está configurado"""
    token = st.session_state.telegram_cfg["token"]
    chat_id = st.session_state.telegram_cfg["chat_id"]
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data, timeout=3)
        except:
            pass

def add_target(user, domain):
    target = f"{user}@{domain}"
    if target not in [t['email'] for t in st.session_state.targets]:
        st.session_state.targets.append({"user": user, "domain": domain, "email": target})

def remove_target(email):
    st.session_state.targets = [t for t in st.session_state.targets if t['email'] != email]

# --- SIDEBAR (CONFIGURACIÓN PROFESIONAL) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2083/2083265.png", width=50)
    st.title("RoyPlay SaaS")
    
    st.markdown("### 🎯 Gestión de Cuentas")
    
    # Agregar cuenta
    c1, c2 = st.columns([2, 1])
    new_user = c1.text_input("Usuario", placeholder="cine1", label_visibility="collapsed")
    new_domain = c2.selectbox("Dom", ["1secmail.com", "1secmail.net", "wwjmz.com"], label_visibility="collapsed")
    
    if st.button("➕ Agregar a la Lista"):
        if new_user:
            add_target(new_user, new_domain)
            st.success(f"Añadido: {new_user}")
    
    # Lista de cuentas activas
    if st.session_state.targets:
        st.markdown("---")
        st.caption(f"MONITOREANDO ({len(st.session_state.targets)})")
        for t in st.session_state.targets:
            c_a, c_b = st.columns([4, 1])
            c_a.code(t['email'])
            if c_b.button("❌", key=t['email']):
                remove_target(t['email'])
                st.rerun()
    else:
        st.warning("Lista vacía. Añade cuentas arriba.")

    st.markdown("---")
    
    # Configuración Telegram (Killer Feature)
    with st.expander("📲 Notificaciones Telegram"):
        tg_token = st.text_input("Bot Token", value=st.session_state.telegram_cfg["token"], type="password")
        tg_chat = st.text_input("Chat ID", value=st.session_state.telegram_cfg["chat_id"])
        if st.button("Guardar Telegram"):
            st.session_state.telegram_cfg = {"token": tg_token, "chat_id": tg_chat}
            send_telegram("🔔 RoyPlay Bot: Conexión de prueba exitosa.")
            st.toast("Configuración guardada", icon="✅")

# --- PANEL PRINCIPAL ---
st.markdown("## 🚀 Dashboard de Operaciones")

# Métricas Superiores
total_hits = len(st.session_state.history)
active_accounts = len(st.session_state.targets)
last_hit = st.session_state.history[0]['Hora'] if st.session_state.history else "--:--"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Estado del Sistema", "ONLINE 🟢" if st.session_state.monitoring else "OFFLINE 🔴")
m2.metric("Cuentas Activas", active_accounts)
m3.metric("Códigos Capturados", total_hits)
m4.metric("Última Captura", last_hit)

# Botón Maestro
if st.session_state.monitoring:
    if st.button("⏹ DETENER MOTOR DE BÚSQUEDA", type="primary", use_container_width=True):
        st.session_state.monitoring = False
        st.rerun()
else:
    if st.button("▶ INICIAR MOTOR MULTI-HILO", type="primary", use_container_width=True):
        if not st.session_state.targets:
            st.error("¡Agrega al menos una cuenta en la barra lateral!")
        else:
            st.session_state.monitoring = True
            st.rerun()

# --- LÓGICA CORE (Multi-Account Loop) ---
if st.session_state.monitoring:
    placeholder_log = st.empty()
    
    # Barra de progreso "infinita"
    my_bar = st.progress(0)
    
    # Iterar sobre todas las cuentas configuradas
    logs_txt = []
    
    for i, target in enumerate(st.session_state.targets):
        user = target['user']
        domain = target['domain']
        email_full = target['email']
        
        # Actualizar UI
        my_bar.progress((i + 1) / len(st.session_state.targets))
        placeholder_log.caption(f"📡 Escaneando nodo: **{email_full}**...")
        
        try:
            # API Request
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
            r = requests.get(url, timeout=3)
            
            if r.status_code == 200:
                msgs = r.json()
                for msg in msgs:
                    if msg['id'] not in st.session_state.processed_ids:
                        
                        # LEER MENSAJE
                        read_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain={domain}&id={msg['id']}"
                        full = requests.get(read_url).json()
                        body = full.get('textBody', '') or full.get('body', '')
                        subject = full.get('subject', 'Sin asunto')
                        sender = full.get('from', 'Desconocido')
                        
                        # --- MOTOR DE EXTRACCIÓN UNIVERSAL ---
                        extracted = "N/A"
                        tipo = "Info"
                        
                        # 1. Detectar Links de Hogar/Update
                        link_match = re.search(r'https://www\.(netflix|disneyplus)\.com/[^\s"]+', body)
                        
                        # 2. Detectar Códigos Numéricos
                        code_match = re.search(r'\b\d{4,8}\b', body)
                        
                        if link_match and ("hogar" in body.lower() or "household" in body.lower() or "update" in body.lower()):
                            extracted = link_match.group(0)
                            tipo = "🔗 LINK HOGAR"
                        elif code_match:
                            extracted = code_match.group(0)
                            tipo = "🔢 CÓDIGO"
                        
                        # Si encontramos algo útil
                        if extracted != "N/A":
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            
                            # Guardar
                            record = {
                                "Hora": timestamp,
                                "Cuenta": email_full,
                                "Plataforma": sender,
                                "Resultado": extracted,
                                "Tipo": tipo
                            }
                            st.session_state.history.insert(0, record)
                            st.session_state.processed_ids.append(msg['id'])
                            
                            # Alerta Visual
                            st.markdown(f"""
                            <div class="custom-alert">
                                <b>¡ÉXITO EN {email_full}!</b><br>
                                {tipo}: {extracted}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Notificar Telegram
                            tg_msg = f"🚀 *RoyPlay Alert*\n\n📧: `{email_full}`\n🔑: `{extracted}`\n🏢: {sender}"
                            send_telegram(tg_msg)
            
            # Anti-ban delay pequeño entre cuentas
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error en {email_full}: {e}")

    # Pausa antes del siguiente ciclo completo
    time.sleep(2)
    st.rerun()

# --- VISUALIZACIÓN DE DATOS ---
col_table, col_chart = st.columns([3, 2])

with col_table:
    st.subheader("📋 Registro en Vivo")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.data_editor(
            df,
            column_config={
                "Resultado": st.column_config.TextColumn("Dato (Copiar)", width="large"),
                "Cuenta": st.column_config.TextColumn("Email Origen", width="medium"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            height=300
        )
    else:
        st.info("Esperando datos...")

with col_chart:
    st.subheader("📊 Actividad")
    if len(st.session_state.history) > 0:
        # Gráfico simple de eventos por cuenta
        df_chart = pd.DataFrame(st.session_state.history)
        fig = px.histogram(df_chart, x="Cuenta", title="Capturas por Cuenta", color_discrete_sequence=['#3b82f6'])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("El gráfico aparecerá cuando haya datos.")