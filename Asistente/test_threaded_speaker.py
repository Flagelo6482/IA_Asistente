import pyttsx3
import threading
import queue
import time

_speech_queue = queue.Queue()
_speech_thread = None
_engine = None

def _speech_worker_loop():
    global _engine
    try:
        _engine = pyttsx3.init()
    except Exception as e:
        print(f"Error inicializando TTS: {e}")
        return

    while True:
        try:
            texto = _speech_queue.get()
            if texto is None:
                break
            _engine.say(texto)
            _engine.runAndWait()
            _speech_queue.task_done()
        except Exception as e:
            print(f"Error en hilo de voz: {e}")

def iniciar_hilo():
    global _speech_thread
    if _speech_thread is None or not _speech_thread.is_alive():
        _speech_thread = threading.Thread(target=_speech_worker_loop, daemon=True)
        _speech_thread.start()

def hablar(texto):
    iniciar_hilo()
    print(f"Hablando: {texto}", flush=True)
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
        except Exception as e:
            print(f"Detener falló: {e}")

# Ejecutar prueba
iniciar_hilo()
hablar("Esta es una frase muy larga que debería ser interrumpida a la mitad para demostrar que el hilo secundario funciona de forma no bloqueante y responde al comando de parada.")
time.sleep(2)
print("Intentando interrumpir...", flush=True)
detener_habla()
time.sleep(1)
hablar("Nueva frase corta.")
time.sleep(2)
print("Prueba finalizada.", flush=True)
