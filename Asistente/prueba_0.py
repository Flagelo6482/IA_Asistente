import psycopg2
import os
import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3 # Para que Frank hable físicamente
import webbrowser # Para abrir páginas web si es necesario
import pywhatkit # Para tareas rápidas como reproducir videos de YouTube
from langchain_ollama import OllamaLLM
import pyautogui
import time
import ollama
import subprocess
import random


#Modelo de ollama
llm_local = OllamaLLM(model="llama3")
# Cargar configuración
load_dotenv()
# Configuración de Gemini
#genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#model = genai.GenerativeModel('models/gemini-3-flash-preview')

# Configuración de Voz (Salida de audio)
engine = pyttsx3.init()
def hablar(texto):
    print(f"Frank: {texto}")
    engine.say(texto)
    engine.runAndWait()

def obtener_respuesta_gemini(consulta_usuario):
    # Frank ahora sabe quién eres y dónde estás
    prompt_sistema = (
        "Eres Frank, un asistente virtual avanzado en Perú. "
        "Tu usuario es un joven de 24 años (1.80m, 69kg) que sigue un plan de déficit calórico. "
        f"Consulta del usuario: {consulta_usuario}"
    )
    
    try:
        response = model.generate_content(prompt_sistema)
        return response.text
    except Exception as e:
        print(f"Error real de la API: {e}")
        return "Hubo un pequeño error en mi núcleo de procesamiento."

def conectar_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            client_encoding='utf8'
        )
        return conn
    except Exception as e:
        print(f"Error conectando a pgAdmin: {e}")
        return None

def escuchar_frank():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[Escuchando...] Di algo...") # Feedback visual
        r.adjust_for_ambient_noise(source, duration=0.5) # Ajuste más rápido
        audio = r.listen(source)

    try:
        print("[Procesando voz...]")
        # El parámetro language="es-PE" es ideal para tu ubicación en Perú
        texto = r.recognize_google(audio, language="es-PE")
        print(f">>> Tú dijiste: {texto}") # ESTO ES LO QUE NECESITAS VER
        return texto.lower()
    except sr.UnknownValueError:
        print("!!! Error: No entendí lo que dijiste.")
        return ""
    except sr.RequestError as e:
        print(f"!!! Error de conexión: {e}")
        return ""
    except Exception as e:
        print(f"!!! Error inesperado: {e}")
        return ""

def guardar_en_historial_completo(comando, respuesta):
    conn = conectar_db()
    if conn:
        cur = conn.cursor()
        query = """
            INSERT INTO historial_interacciones 
            (usuario_id, dispositivo_id, comando_original, respuesta_frank, intencion_detectada) 
            VALUES (%s, %s, %s, %s, %s)
        """
        # Aquí podrías usar Gemini para detectar la 'intención', por ahora ponemos 'GENERAL'
        cur.execute(query, (1, 1, comando, respuesta, 'CONSULTA_GENERAL'))
        conn.commit()
        cur.close()
        conn.close()

def obtener_respuesta_ollama(consulta_usuario):
    # Mantenemos tu prompt de sistema para que no pierda su "esencia"
    prompt_sistema = (
        "Eres Frank, un asistente virtual avanzado en Perú. "
        "Tu usuario es un joven de 24 años (1.80m, 69kg)."
    )
    
    try:
        # Aquí llamamos a Ollama en lugar de a Google
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': consulta_usuario},
        ])
        return response['message']['content']
    except Exception as e:
        print(f"Error local de Ollama: {e}")
        return "Parece que Ollama no está respondiendo en este momento."

# ======================================= #
# FUNCIONES QUE REALIZARA EL ASISTENTE    #
# ======================================= #
def abrir_web(url):
    """Abre una página web específica."""
    webbrowser.open(url)
    return f"He abierto la página {url} para ti."

def ejecutar_aplicacion(nombre_app):
    """Intenta abrir una aplicación local."""
    # Ejemplo para Windows:
    if "calculadora" in nombre_app:
        os.system("calc")
    elif "code" in nombre_app:
        os.system("code") # Abre VS Code
    return f"Iniciando {nombre_app}."

def reproducir_en_youtube(busqueda):
    """Busca y reproduce el primer video encontrado en YouTube."""
    try:
        # Esto abrirá el navegador y pondrá el video automáticamente
        pywhatkit.playonyt(busqueda)
        return f"Claro, reproduciendo {busqueda} en YouTube."
    except Exception as e:
        return f"Hubo un error al intentar poner la música: {e}"

