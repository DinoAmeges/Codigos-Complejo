import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="RoyPlay Selenium Core", page_icon="☢️", layout="wide")

# --- CSS ESTILO HACKER/NEÓN ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    div[data-testid="stMetric"] { background: #111; border: 1px solid #333; color: #0f0; }
    div[data-testid="stMetricLabel"] { color: #888; }
    .titan-card { background: #111; border: 1px solid #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    div.stButton > button:first-child { background: #008000; color: white; border: none; font-weight: bold; }
    div.stButton > button:first-child:hover { background: #00ff00; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR SELENIUM (NAVEGADOR REAL) ---
def get_driver():
    """Configura un navegador Chrome invisible"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Sin interfaz gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Truco para evitar detección de bot básico
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Instalación automática del driver
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scan_yopmail(target_user):
    """Navega a Yopmail y extrae el último correo"""
    driver = None
    try:
        driver = get_driver()
        # 1. Entrar a la bandeja directa
        url = f"https://yopmail.com/en/wm?login={target_user}"
        driver.get(url)
        
        # Esperar a que cargue
        wait = WebDriverWait(driver, 10)
        
        # 2. Yopmail usa IFRAMES. Hay que cambiar al frame del inbox ('ifinbox')
        # Sin esto, el bot no ve nada.
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ifinbox")))
        
        # Obtener el último correo de la lista
        try:
            latest_email = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "m")))
            msg_id = latest_email.get_attribute("id")
            
            # Clic para cargarlo en el visor
            latest_email.click()
            time.sleep(1) # Espera breve para carga de JS
        except:
            return None, "Bandeja vacía o error de carga"
        
        # 3. Salir del iframe inbox y entrar al iframe del mensaje ('ifmail')
        driver.switch_to.default_content() # Volver al principal
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ifmail")))
        
        # 4. Extraer datos
        try:
            body_element = driver.find_element(By.ID, "mailmillieu")
            body_text = body_element.text
            
            # Intentar sacar asunto/remitente (a veces están en el header del iframe)
            # Para simplificar, usamos el body que es lo importante para el código
            return {"id": msg_id, "body": body_text}, "Éxito"
            
        except Exception as e:
            return None, f"Error leyendo cuerpo: {e}"

    except Exception as e:
        return None, f"Error crítico: {e}"
    finally:
        if driver:
            driver.quit()

# --- ESTADO ---
if 'run' not in st.session_state: st.session_state.run = False
if 'history' not in st.session_state: st.session_state.history = []
if 'last_id' not in st.session_state: st.session_state.last_id = ""

# --- UI ---
st.title("☢️ ROYPLAY SELENIUM CORE")

with st.sidebar:
    st.header("CONFIG")
    target = st.text_input("Usuario", placeholder="ej: netflix1")
    st.info("Este bot lanza un Chrome real en la nube. Es más lento pero infalible.")

# Métrica
col1, col2 = st.columns(2)
col1.metric("ESTADO", "RUNNING" if st.session_state.run else "STOPPED")
col2.metric("CAPTURAS", len(st.session_state.history))

# Botón
if st.button("⏹ DETENER" if st.session_state.run else "▶ INICIAR MOTOR"):
    if not target:
        st.error("Falta usuario")
    else:
        st.session_state.run = not st.session_state.run
        st.rerun()

# --- LOGICA ---
if st.session_state.run:
    with st.spinner("Lanzando navegador virtual... (Esto toma unos segundos)"):
        data, status = scan_yopmail(target)
        
        if data:
            current_id = data['id']
            body = data['body']
            
            # Si es un correo nuevo
            if current_id != st.session_state.last_id:
                st.session_state.last_id = current_id
                
                # Regex Extracción
                extracted = "Texto"
                tipo = "INFO"
                
                code = re.search(r'\b\d{4,8}\b', body)
                link = re.search(r'https://www\.(netflix|disneyplus|amazon|hbomax|max|paramountplus)\.com/[^\s"]+', body)
                
                if link and ("hogar" in body.lower() or "update" in body.lower()):
                    extracted = link.group(0)
                    tipo = "LINK 🏠"
                elif code:
                    extracted = code.group(0)
                    tipo = "CODE 🔢"
                
                # Guardar
                st.session_state.history.insert(0, {
                    "Hora": datetime.now().strftime("%H:%M:%S"),
                    "Tipo": tipo,
                    "Dato": extracted
                })
                st.toast(f"¡NUEVO! {tipo}", icon="🔥")
            else:
                pass # Mismo correo, no hacemos nada
        else:
            # st.warning(status) # Descomentar para debug
            pass
            
    # Pausa obligatoria para no saturar la RAM del servidor gratis
    time.sleep(5)
    st.rerun()

# --- RESULTADOS ---
st.markdown("### 📡 FEED EN VIVO")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
else:
    st.info("Esperando correos...")