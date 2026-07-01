import pyttsx3
import threading
import queue

# Cola para almacenar los textos por reproducir en segundo plano
_speech_queue = queue.Queue()
_speech_thread = None
_engine = None

def _speech_worker_loop():
    """Bucle del hilo secundario que inicializa y opera el motor de voz de forma segura."""
    global _engine
    while True:
        try:
            texto = _speech_queue.get()
            if texto is None:
                break
            
            # Re-inicializar localmente en cada texto para evitar bloqueos del estado interno
            # tras usar engine.stop() de Windows SAPI5
            _engine = pyttsx3.init()
            _engine.say(texto)
            _engine.runAndWait()
            _engine = None
            _speech_queue.task_done()
        except Exception as e:
            _engine = None

def iniciar_hilo_voz():
    """Garantiza que el hilo de procesamiento de audio en segundo plano esté activo."""
    global _speech_thread
    if _speech_thread is None or not _speech_thread.is_alive():
        _speech_thread = threading.Thread(target=_speech_worker_loop, daemon=True)
        _speech_thread.start()

def hablar(texto):
    """Muestra el texto en la consola e inicia la síntesis de voz en segundo plano sin bloquear el terminal."""
    iniciar_hilo_voz()
    print(f"Frank: {texto}", flush=True)
    
    # Detiene cualquier reproducción en curso e inserta la nueva frase
    detener_habla()
    _speech_queue.put(texto)

def detener_habla():
    """Detiene inmediatamente el motor de voz de Windows y vacía los textos en espera de la cola."""
    global _engine
    # Vaciar los mensajes pendientes en la cola
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break
            
    # Indicar al sintetizador SAPI5 que se detenga
    if _engine:
        try:
            _engine.stop()
        except Exception:
            pass
