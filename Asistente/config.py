import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3")

USUARIO_ID    = int(os.getenv("USUARIO_ID", "1"))
DISPOSITIVO_ID = int(os.getenv("DISPOSITIVO_ID", "1"))

IDIOMA_VOZ = "es-PE"
PALABRA_ACTIVACION = "frank"

# Voz de Frank para edge-tts. Opciones recomendadas:
#   es-PE-AlexNeural   → masculina, Perú
#   es-PE-CamilaNeural → femenina,  Perú
#   Ejecuta probar_voces.py para escuchar todas las opciones.
FRANK_VOZ = os.getenv("FRANK_VOZ", "es-PE-AlexNeural")
