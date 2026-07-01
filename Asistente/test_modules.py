import sys
import time

def log(msg):
    print(msg, flush=True)

log("1. Probando base de datos y obtención de nombre...")
try:
    from config.database import obtener_nombre_usuario
    nombre = obtener_nombre_usuario(1)
    log(f"   [Éxito] Nombre de usuario obtenido: {nombre}")
except Exception as e:
    log(f"   [Fallo] DB: {e}")

log("2. Probando obtención de respuesta con Ollama y prompt_sistema...")
try:
    from core.brain import obtener_respuesta_ollama
    log("   [Acción] Enviando 'hola' con prompt_sistema...")
    inicio = time.time()
    respuesta = obtener_respuesta_ollama("hola")
    fin = time.time()
    log(f"   [Éxito] Ollama respondió en {fin - inicio:.2f} segundos:")
    log(f"   >>> {respuesta}")
except Exception as e:
    log(f"   [Fallo] Ollama con prompt_sistema: {e}")

log("3. Probando hablar la respuesta...")
try:
    from core.speaker import hablar
    log("   [Acción] Intentando hablar la respuesta...")
    hablar(respuesta)
    log("   [Éxito] Habla completada.")
except Exception as e:
    log(f"   [Fallo] Speaker: {e}")

log("4. Probando guardar en el historial completo...")
try:
    from config.database import guardar_en_historial_completo
    log("   [Acción] Guardando en la tabla historial_interacciones...")
    inicio = time.time()
    guardar_en_historial_completo("hola", respuesta, "OLLAMA_LOCAL_TEST")
    fin = time.time()
    log(f"   [Éxito] Guardado en historial en {fin - inicio:.4f} segundos.")
except Exception as e:
    log(f"   [Fallo] Guardar historial: {e}")

log("Prueba finalizada con todas las subfunciones de main.py.")
sys.exit(0)
