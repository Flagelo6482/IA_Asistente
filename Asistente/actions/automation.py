import os
import time
import webbrowser
import pywhatkit
import pyautogui
from config.database import conectar_db
from core.brain import llm_local

def abrir_web(url):
    """Abre una página web específica."""
    webbrowser.open(url)
    return f"He abierto la página {url} en tu navegador."

def ejecutar_aplicacion(nombre_app):
    """Intenta abrir una aplicación local en Windows."""
    nombre_app = nombre_app.lower()
    if "calculadora" in nombre_app:
        os.system("calc")
    elif "code" in nombre_app:
        os.system("code")
    else:
        # Abrir app genérica
        os.system(nombre_app)
    return f"Iniciando {nombre_app}."

def reproducir_en_youtube(busqueda):
    """Busca y reproduce el primer video encontrado en YouTube."""
    try:
        pywhatkit.playonyt(busqueda)
        return f"Claro, reproduciendo '{busqueda}' en YouTube."
    except Exception as e:
        return f"Hubo un error al intentar poner la música en YouTube: {e}"

def enviar_whatsapp_contacto(alias, mensaje):
    """Busca el número de celular del alias en la base de datos y envía el mensaje por WhatsApp."""
    conn = conectar_db()
    if not conn:
        return "Error de conexión con la base de datos."
        
    try:
        cur = conn.cursor()
        cur.execute("SELECT numero_celular FROM agenda_contactos WHERE nombre_alias = %s", (alias.lower(),))
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            numero = resultado[0]
            print(f"Frank: Iniciando protocolo de envío instantáneo para {alias} ({numero})...")
            # Envío automático instantáneo. wait_time=15 da margen para cargar el navegador
            pywhatkit.sendwhatmsg_instantly(numero, mensaje, wait_time=15, tab_close=True)
            
            # Pausa breve para asegurar foco en el navegador
            time.sleep(3) 
            
            # Simular presionar enter
            pyautogui.press('enter')
            return f"Mensaje enviado con éxito a {alias}."
        else:
            return f"No encontré a '{alias}' en la agenda de contactos de pgAdmin."
    except Exception as e:
        return f"Excepción durante el proceso de envío de WhatsApp: {e}"

def procesar_comando_whatsapp(comando):
    """Extrae el destinatario y el mensaje exacto a enviar usando Ollama local."""
    if not llm_local:
        return None, None
        
    prompt = (
        f"Eres un extractor de datos estricto. Analiza: '{comando}'\n\n"
        "REGLAS:\n"
        "1. Extrae el NOMBRE del destinatario (sin preposiciones como 'al').\n"
        "2. Extrae el MENSAJE exacto que el usuario quiere enviar.\n"
        "3. Responde ÚNICAMENTE en este formato: NOMBRE | MENSAJE\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'frank envía un mensaje a mama diciendo hola'\n"
        "Salida: mama | hola\n\n"
        "Entrada: 'frank envia un mensaje al sonso diciendo que es un sonso'\n"
        "Salida: sonso | eres un sonso\n\n"
        "TU RESPUESTA:"
    )
    
    try:
        respuesta = llm_local.invoke(prompt).strip()
        print(f"DEBUG - IA Procesó: {respuesta}") 
        if "|" in respuesta:
            partes = respuesta.split("|", 1)
            return partes[0].strip().lower(), partes[1].strip()
    except Exception as e:
        print(f"Error extrayendo entidad de mensaje con Ollama: {e}")
    return None, None
