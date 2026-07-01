import pyttsx3
import time

def speak(label):
    print(f"Probando hablar despues de: {label}", flush=True)
    try:
        engine = pyttsx3.init()
        engine.say(f"Prueba despues de {label}")
        engine.runAndWait()
        print("   [Éxito] Hablado.", flush=True)
    except Exception as e:
        print(f"   [Fallo] {e}", flush=True)

speak("inicio")

import psycopg2
speak("psycopg2")

import speech_recognition
speak("speech_recognition")

import langchain_ollama
speak("langchain_ollama")

import ollama
speak("ollama")

import pywhatkit
speak("pywhatkit")

import pyautogui
speak("pyautogui")

print("Pruebas de conflicto finalizadas.", flush=True)
