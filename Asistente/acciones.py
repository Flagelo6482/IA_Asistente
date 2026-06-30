import asyncio
import logging
import os
import random
import tempfile
import time
import webbrowser

import pyautogui
import pyttsx3
import pywhatkit
import schedule
import speech_recognition as sr

from config import IDIOMA_VOZ, FRANK_VOZ
from db import (
    guardar_recordatorio,
    obtener_numero_contacto,
    obtener_ruta_musica,
    obtener_recordatorios_activos,
)

log = logging.getLogger(__name__)

_engine = pyttsx3.init()
_alarmas_programadas: set[int] = set()

# Detectamos si edge-tts está disponible al iniciar
try:
    import edge_tts
    _EDGE_TTS_DISPONIBLE = True
except ImportError:
    _EDGE_TTS_DISPONIBLE = False
    log.warning("edge-tts no está instalado. Usando pyttsx3 (voz robótica). "
                "Instala con: pip install edge-tts playsound")

try:
    from playsound import playsound as _playsound
    _PLAYSOUND_DISPONIBLE = True
except ImportError:
    _PLAYSOUND_DISPONIBLE = False


# ============================================ #
# VOZ                                          #
# ============================================ #

async def _generar_audio_edge(texto: str, voz: str, ruta: str):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(ruta)


def _hablar_edge(texto: str) -> bool:
    """Intenta hablar con edge-tts. Devuelve False si falla (sin internet o error)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            ruta_audio = f.name
        asyncio.run(_generar_audio_edge(texto, FRANK_VOZ, ruta_audio))

        if _PLAYSOUND_DISPONIBLE:
            _playsound(ruta_audio)
        else:
            os.startfile(ruta_audio)
            # Pausa aproximada según longitud del texto
            time.sleep(max(2.0, len(texto) * 0.055))

        try:
            os.remove(ruta_audio)
        except OSError:
            pass
        return True
    except Exception as e:
        log.warning("edge-tts falló (%s). Usando pyttsx3 como respaldo.", e)
        return False


def hablar(texto: str):
    log.info("Frank: %s", texto)
    print(f"Frank: {texto}")

    if _EDGE_TTS_DISPONIBLE and _hablar_edge(texto):
        return

    # Fallback: pyttsx3 (funciona sin internet)
    _engine.say(texto)
    _engine.runAndWait()


def escuchar() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[Escuchando...] Di algo...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language=IDIOMA_VOZ)
        log.debug("Voz reconocida: %s", texto)
        return texto.lower()
    except sr.UnknownValueError:
        log.warning("No se pudo entender el audio.")
        return ""
    except sr.RequestError as e:
        log.error("Error de conexión con Google Speech: %s", e)
        return ""


# ============================================ #
# MÚSICA                                       #
# ============================================ #

def reproducir_musica_local(clave: str) -> str:
    ruta = obtener_ruta_musica(clave)
    if not ruta:
        return f"No encontré ninguna lista con la clave '{clave}' en la base de datos."

    ruta = os.path.normpath(ruta)
    extensiones = ('.mp3', '.mp4', '.wav', '.flac')

    try:
        archivos = [f for f in os.listdir(ruta) if f.lower().endswith(extensiones)]
        if not archivos:
            return "La carpeta existe, pero no encontré archivos de música adentro."

        random.shuffle(archivos)
        playlist_path = os.path.join(ruta, "lista_frank.m3u")
        with open(playlist_path, "w", encoding="utf-8") as f:
            for cancion in archivos:
                f.write(os.path.join(ruta, cancion) + "\n")

        os.startfile(playlist_path)
        log.info("Playlist '%s' iniciada con %d canciones.", clave, len(archivos))
        return f"Lista '{clave}' iniciada con {len(archivos)} canciones."
    except Exception as e:
        log.error("Error reproduciendo música local: %s", e)
        return f"Error al acceder a la carpeta: {e}"


def reproducir_en_youtube(busqueda: str) -> str:
    log.info("Reproduciendo en YouTube: %s", busqueda)
    try:
        pywhatkit.playonyt(busqueda)
        return f"Reproduciendo '{busqueda}' en YouTube."
    except Exception as e:
        log.error("Error en YouTube: %s", e)
        return f"Error al reproducir en YouTube: {e}"


# ============================================ #
# WHATSAPP                                     #
# ============================================ #

def enviar_whatsapp(alias: str, mensaje: str) -> str:
    numero = obtener_numero_contacto(alias)
    if not numero:
        return f"No encontré a '{alias}' en la agenda."
    try:
        log.info("Enviando WhatsApp a %s (%s)", alias, numero)
        pywhatkit.sendwhatmsg_instantly(numero, mensaje, wait_time=15, tab_close=True)
        time.sleep(3)
        pyautogui.press('enter')
        return f"Mensaje enviado a {alias}."
    except Exception as e:
        log.error("Error enviando WhatsApp a %s: %s", alias, e)
        return f"Error al enviar el mensaje: {e}"


# ============================================ #
# APLICACIONES Y WEB                           #
# ============================================ #

def abrir_web(url: str) -> str:
    webbrowser.open(url)
    log.info("Abriendo web: %s", url)
    return f"He abierto {url}."


def ejecutar_aplicacion(nombre_app: str) -> str:
    nombre = nombre_app.lower()
    if "calculadora" in nombre:
        os.system("calc")
    elif "code" in nombre or "vscode" in nombre:
        os.system("code")
    else:
        log.warning("Aplicación no reconocida: %s", nombre_app)
        return f"No sé cómo abrir '{nombre_app}'."
    log.info("Aplicación iniciada: %s", nombre_app)
    return f"Iniciando {nombre_app}."


# ============================================ #
# ALARMAS Y RECORDATORIOS                      #
# ============================================ #

def _crear_disparador(descripcion: str):
    def disparar():
        hablar(f"Recordatorio: {descripcion}")
        log.info("Alarma disparada: %s", descripcion)
    return disparar


def agregar_alarma(descripcion: str, hora_hhmm: str, guardar_en_db: bool = True) -> str:
    """Programa una alarma diaria a la hora indicada (formato HH:MM en 24h)."""
    try:
        schedule.every().day.at(hora_hhmm).do(_crear_disparador(descripcion))
        log.info("Alarma programada: %s a las %s", descripcion, hora_hhmm)
        if guardar_en_db:
            guardar_recordatorio(descripcion, hora_hhmm)
        return f"Recordatorio programado para las {hora_hhmm}: {descripcion}"
    except Exception as e:
        log.error("Error programando alarma: %s", e)
        return f"No pude programar la alarma: {e}"


def cargar_alarmas_desde_db():
    """Carga y programa todos los recordatorios activos guardados en la BD."""
    recordatorios = obtener_recordatorios_activos()
    for rec in recordatorios:
        rec_id, descripcion, hora_alarma, _ = rec
        if rec_id not in _alarmas_programadas:
            hora_str = hora_alarma.strftime("%H:%M") if hasattr(hora_alarma, "strftime") else str(hora_alarma)
            schedule.every().day.at(hora_str).do(_crear_disparador(descripcion))
            _alarmas_programadas.add(rec_id)
            log.info("Alarma cargada desde BD: %s a las %s", descripcion, hora_str)
    if recordatorios:
        log.info("%d recordatorio(s) cargado(s) desde la base de datos.", len(recordatorios))


def ejecutar_alarmas_pendientes():
    """Ejecuta las alarmas cuya hora ya llegó. Llamar en el bucle principal."""
    schedule.run_pending()
