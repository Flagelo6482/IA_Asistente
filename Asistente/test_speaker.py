import pyttsx3
import time

def test_speak(text):
    print(f"Probando: '{text}'", flush=True)
    engine = pyttsx3.init()
    start = time.time()
    engine.say(text)
    engine.runAndWait()
    end = time.time()
    print(f"Completado en {end - start:.2f} segundos.", flush=True)

print("Iniciando pruebas de altavoz...", flush=True)
test_speak("Hello world")
test_speak("Hola mundo")
test_speak("¡Hola! ¿Cómo estás?")
test_speak("Hola Frank, tu asistente virtual avanzado en Perú. Me alegra poder ayudarte en tus objetivos de salud y bienestar.")
print("Todas las pruebas del altavoz completadas.", flush=True)
