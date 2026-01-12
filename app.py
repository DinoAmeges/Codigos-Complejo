import streamlit as st
import requests
import pandas as pd
import time
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# --- CONFIGURACIÓN PRINCIPAL ---
st.set_page_config(
    page_title="RoyPlay Titanium Monitor",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS "TITANIUM" (DISEÑO PRO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Inter:wght@400;600&display=swap');
    
    :root {
        --bg-dark: #050505;
        --card-bg: #0a0a0a;
        --border: #1f1f1f;
        --neon-blue: #00f3ff;
        --neon-purple: #bc13fe;
        --success: #00ff9d;
    }

    .stApp {
        background-color: var(--bg-dark);
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
        font-family: 'Inter', sans-serif;
    }

    /* Títulos */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif; text-transform: uppercase; }
    
    /* Tarjetas Glass */
    .titan-card {
        background: rgba(10, 10, 10, 0.7);
        border: 1px solid var(--border);
        border-top: 1px solid #333;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: 15px;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: #0f0f0f;
        border: 1px solid #222;
        border-left: 3px solid var(--neon-blue);
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetricLabel"] { color: #666; font-size: 0.8rem; }
    div[data-testid="stMetricValue"] { color: #fff; font-family: 'Rajdhani'; }

    /* Botón Start */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
        border: none;
        color: #000;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 4px;
        height: 50px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
        transform: scale(1.01);
    }

    /* Terminal */
    .console {
        font-family: 'Courier New', monospace;
        background: #000;
        border: 1px solid #222;
        padding: 15px;
        height: 200px;
        overflow-y: auto;
        font-size: 11px;
        color: #0f0;
        border-radius: 6px;
    }
    .log-line { border-bottom: 1px solid #111; padding: 2px 0; }
    .log-err { color: #ff4444; }
    .log-succ { color: var(--neon-blue); font-weight: bold; }

    /* Alerta de Resultado */
    .result-box {
        background: rgba(0, 255, 157, 0.05);
        border: 1px solid var(--success);
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        animation: flash 1s;
    }
    @keyframes flash { 0% { opacity: 0; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE SCRAPING MEJORADO ---
class YopmailEngine:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.update_headers()
        self.cookies_set = False

    def update_headers(self):
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://yopmail.com/en/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    def init_cookies(self):
        """Visita la home para obtener cookies válidas (CRÍTICO PARA QUE FUNCIONE)"""
        try:
            # 1. Petición inicial a la home
            r = self.session.get("https://yopmail.com/en/", timeout=8)
            # 2. Forzamos la cookie de consentimiento
            self.session.cookies.set('consent', 'yes', domain='.yopmail.com')
            self.session.cookies.set('yp', '1', domain='.yopmail.com') # Cookie de configuración
            self.cookies_set = True
            return True, "Cookies de sesión firmadas."
        except Exception as e:
            return False, f"Error iniciando sesión: {e}"

    def scan_inbox(self, user):
        """Lee la bandeja interna"""
        if not self.cookies_set:
            self.init_cookies()
            
        clean_user = user.split('@')[0]
        # URL exacta que usa el iframe de Yopmail
        # 'd=' vacía cache, 'ctrl=' evita cache, 'scrl=' scroll, 'spam=true' ve spam también
        url = f"https://yopmail.com/en/inbox?login={clean_user}&p=1&d=&ctrl=&scrl=&spam=true&v=3.1&r_c=&id="
        
        try:
            r = self.session.get(url, timeout=5)
            if "To access your inbox" in r.text: # Captcha detectado
                self.update_headers() # Rotar identidad
                return [], "Bloqueo suave detectado, rotando IP..."
                
            soup = BeautifulSoup(r.text, 'lxml')
            emails = []
            
            # Iterar sobre los mensajes (divs clase 'm')
            for msg in soup.find_all('div', class_='m'):
                try:
                    mid = msg['id']
                    # Extraer remitente
                    s_tag = msg.find('span', class_='lmf')
                    sender = s_tag.text.strip() if s_tag else "Desconocido"
                    # Extraer asunto
                    sub_tag = msg.find('div', class_='lms')
                    subject = sub_tag.text.strip() if sub_tag else "Sin asunto"
                    
                    emails.append({'id': mid, 'sender': sender, 'subject': subject})
                except:
                    continue
            return emails, "Escaneo correcto"
        except Exception as e:
            return [], str(e)

    def read_mail(self, user, msg_id):
        """Lee el cuerpo del mensaje"""
        clean_user = user.split('@')[0]
        url = f"https://yopmail.com/en/mail?b={clean_user}&id={msg_id}"
        try:
            r = self.session.get(url, timeout=5)
            soup = BeautifulSoup(r.text, 'lxml')
            body = soup.find('div', id='mailmillieu')
            return body.get_text(separator=' ', strip=True) if body else ""
        except:
            return ""

# --- VARIABLES DE ESTADO ---
if 'engine' not in st.session_state: st.session_state.engine = YopmailEngine()
if 'run' not in st.session_state: st.session_state.run = False
if 'data' not in st.session_state: st.session_state.data = []
if 'processed' not in st.session_state: st.session_state.processed = []
if 'logs' not in st.session_state: st.session_state.logs = []

# --- FUNCIONES UI ---
def log(msg, type="info"):
    t = datetime.now().strftime("%H:%M:%S")
    color = "log-succ" if type=="success" else ("log-err" if type=="error" else "")
    st.session_state.logs.insert(0, f"<div class='log-line {color}'>[{t}] {msg}</div>")
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

def toggle():
    if not st.session_state.target:
        st.toast("⚠️ Falta el usuario", icon="🚫")
        return
    st.session_state.run = not st.session_state.run
    if st.session_state.run:
        log(f"Iniciando monitor para: {st.session_state.target}", "success")
        ok, msg = st.session_state.engine.init_cookies()
        log(msg, "info")
    else:
        log("Monitor detenido", "error")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/919/919825.png", width=40)
    st.markdown("### CONFIGURACIÓN")
    st.session_state.target = st.text_input("Usuario Yopmail", placeholder="ej: cine123")
    
    st.markdown("---")
    st.markdown("### 🧬 PLATAFORMAS DETECTABLES")
    st.caption("✅ Netflix (Hogar/Código)")
    st.caption("✅ Disney+ / Star+")
    st.caption("✅ HBO Max / Max")
    st.caption("✅ Amazon Prime Video")
    st.caption("✅ Paramount+")
    
    st.markdown("---")
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.data = []
        st.session_state.processed = []
        st.rerun()

# --- PANEL PRINCIPAL ---
st.markdown("## 💎 ROYPLAY TITANIUM")

# Métricas
m1, m2, m3, m4 = st.columns(4)
m1.metric("ESTADO", "RUNNING" if st.session_state.run else "STOPPED")
m2.metric("CAPTURAS", len(st.session_state.data))
m3.metric("ÚLTIMO CHECK", datetime.now().strftime("%H:%M:%S"))
m4.metric("TARGET", st.session_state.target if st.session_state.target else "---")

# Layout
c_main, c_log = st.columns([2, 1])

with c_main:
    btn_txt = "⏹ ABORTAR MISION" if st.session_state.run else "▶ INICIAR SISTEMA"
    st.button(btn_txt, on_click=toggle)
    
    st.markdown('<div class="titan-card">', unsafe_allow_html=True)
    st.markdown("#### 📡 INTERCEPTOR FEED")
    
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.data_editor(
            df,
            column_config={
                "Plataforma": st.column_config.TextColumn("Servicio", width="small"),
                "Dato": st.column_config.TextColumn("Dato (Copiar)", width="large"),
                "Tipo": st.column_config.TextColumn("Tipo", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=350
        )
    else:
        st.info("Esperando señales...")
    st.markdown('</div>', unsafe_allow_html=True)

with c_log:
    st.markdown("#### 📟 TERMINAL")
    logs_html = "".join(st.session_state.logs)
    st.markdown(f'<div class="console">{logs_html}</div>', unsafe_allow_html=True)

# --- BUCLE DE PROCESAMIENTO (HIDDEN) ---
if st.session_state.run:
    with st.spinner("Escaneando frecuencia..."):
        time.sleep(4) # Importante: Yopmail bloquea si bajas de 3s
        
        # 1. Escaneo
        mails, status = st.session_state.engine.scan_inbox(st.session_state.target)
        
        if not mails:
            # log(status) # Silenciado para no llenar el log
            pass
        
        for m in mails:
            if m['id'] not in st.session_state.processed:
                # Nuevo correo
                sender = m['sender']
                subj = m['subject']
                log(f"Interceptado: {sender} | {subj}", "info")
                
                # 2. Lectura
                body = st.session_state.engine.read_mail(st.session_state.target, m['id'])
                
                # 3. Lógica de Extracción (REGEX AVANZADO)
                extracted = None
                tipo = "Info"
                plat = "Otro"
                
                # Patrones
                link_pat = re.search(r'https://www\.(netflix|disneyplus|amazon|hbomax|max|paramountplus)\.com/[^\s"]+', body)
                code_pat = re.search(r'\b\d{4,8}\b', body) # Captura 4, 6 u 8 dígitos
                
                # Identificar Plataforma
                s_lower = sender.lower()
                if "netflix" in s_lower: plat = "Netflix"
                elif "disney" in s_lower: plat = "Disney+"
                elif "hbo" in s_lower or "max" in s_lower: plat = "HBO Max"
                elif "amazon" in s_lower or "prime" in s_lower: plat = "Prime Video"
                elif "paramount" in s_lower: plat = "Paramount+"
                
                # Decisión
                if link_match := link_pat:
                    if "hogar" in body.lower() or "household" in body.lower() or "update" in body.lower():
                        extracted = link_match.group(0)
                        tipo = "LINK 🏠"
                
                if not extracted and code_pat:
                    extracted = code_pat.group(0)
                    tipo = "CODE 🔢"
                
                # Si encontramos algo
                if extracted:
                    st.session_state.data.insert(0, {
                        "Hora": datetime.now().strftime("%H:%M"),
                        "Plataforma": plat,
                        "Dato": extracted,
                        "Tipo": tipo
                    })
                    log(f"¡ÉXITO! {plat}: {extracted}", "success")
                    st.toast(f"{plat}: {extracted}", icon="🔥")
                
                st.session_state.processed.append(m['id'])
        
        st.rerun()