def enviar_whatsapp_contacto(alias, mensaje):
    conn = conectar_db()
    if conn:
        cur = conn.cursor()
        # Esta es la query que busca al 'sonso' en tu tabla agenda_contactos
        cur.execute("SELECT numero_celular FROM agenda_contactos WHERE nombre_alias = %s", (alias.lower(),))
        resultado = cur.fetchone()
        
        if resultado:
            numero = resultado[0] # <--- Asegúrate de que esto tenga 12 espacios (sangría)
            print(f"Frank: Iniciando protocolo de envío para {alias}...")
            
            # 1. Abrimos el chat y escribimos el mensaje
            # wait_time=15 es ideal para que cargue WhatsApp Web en tu PC GAMER
            pywhatkit.sendwhatmsg_instantly(numero, mensaje, wait_time=15, tab_close=True)
            
            # 2. Pausa de seguridad para que el navegador esté al frente
            time.sleep(3) 
            
            # 3. ¡EL TRUCO DE JARVIS! Simula presionar Enter
            pyautogui.press('enter')
            
            cur.close()
            conn.close()
            return f"Orden ejecutada. Mensaje enviado a {alias}."
        else:
            cur.close()
            conn.close()
            return f"No encontré a '{alias}' en mi agenda de pgAdmin, Frank."
    return "Error de conexión con la base de datos."

def procesar_comando_whatsapp(comando):
    # Prompt con "Few-Shot Prompting" (ejemplos) para guiar a Llama 3
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
        # Usamos .strip() para limpiar espacios vacíos que mande la RTX 3060 Ti
        respuesta = llm_local.invoke(prompt).strip()
        print(f"DEBUG - IA Procesó: {respuesta}") 
        
        if "|" in respuesta:
            partes = respuesta.split("|", 1)
            return partes[0].strip().lower(), partes[1].strip()
    except Exception as e:
        print(f"Error en Ollama: {e}")
    return None, None

# ======================================= #
# FUNCIONES PARA REPRODUCIR LA MUSICA     #
# ======================================= #
def abrir_carpeta_de_musica(clave):
    conn = conectar_db()
    if conn:
        cur = conn.cursor()
        # Buscamos la ruta usando la clave que detectó Ollama
        cur.execute("SELECT ruta_carpeta FROM biblioteca_musica WHERE clave_activacion = %s", (clave,))
        resultado = cur.fetchone()
        
        if resultado:
            ruta = os.path.normpath(resultado[0])
            hablar(f"Entendido Frank, reproduciendo la lista {clave}.")
            
            try:
                # 2. Listamos archivos y filtramos por mp3 (y otros por si acaso)
                # Usamos .lower() para que encuentre '.MP3' o '.mp3' por igual
                extensiones_musicales = ('.mp3', '.mp4', '.wav', '.flac')
                archivos = [f for f in os.listdir(ruta) if f.lower().endswith(extensiones_musicales)]

                if archivos:
                    # --- EL TRUCO PARA EL ORDEN ALEATORIO ---
                    # Desordenamos la lista de nombres de archivos
                    random.shuffle(archivos)
                    
                    # Creamos el archivo de lista de reproducción (.m3u)
                    playlist_path = os.path.join(ruta, "lista_frank.m3u")
                    
                    with open(playlist_path, "w", encoding="utf-8") as f:
                        for cancion in archivos:
                            f.write(os.path.join(ruta, cancion) + "\n")
                    
                    # Abrimos el archivo de lista de reproducción
                    os.startfile(playlist_path)
                    
                    cur.close()
                    conn.close()
                    return f"He preparado la lista {clave} con {len(archivos)} canciones."
                else:
                    cur.close()
                    conn.close()
                    return "La carpeta existe, pero no encontré archivos .mp3 adentro."
            
            except Exception as e:
                return f"Error al acceder a la carpeta: {e}"
        else:
            cur.close()
            conn.close()
            return f"No encontré ninguna ruta con la clave '{clave}' en la base de datos."
    return "Error de conexión con la base de datos."

