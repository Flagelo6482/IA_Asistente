import logging
import psycopg2
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, USUARIO_ID, DISPOSITIVO_ID

log = logging.getLogger(__name__)


def conectar():
    try:
        return psycopg2.connect(
            host=DB_HOST, database=DB_NAME,
            user=DB_USER, password=DB_PASS,
            client_encoding='utf8'
        )
    except Exception as e:
        log.error("Error conectando a la base de datos: %s", e)
        return None


def obtener_usuario():
    conn = conectar()
    if not conn:
        return "Usuario", ""
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT nombre, preferencias FROM usuarios WHERE usuario_id = %s",
                    (USUARIO_ID,)
                )
                row = cur.fetchone()
                return (row[0], row[1]) if row else ("Usuario", "")
    except Exception as e:
        log.error("Error obteniendo datos del usuario: %s", e)
        return "Usuario", ""


def guardar_historial(comando, respuesta, intencion="CONSULTA_GENERAL"):
    # Mapear y normalizar intenciones para cumplir con las restricciones de la clave foránea cat_intenciones
    mapa_intenciones = {
        'WHATSAPP': 'WHATSAPP_SEND',
        'WHATSAPP_SEND': 'WHATSAPP_SEND',
        'MUSICA_LOCAL': 'MUSICA_PEDIDO',
        'MUSICA_YOUTUBE': 'MUSICA_PEDIDO',
        'MUSICA_PEDIDO': 'MUSICA_PEDIDO',
        'DIETA_CONSULTA': 'DIETA_CONSULTA',
        'DIETA_LOG': 'DIETA_LOG',
        'ANIMO_NEGATIVO': 'ANIMO_NEGATIVO',
        'ARC_FACIAL_CONTROL': 'ARC_FACIAL_CONTROL',
        'CONSULTA_GENERAL': 'CONSULTA_GENERAL',
        'CONVERSACION': 'CONSULTA_GENERAL',
        'ALARMA': 'CONSULTA_GENERAL',
        'GUARDAR_MEMORIA': 'CONSULTA_GENERAL',
        'GUARDAR_TAREA': 'CONSULTA_GENERAL',
        'GUARDAR_RUTINA': 'CONSULTA_GENERAL',
        'OLVIDAR': 'CONSULTA_GENERAL',
        'VER_TAREAS': 'CONSULTA_GENERAL',
        'WEB': 'CONSULTA_GENERAL',
        'APP': 'CONSULTA_GENERAL',
        'MAPA': 'CONSULTA_GENERAL',
    }
    intencion_valida = mapa_intenciones.get(intencion.upper(), 'CONSULTA_GENERAL')

    conn = conectar()
    if not conn:
        return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO historial_interacciones
                    (usuario_id, dispositivo_id, comando_original, respuesta_frank, intencion_detectada)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (USUARIO_ID, DISPOSITIVO_ID, comando, respuesta, intencion_valida)
                )
        log.debug("Historial guardado: intención=%s (original=%s)", intencion_valida, intencion)
    except Exception as e:
        log.error("Error guardando historial: %s", e)


def obtener_numero_contacto(alias):
    conn = conectar()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT numero_celular FROM agenda_contactos WHERE nombre_alias = %s",
                    (alias.lower(),)
                )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        log.error("Error buscando contacto '%s': %s", alias, e)
        return None


def obtener_ruta_musica(clave):
    conn = conectar()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT ruta_carpeta FROM biblioteca_musica WHERE clave_activacion = %s",
                    (clave,)
                )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        log.error("Error buscando ruta de música con clave '%s': %s", clave, e)
        return None


def registrar_patron(evento_disparador, accion_siguiente, clave_accion=""):
    """Registra una correlación de comportamiento del usuario."""
    conn = conectar()
    if not conn:
        return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO patrones_usuario
                    (usuario_id, evento_disparador, accion_siguiente, clave_accion)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING""",
                    (USUARIO_ID, evento_disparador, accion_siguiente, clave_accion)
                )
        log.debug("Patrón registrado: %s → %s", evento_disparador, accion_siguiente)
    except Exception as e:
        log.error("Error registrando patrón: %s", e)


def obtener_recordatorios_activos():
    """Carga todos los recordatorios activos de la base de datos."""
    conn = conectar()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT recordatorio_id, descripcion, hora_alarma, dias_semana
                    FROM recordatorios
                    WHERE usuario_id = %s AND activo = TRUE""",
                    (USUARIO_ID,)
                )
                return cur.fetchall()
    except Exception as e:
        log.error("Error obteniendo recordatorios: %s", e)
        return []


def guardar_recordatorio(descripcion, hora_alarma, dias_semana="todos"):
    conn = conectar()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO recordatorios (usuario_id, descripcion, hora_alarma, dias_semana)
                    VALUES (%s, %s, %s, %s) RETURNING recordatorio_id""",
                    (USUARIO_ID, descripcion, hora_alarma, dias_semana)
                )
                return cur.fetchone()[0]
    except Exception as e:
        log.error("Error guardando recordatorio: %s", e)
        return None


# ============================================================
# MEMORIA DINÁMICA
# ============================================================

def guardar_memoria(tipo: str, clave: str, valor: str, categoria: str = "", relevancia: int = 5) -> bool:
    """Inserta o actualiza un hecho/preferencia/hábito del usuario."""
    conn = conectar()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO memoria_usuario
                    (usuario_id, tipo, categoria, clave, valor, relevancia)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (usuario_id, clave)
                    DO UPDATE SET valor = EXCLUDED.valor,
                                  tipo = EXCLUDED.tipo,
                                  categoria = EXCLUDED.categoria,
                                  relevancia = EXCLUDED.relevancia""",
                    (USUARIO_ID, tipo.upper(), categoria.lower(), clave.lower(), valor, relevancia)
                )
        log.info("Memoria guardada: [%s] %s = %s", tipo, clave, valor)
        return True
    except Exception as e:
        log.error("Error guardando memoria: %s", e)
        return False


