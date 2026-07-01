import speech_recognition as sr

def escuchar_frank():
    """Captura el audio del micrófono y lo traduce a texto utilizando Google Speech Recognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[Escuchando...] Di algo...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)

    try:
        print("[Procesando voz...]")
        # recognize_google requiere internet y envía el audio a los servidores de Google
        texto = r.recognize_google(audio, language="es-PE")
        print(f">>> Tú dijiste: {texto}")
        return texto.lower()
    except sr.UnknownValueError:
        print("!!! Error: No entendí lo que dijiste o no hay sonido.")
        return ""
    except sr.RequestError as e:
        print(f"!!! Error de conexión: {e}. (Recomendación: instala Vosk para modo 100% offline)")
        return ""
    except Exception as e:
        print(f"!!! Error inesperado en entrada de audio: {e}")
        return ""
