import logging
import ollama
from langchain_ollama import OllamaLLM
from config import OLLAMA_MODEL

log = logging.getLogger(__name__)

_llm = OllamaLLM(model=OLLAMA_MODEL)

_PERFIL_BASE = (
    "Eres Frank, un asistente virtual personal avanzado en Perú. "
    "Tu usuario es un joven de 24 años (1.80m, 69kg) que sigue un plan de déficit calórico. "
    "Responde siempre en español, de forma concisa y natural. "
    "Usa los datos del usuario para personalizar cada respuesta cuando sea relevante."
)

# Historial de mensajes de la sesión actual (se resetea al salir)
_historial_chat: list[dict] = []

INTENCIONES_VALIDAS = {
    "WHATSAPP", "MUSICA_LOCAL", "MUSICA_YOUTUBE",
    "WEB", "APP", "ALARMA",
    "GUARDAR_MEMORIA", "GUARDAR_TAREA", "GUARDAR_RUTINA", "OLVIDAR",
    "VER_TAREAS",
    "CONVERSACION",
}


def _construir_prompt_sistema() -> str:
    """Genera el system prompt con el contexto actualizado del usuario."""
    from db import construir_contexto_usuario
    contexto = construir_contexto_usuario()
    if contexto:
        return f"{_PERFIL_BASE}\n\nLO QUE SABES SOBRE TU USUARIO:\n{contexto}"
    return _PERFIL_BASE


def obtener_respuesta(consulta: str) -> str:
    """Consulta al LLM manteniendo el historial y con contexto dinámico del usuario."""
    _historial_chat.append({"role": "user", "content": consulta})
    try:
        mensajes = [{"role": "system", "content": _construir_prompt_sistema()}] + _historial_chat
        response = ollama.chat(model=OLLAMA_MODEL, messages=mensajes)
        respuesta = response["message"]["content"]
        _historial_chat.append({"role": "assistant", "content": respuesta})
        return respuesta
    except Exception as e:
        log.error("Error en Ollama: %s", e)
        _historial_chat.pop()
        return "Parece que Ollama no está respondiendo en este momento."


def limpiar_historial():
    _historial_chat.clear()
    log.info("Historial de conversación limpiado.")


def detectar_intencion(comando: str) -> str:
    """Clasifica el comando usando el LLM. Fallback a CONVERSACION si falla."""
    prompt = (
        f"Clasifica la intención de este comando de asistente virtual: '{comando}'\n\n"
        "Intenciones posibles:\n"
        "- WHATSAPP: enviar mensaje de WhatsApp\n"
        "- MUSICA_LOCAL: reproducir lista de música guardada\n"
        "- MUSICA_YOUTUBE: buscar y reproducir en YouTube\n"
        "- WEB: abrir una página web\n"
        "- APP: abrir una aplicación local\n"
        "- ALARMA: crear un recordatorio o alarma con hora específica\n"
        "- GUARDAR_MEMORIA: guardar un hecho, preferencia, hábito u objetivo del usuario (ej: 'recuerda que me gusta X')\n"
        "- GUARDAR_TAREA: guardar una tarea o pendiente (ej: 'tengo que X', 'no olvides que debo X')\n"
        "- GUARDAR_RUTINA: guardar una actividad recurrente con horario (ej: 'voy al gym los lunes')\n"
        "- OLVIDAR: olvidar o eliminar un dato guardado (ej: 'olvida que...', 'ya no...')\n"
        "- VER_TAREAS: el usuario quiere ver sus tareas pendientes\n"
        "- CONVERSACION: cualquier otra consulta, pregunta o conversación general\n\n"
        "Responde ÚNICAMENTE con una de las palabras de la lista, sin puntos ni texto extra."
    )
    try:
        respuesta = _llm.invoke(prompt).strip().upper()
        for intencion in INTENCIONES_VALIDAS:
            if intencion in respuesta:
                return intencion
        log.warning("Intención no reconocida: '%s'. Usando CONVERSACION.", respuesta)
        return "CONVERSACION"
    except Exception as e:
        log.error("Error detectando intención: %s", e)
        return "CONVERSACION"


# ============================================================
# EXTRACTORES DE MEMORIA, TAREA Y RUTINA
# ============================================================