def extraer_clave_de_musica(clave):
    prompt = (
        f"Analiza la orden: '{comando}'. "
        "El usuario quiere reproducir una lista de música. "
        "Extrae únicamente el código o clave de la lista (ejemplo: 00, 01, relax). "
        "Responde solo con la clave, sin puntos ni texto extra."
    )
    # Usas tu modelo local para limpiar la orden
    clave = llm_local.invoke(prompt).strip().lower()
    return clave



# BUCLE PRINCIPAL (El programa no se cierra)
if __name__ == "__main__":
    # 1. Cierre de Fase 1: Recuperar datos del usuario al iniciar
    # Frank lee tu perfil desde pgAdmin 4
    conn = conectar_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT nombre, preferencias FROM usuarios WHERE usuario_id = 1")
        usuario = cur.fetchone()
        nombre_usuario = usuario[0] if usuario else "Usuario"
        cur.close()
        conn.close()
        
    #hablar("Sistema Frank iniciado y conectado a la base de datos.")
    print(f"--- Sistema Frank iniciado para {nombre_usuario} ---")
    print("Escribe 'salir' para cerrar o 'adiós frank' para terminar la sesión.")
    
    while True:
        #frase = escuchar_frank()
        frase = input("\n[Tú]: ").lower().strip()
        
        if not frase:
            continue
        
        if frase == "salir" or "adios frank" in frase:
            print("Entendido. Guardando sesión en pgAdmin y cerrando. Hasta pronto.")
            break
        
        if "frank" in frase:
            comando = frase.replace("frank", "").strip()
            
            if comando:
                # ================================================ #
                # DETECCIÓN DE INTENCIÓN DE WHATSAPP
                # ================================================ #
                if "whatsapp" in comando or "mensaje" in comando or "escríbele a" in comando:
                    # El "Mozo" (IA) extrae la información
                    contacto, mensaje_extraido = procesar_comando_whatsapp(comando)
                    if contacto and mensaje_extraido:
                        # Ahora enviamos el mensaje que la IA limpió, no el comando original
                        resultado = enviar_whatsapp_contacto(contacto, mensaje_extraido)
                        hablar(resultado)
                    else:
                        hablar("No pude filtrar los datos del mensaje, Frank.")
                # ================================================ #
                # DETECCIÓN PARA REPRODUCIR MUSICA LOCAL >:3
                # ================================================ #
                elif "reproduce la lista" in comando or "pon la lista" in comando:
                    clave_limpia = extraer_clave_de_musica(comando)
                    print(f"Clave detectada: {clave_limpia}")
                    resultado = abrir_carpeta_de_musica(clave_limpia)
                    hablar(resultado)
                # ================================================ #
                # DETECCIÓN PARA REPRODUCIR MUSICA EN YOUTUBE
                # ================================================ #
                elif "reproduce" in comando or "pon la musica de" in comando:
                    musica = comando.replace("reproduce", "").replace("pon la musica de", "").strip()
                    print(f"Frank: Buscando '{musica}' en Youtube...")
                    #Funcion de YOUTUBE
                    reproducir_en_youtube(musica)
                    #Guardamos en HISTORIAL
                    guardar_en_historial_completo(comando, f"Reproduciendo {musica}")
                else:
                    respuesta = obtener_respuesta_ollama(comando)
                    hablar(respuesta)
                    guardar_en_historial_completo(comando, respuesta)
            else:
                print("Frank: ¿Sí? Estoy escuchando.")
                    
        
        #if "frank" in frase:
        #    # Limpiamos el comando para quitar la palabra de activación
        #    comando = frase.replace("frank", "").strip()
        #    
        #    if comando:
        #        # LÓGICA DE ACCIÓN: ¿Es una orden de música?
        #        if "reproduce" in comando or "pon la música de" in comando:
        #            musica = comando.replace("reproduce", "").replace("pon la música de", "").strip()
        #            mensaje_confirmacion = reproducir_en_youtube(musica)
        #            hablar(mensaje_confirmacion)
        #            guardar_en_historial_completo(comando, mensaje_confirmacion)
        #        
        #        # LÓGICA DE CONVERSACIÓN: Si no es música, es una pregunta para la IA
        #        else:
        #            respuesta = obtener_respuesta_gemini(comando)
        #            hablar(respuesta)
        #            guardar_en_historial_completo(comando, respuesta)
        #    else:
        #        hablar("¿Sí? Estoy escuchando.")
        #if "adiós frank" in frase:
        #    hablar("Entendido. Apagando sistemas. Hasta pronto.")
        #    break