def obtener_memorias_activas(limite: int = 30) -> list[dict]:
    """Devuelve las memorias activas ordenadas por relevancia descendente."""
    conn = conectar()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT tipo, categoria, clave, valor, relevancia
                    FROM memoria_usuario
                    WHERE usuario_id = %s AND activo = TRUE
                    ORDER BY relevancia DESC, actualizado_en DESC
                    LIMIT %s""",
                    (USUARIO_ID, limite)
                )
                cols = ["tipo", "categoria", "clave", "valor", "relevancia"]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        log.error("Error obteniendo memorias: %s", e)
        return []


def desactivar_memoria(clave: str) -> bool:
    """Marca una memoria como inactiva (Frank 'olvida' ese dato)."""
    conn = conectar()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE memoria_usuario SET activo = FALSE WHERE usuario_id = %s AND clave = %s",
                    (USUARIO_ID, clave.lower())
                )
        log.info("Memoria desactivada: %s", clave)
        return True
    except Exception as e:
        log.error("Error desactivando memoria: %s", e)
        return False


# ============================================================
# RUTINAS
# ============================================================

def guardar_rutina(nombre: str, descripcion: str = "", dias: str = "todos",
                   hora_inicio: str = None, hora_fin: str = None) -> bool:
    conn = conectar()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO rutinas
                    (usuario_id, nombre, descripcion, dias_semana, hora_inicio, hora_fin)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (USUARIO_ID, nombre, descripcion, dias, hora_inicio, hora_fin)
                )
        log.info("Rutina guardada: %s (%s)", nombre, dias)
        return True
    except Exception as e:
        log.error("Error guardando rutina: %s", e)
        return False


def obtener_rutinas_activas() -> list[dict]:
    conn = conectar()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT nombre, descripcion, dias_semana, hora_inicio, hora_fin
                    FROM rutinas
                    WHERE usuario_id = %s AND activo = TRUE
                    ORDER BY hora_inicio ASC NULLS LAST""",
                    (USUARIO_ID,)
                )
                cols = ["nombre", "descripcion", "dias_semana", "hora_inicio", "hora_fin"]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        log.error("Error obteniendo rutinas: %s", e)
        return []


# ============================================================
# TAREAS
# ============================================================

def guardar_tarea(descripcion: str, fecha_limite: str = None, prioridad: str = "media") -> int | None:
    conn = conectar()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO tareas (usuario_id, descripcion, fecha_limite, prioridad)
                    VALUES (%s, %s, %s, %s) RETURNING tarea_id""",
                    (USUARIO_ID, descripcion, fecha_limite or None, prioridad.lower())
                )
                return cur.fetchone()[0]
    except Exception as e:
        log.error("Error guardando tarea: %s", e)
        return None


def obtener_tareas_pendientes(limite: int = 10) -> list[dict]:
    conn = conectar()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT tarea_id, descripcion, fecha_limite, prioridad
                    FROM tareas
                    WHERE usuario_id = %s AND completada = FALSE
                    ORDER BY
                        CASE prioridad WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END,
                        fecha_limite ASC NULLS LAST
                    LIMIT %s""",
                    (USUARIO_ID, limite)
                )
                cols = ["tarea_id", "descripcion", "fecha_limite", "prioridad"]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as e:
        log.error("Error obteniendo tareas: %s", e)
        return []


def completar_tarea(tarea_id: int) -> bool:
    conn = conectar()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tareas SET completada = TRUE, completado_en = NOW() WHERE tarea_id = %s AND usuario_id = %s",
                    (tarea_id, USUARIO_ID)
                )
        log.info("Tarea %d marcada como completada.", tarea_id)
        return True
    except Exception as e:
        log.error("Error completando tarea %d: %s", tarea_id, e)
        return False


# ============================================================
# CONSTRUCTOR DE CONTEXTO (lo usa ia.py en cada respuesta)
# ============================================================

def construir_contexto_usuario() -> str:
    """Genera el bloque de contexto que se inyecta en el prompt de sistema de Frank."""
    secciones = []

    memorias = obtener_memorias_activas()
    if memorias:
        lineas = []
        for m in memorias:
            prefijo = f"[{m['categoria']}] " if m["categoria"] else ""
            lineas.append(f"  - {prefijo}{m['clave']}: {m['valor']}")
        secciones.append("DATOS Y PREFERENCIAS DEL USUARIO:\n" + "\n".join(lineas))

    rutinas = obtener_rutinas_activas()
    if rutinas:
        lineas = []
        for r in rutinas:
            hora = f" a las {r['hora_inicio']}" if r["hora_inicio"] else ""
            lineas.append(f"  - {r['nombre']} ({r['dias_semana']}{hora})")
        secciones.append("RUTINAS:\n" + "\n".join(lineas))

    tareas = obtener_tareas_pendientes()
    if tareas:
        lineas = []
        for t in tareas:
            fecha = f" → antes del {t['fecha_limite']}" if t["fecha_limite"] else ""
            lineas.append(f"  - [{t['prioridad'].upper()}]{fecha}: {t['descripcion']}")
        secciones.append("TAREAS PENDIENTES:\n" + "\n".join(lineas))

    return "\n\n".join(secciones)