def extraer_memoria(comando: str) -> tuple[str, str, str, str, int]:
    """Extrae (tipo, categoria, clave, valor, relevancia) de un comando de memorización."""
    prompt = (
        f"El usuario dijo: '{comando}'. Quiere que su asistente recuerde este dato.\n\n"
        "Extrae:\n"
        "1. TIPO: uno de → PREFERENCIA | HABITO | OBJETIVO | DATO_PERSONAL | AVERSION | CONTEXTO\n"
        "2. CATEGORIA: tema general (musica, comida, ejercicio, trabajo, salud, etc.)\n"
        "3. CLAVE: nombre corto del dato (ej: 'musica favorita', 'hora de gym')\n"
        "4. VALOR: el dato en sí (ej: 'rock y metal', '6am lunes y jueves')\n"
        "5. RELEVANCIA: número del 1 al 10 según qué tan importante parece (10=muy importante)\n\n"
        "Responde ÚNICAMENTE en este formato: TIPO | CATEGORIA | CLAVE | VALOR | RELEVANCIA\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'recuerda que me gusta el rock'\n"
        "Salida: PREFERENCIA | musica | musica favorita | rock | 6\n\n"
        "Entrada: 'recuerda que mi objetivo es bajar a 65kg antes de diciembre'\n"
        "Salida: OBJETIVO | salud | objetivo de peso | bajar a 65kg antes de diciembre | 9\n\n"
        "TU RESPUESTA:"
    )
    try:
        respuesta = _llm.invoke(prompt).strip()
        partes = [p.strip() for p in respuesta.split("|")]
        if len(partes) >= 5:
            tipo = partes[0].upper()
            categoria = partes[1].lower()
            clave = partes[2].lower()
            valor = partes[3]
            relevancia = int(partes[4]) if partes[4].isdigit() else 5
            relevancia = max(1, min(10, relevancia))
            return tipo, categoria, clave, valor, relevancia
    except Exception as e:
        log.error("Error extrayendo memoria: %s", e)
    return "DATO_PERSONAL", "", comando, comando, 5


def extraer_tarea(comando: str) -> tuple[str, str | None, str]:
    """Extrae (descripcion, fecha_limite, prioridad) de un comando de tarea."""
    prompt = (
        f"El usuario dijo: '{comando}'. Quiere guardar una tarea o pendiente.\n\n"
        "Extrae:\n"
        "1. DESCRIPCION: qué tiene que hacer\n"
        "2. FECHA: fecha límite en formato YYYY-MM-DD (o 'ninguna' si no hay)\n"
        "3. PRIORIDAD: alta | media | baja según la urgencia\n\n"
        "Responde ÚNICAMENTE en este formato: DESCRIPCION | FECHA | PRIORIDAD\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'tengo que pagar el internet el 15'\n"
        "Salida: pagar el internet | 2026-06-15 | alta\n\n"
        "Entrada: 'no olvides que debo llamar al doctor'\n"
        "Salida: llamar al doctor | ninguna | media\n\n"
        "TU RESPUESTA:"
    )
    try:
        respuesta = _llm.invoke(prompt).strip()
        partes = [p.strip() for p in respuesta.split("|")]
        if len(partes) >= 3:
            descripcion = partes[0]
            fecha = None if partes[1].lower() in ("ninguna", "none", "") else partes[1]
            prioridad = partes[2].lower() if partes[2].lower() in ("alta", "media", "baja") else "media"
            return descripcion, fecha, prioridad
    except Exception as e:
        log.error("Error extrayendo tarea: %s", e)
    return comando, None, "media"


def extraer_rutina(comando: str) -> tuple[str, str, str, str | None]:
    """Extrae (nombre, dias, hora_inicio, descripcion) de un comando de rutina."""
    prompt = (
        f"El usuario dijo: '{comando}'. Quiere guardar una actividad recurrente.\n\n"
        "Extrae:\n"
        "1. NOMBRE: nombre corto de la actividad (ej: gym, meditación)\n"
        "2. DIAS: días de la semana separados por coma, o 'todos' (ej: lunes,jueves)\n"
        "3. HORA: hora de inicio en formato HH:MM o 'ninguna'\n"
        "4. DESCRIPCION: descripción completa (ej: 'gym los lunes y jueves a las 6am')\n\n"
        "Responde ÚNICAMENTE en este formato: NOMBRE | DIAS | HORA | DESCRIPCION\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'voy al gym los lunes y jueves a las 6am'\n"
        "Salida: gym | lunes,jueves | 06:00 | gym los lunes y jueves a las 6am\n\n"
        "Entrada: 'medito todos los días al despertar'\n"
        "Salida: meditación | todos | ninguna | medita todos los días al despertar\n\n"
        "TU RESPUESTA:"
    )
    try:
        respuesta = _llm.invoke(prompt).strip()
        partes = [p.strip() for p in respuesta.split("|")]
        if len(partes) >= 4:
            nombre = partes[0]
            dias = partes[1]
            hora = None if partes[2].lower() in ("ninguna", "none", "") else partes[2]
            descripcion = partes[3]
            return nombre, dias, hora, descripcion
    except Exception as e:
        log.error("Error extrayendo rutina: %s", e)
    return "rutina", "todos", None, comando


