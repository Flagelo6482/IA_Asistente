import psycopg2
import os
import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3 # Para que Frank hable físicamente
import webbrowser # Para abrir páginas web si es necesario
import pywhatkit # Para tareas rápidas como reproducir videos de YouTube


# Cargar configuración
load_dotenv()
# Configuración de Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-3-flash-preview')

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
            password=os.getenv("DB_PASS")
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
                if "reproduce" in comando or "pon la musica de" in comando:
                    musica = comando.replace("reproduce", "").replace("pon la musica de", "").strip()
                    print(f"Frank: Buscando '{musica}' en Youtube...")
                    #Funcion de YOUTUBE
                    reproducir_en_youtube(musica)
                    #Guardamos en HISTORIAL
                    guardar_en_historial_completo(comando, f"Reproduciendo {musica}")
                else:
                    respuesta = obtener_respuesta_gemini(comando)
                    print(f"Frank: {respuesta}")
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