import pyttsx3
import threading
import queue
import time

_speech_queue = queue.Queue()
_speech_thread = None
_engine = None

def _speech_worker_loop():
    global _engine
    while True:
        try:
            texto = _speech_queue.get()
            if texto is None:
                break
            print(f"-> Iniciando TTS para: '{texto}'", flush=True)
            # Re-inicializar localmente en cada texto para evitar bloqueos del estado interno
            _engine = pyttsx3.init()
            _engine.say(texto)
            _engine.runAndWait()
            _engine = None
            print(f"-> Terminado TTS para: '{texto}'", flush=True)
            _speech_queue.task_done()
        except Exception as e:
            print(f"Error en loop: {e}", flush=True)
            _engine = None

def iniciar_hilo():
    global _speech_thread
    if _speech_thread is None or not _speech_thread.is_alive():
        _speech_thread = threading.Thread(target=_speech_worker_loop, daemon=True)
        _speech_thread.start()

def hablar(texto):
    iniciar_hilo()
    detener_habla()
    _speech_queue.put(texto)

def detener_habla():
    global _engine
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break
    if _engine:
        try:
            _engine.stop()
            print("-> Parada ejecutada con éxito", flush=True)
        except Exception as e:
            print(f"-> Detener falló: {e}", flush=True)

# Test
iniciar_hilo()
hablar("Frase larga uno que vamos a interrumpir rápidamente.")
time.sleep(1)
detener_habla()
time.sleep(1)
hablar("Frase corta dos que debería escucharse completa.")
time.sleep(2)
hablar("Frase corta tres que también debería escucharse completa.")
time.sleep(3)
print("Test completado.", flush=True)