def extraer_clave_a_olvidar(comando: str) -> str:
    """Extrae qué dato quiere que Frank olvide."""
    prompt = (
        f"El usuario dijo: '{comando}'. Quiere que su asistente olvide un dato guardado.\n"
        "Extrae la CLAVE del dato que se debe olvidar (el nombre corto del dato).\n"
        "Responde solo con la clave, sin texto extra.\n\n"
        "EJEMPLO:\n"
        "Entrada: 'olvida que me gusta el rock'\n"
        "Salida: musica favorita\n\n"
        "TU RESPUESTA:"
    )
    try:
        return _llm.invoke(prompt).strip().lower()
    except Exception as e:
        log.error("Error extrayendo clave a olvidar: %s", e)
        return ""


# ============================================================
# EXTRACTORES ORIGINALES (sin cambios)
# ============================================================

def extraer_datos_whatsapp(comando: str) -> tuple[str | None, str | None]:
    prompt = (
        f"Eres un extractor de datos estricto. Analiza: '{comando}'\n\n"
        "REGLAS:\n"
        "1. Extrae el NOMBRE del destinatario (sin preposiciones como 'al', 'a').\n"
        "2. Extrae el MENSAJE exacto que el usuario quiere enviar.\n"
        "3. Responde ÚNICAMENTE en este formato: NOMBRE | MENSAJE\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'envía un mensaje a mama diciendo hola'\n"
        "Salida: mama | hola\n\n"
        "Entrada: 'envia un mensaje al sonso diciéndole que llegue temprano'\n"
        "Salida: sonso | llega temprano\n\n"
        "TU RESPUESTA:"
    )
    try:
        respuesta = _llm.invoke(prompt).strip()
        if "|" in respuesta:
            partes = respuesta.split("|", 1)
            return partes[0].strip().lower(), partes[1].strip()
    except Exception as e:
        log.error("Error extrayendo datos de WhatsApp: %s", e)
    return None, None


def extraer_clave_musica(comando: str) -> str:
    prompt = (
        f"Analiza la orden: '{comando}'. "
        "El usuario quiere reproducir una lista de música guardada. "
        "Extrae únicamente el código o clave de la lista (ejemplos: 00, 01, relax, gym). "
        "Responde solo con la clave, sin puntos ni texto extra."
    )
    try:
        return _llm.invoke(prompt).strip().lower()
    except Exception as e:
        log.error("Error extrayendo clave de música: %s", e)
        return ""


def extraer_datos_alarma(comando: str) -> tuple[str | None, str | None]:
    prompt = (
        f"El usuario dijo: '{comando}'. Quiere programar un recordatorio.\n"
        "Extrae la HORA en formato HH:MM (24 horas) y la DESCRIPCIÓN del recordatorio.\n"
        "Responde ÚNICAMENTE en este formato: HH:MM | DESCRIPCION\n\n"
        "EJEMPLOS:\n"
        "Entrada: 'recuérdame a las 8 de la mañana tomar agua'\n"
        "Salida: 08:00 | tomar agua\n\n"
        "Entrada: 'ponme un recordatorio a las 5:20 para el gym'\n"
        "Salida: 05:20 | ir al gym\n\n"
        "TU RESPUESTA:"
    )
    try:
        respuesta = _llm.invoke(prompt).strip()
        if "|" in respuesta:
            partes = respuesta.split("|", 1)
            return partes[0].strip(), partes[1].strip()
    except Exception as e:
        log.error("Error extrayendo datos de alarma: %s", e)
    return None, None
