import os
import google.generativeai as genai
from langchain_ollama import OllamaLLM
import ollama
from dotenv import load_dotenv

# Cargar configuración del .env
load_dotenv()

# Inicializar modelo local de Ollama (Llama 3)
try:
    llm_local = OllamaLLM(model="llama3")
except Exception as e:
    print(f"Advertencia: No se pudo instanciar langchain_ollama: {e}")
    llm_local = None

# Configurar API de Gemini
api_key = os.getenv("GEMINI_API_KEY")
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Usamos gemini-1.5-flash como modelo estándar de producción
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configurando la API de Gemini: {e}")

# Prompt de personalidad e historia de Frank
prompt_sistema = (
    "Eres Frank, un asistente de IA amigable y directo en Perú. Tu usuario es un joven de 24 años (1.80m, 69kg) en plan de déficit calórico.\n"
    "REGLAS DE CONVERSACIÓN:\n"
    "1. NO inicies tus respuestas con saludos como '¡Hola!', '¡Hola Frank!' o recordatorios de quién eres ('Como asistente virtual avanzado...'), a menos que sea la primera interacción absoluta.\n"
    "2. Sé directo, conciso y ve al grano en tus respuestas. Evita introducciones y cierres formales redundantes.\n"
    "3. Adopta un tono de colega amigable y casual en español peruano, sin sonar excesivamente formal."
)

def obtener_respuesta_gemini(consulta_usuario):
    """Envía la consulta a Gemini en la nube."""
    if not model:
        raise ValueError("El modelo Gemini no está configurado.")
    prompt = f"{prompt_sistema}\nConsulta del usuario: {consulta_usuario}"
    response = model.generate_content(prompt)
    return response.text

def obtener_respuesta_ollama(consulta_usuario):
    """Envía la consulta a Ollama corriendo localmente en tu GPU (Llama3)."""
    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': consulta_usuario},
        ])
        return response['message']['content']
    except Exception as e:
        print(f"Error local de Ollama: {e}")
        return "Parece que Ollama no está respondiendo localmente en este momento."

def procesar_con_ia(consulta_usuario, preferir_offline=True):
    """
    Orquesta la generación de respuestas de IA.
    Si preferir_offline=False y hay conexión a internet, intentará usar Gemini API.
    Si falla o está en modo offline, caerá transparentemente en Ollama (Llama3 local).
    """
    if not preferir_offline and model:
        try:
            return obtener_respuesta_gemini(consulta_usuario), 'GEMINI_CLOUD'
        except Exception as e:
            print(f"Error en Gemini Cloud (Posiblemente offline): {e}. Usando fallback a Ollama local...")
            return obtener_respuesta_ollama(consulta_usuario), 'OLLAMA_LOCAL_FALLBACK'
    else:
        return obtener_respuesta_ollama(consulta_usuario), 'OLLAMA_LOCAL'

def extraer_clave_de_musica(comando):
    """Usa el LLM local para depurar la clave de la playlist solicitada."""
    if not llm_local:
        # Fallback simple si LangChain no responde
        return comando.replace("reproduce la lista", "").replace("pon la lista", "").strip().lower()
    
    prompt = (
        f"Analiza la orden: '{comando}'. "
        "El usuario quiere reproducir una lista de música. "
        "Extrae únicamente el código o clave de la lista (ejemplo: 00, 01, relax). "
        "Responde solo con la clave, sin puntos ni texto extra."
    )
    try:
        clave = llm_local.invoke(prompt).strip().lower()
        return clave
    except Exception as e:
        print(f"Error extrayendo clave con LLM: {e}")
        return comando.replace("reproduce la lista", "").replace("pon la lista", "").strip().lower()
