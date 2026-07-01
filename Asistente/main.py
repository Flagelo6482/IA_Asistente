"""
Frank - Asistente Virtual Personal
Uso:
    python main.py               (modo texto, por defecto)
    python main.py --modo voz    (modo micrófono)
    python main.py --modo texto  (modo consola explícito)
"""
import argparse
import logging
import os
import sys

from acciones import (
    abrir_web,
    agregar_alarma,
    cargar_alarmas_desde_db,
    ejecutar_alarmas_pendientes,
    ejecutar_aplicacion,
    escuchar,
    hablar,
    reproducir_en_youtube,
    reproducir_musica_local,
    enviar_whatsapp,
)
from config import PALABRA_ACTIVACION
from db import (
    guardar_historial,
    guardar_memoria,
    guardar_tarea,
    guardar_rutina,
    desactivar_memoria,
    obtener_tareas_pendientes,
    obtener_usuario,
)
from ia import (
    detectar_intencion,
    extraer_clave_musica,
    extraer_clave_a_olvidar,
    extraer_datos_alarma,
    extraer_datos_whatsapp,
    extraer_memoria,
    extraer_rutina,
    extraer_tarea,
    limpiar_historial,
    obtener_respuesta,
)

# ============================================ #
# LOGGING                                      #
# ============================================ #

def configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("frank.log", encoding="utf-8"),
        ],
    )

log = logging.getLogger("main")


# ============================================ #
# PROTOCOLOS / MACROS                          #
# ============================================ #

def cargar_protocolos(ruta: str = "protocolos.txt") -> dict[str, str]:
    """Lee protocolos.txt y devuelve {codigo: accion}."""
    protocolos: dict[str, str] = {}
    if not os.path.exists(ruta):
        return protocolos
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = [p.strip() for p in linea.split("|")]
            if len(partes) >= 3:
                protocolos[partes[0].lower()] = partes[2]
    return protocolos


# ============================================ #
# ENRUTADOR DE INTENCIONES                     #
# ============================================ #

def procesar_comando(comando: str, protocolos: dict[str, str]) -> str:
    # 1. Verificar protocolos primero (sin pasar por el LLM = respuesta instantánea)
    for codigo, accion in protocolos.items():
        if codigo in comando:
            log.info("Protocolo activado: '%s' → '%s'", codigo, accion)
            hablar(f"Protocolo {codigo} activado.")
            return procesar_comando(accion, {})

    # 2. Verificar comandos del mapa (Integración con peru-security-map)
    if "mapa" in comando or "llévame a" in comando or "limpia el mapa" in comando:
        try:
            from actions.map_controller import enviar_comando_mapa
            log.info("Comando de mapa detectado: '%s'", comando)
            if "limpia" in comando:
                exito, resultado = enviar_comando_mapa("reset")
                guardar_historial(comando, resultado, "MAPA")
                return resultado
            elif "llévame a" in comando:
                lugar = comando.replace("llévame a", "").replace("el distrito de", "").replace("distrito de", "").strip()
                exito, resultado = enviar_comando_mapa("navigate_to", {"target": lugar, "scope": "dist"})
                guardar_historial(comando, resultado, "MAPA")
                return resultado
            elif "muestra" in comando:
                if "comisaría" in comando or "comisarias" in comando or "policía" in comando:
                    poi = "police"
                elif "colegio" in comando or "escuela" in comando:
                    poi = "school"
                elif "hospital" in comando or "clínica" in comando or "salud" in comando:
                    poi = "hospital"
                else:
                    poi = "all"
                exito, resultado = enviar_comando_mapa("show_poi", {"poi": poi})
                guardar_historial(comando, resultado, "MAPA")
                return resultado
        except Exception as e:
            log.error("Error en modulo de mapa: %s", e)

    # 3. Clasificar intención con el LLM
    intencion = detectar_intencion(comando)
    log.info("Intención detectada: %s | Comando: %s", intencion, comando)

    if intencion == "WHATSAPP":
        contacto, mensaje = extraer_datos_whatsapp(comando)
        if contacto and mensaje:
            resultado = enviar_whatsapp(contacto, mensaje)
        else:
            resultado = "No pude extraer el contacto o el mensaje. Intenta de nuevo."
        guardar_historial(comando, resultado, "WHATSAPP")
        return resultado

    if intencion == "MUSICA_LOCAL":
        clave = extraer_clave_musica(comando)
        log.info("Clave de música extraída: '%s'", clave)
        resultado = reproducir_musica_local(clave)
        guardar_historial(comando, resultado, "MUSICA_LOCAL")
        return resultado

    if intencion == "MUSICA_YOUTUBE":
        busqueda = (
            comando.replace("reproduce", "")
                   .replace("pon la musica de", "")
                   .replace("pon", "")
                   .strip()
        )
        resultado = reproducir_en_youtube(busqueda)
        guardar_historial(comando, resultado, "MUSICA_YOUTUBE")
        return resultado

    if intencion == "ALARMA":
        hora, descripcion = extraer_datos_alarma(comando)
        if hora and descripcion:
            resultado = agregar_alarma(descripcion, hora)
        else:
            resultado = "No pude entender la hora o la descripción del recordatorio."
        guardar_historial(comando, resultado, "ALARMA")
        return resultado

    if intencion == "GUARDAR_MEMORIA":
        tipo, categoria, clave, valor, relevancia = extraer_memoria(comando)
        ok = guardar_memoria(tipo, clave, valor, categoria, relevancia)
        resultado = (
            f"Entendido, lo recordaré: {clave} → {valor}."
            if ok else "No pude guardar ese dato, hubo un problema."
        )
        guardar_historial(comando, resultado, "GUARDAR_MEMORIA")
        return resultado

    if intencion == "GUARDAR_TAREA":
        descripcion, fecha, prioridad = extraer_tarea(comando)
        tarea_id = guardar_tarea(descripcion, fecha, prioridad)
        fecha_str = f" para el {fecha}" if fecha else ""
        resultado = (
            f"Tarea guardada [{prioridad}]{fecha_str}: {descripcion}."
            if tarea_id else "No pude guardar la tarea."
        )
        guardar_historial(comando, resultado, "GUARDAR_TAREA")
        return resultado

    if intencion == "GUARDAR_RUTINA":
        nombre, dias, hora, descripcion = extraer_rutina(comando)
        ok = guardar_rutina(nombre, descripcion or "", dias, hora)
        resultado = (
            f"Rutina '{nombre}' guardada: {dias}"
            + (f" a las {hora}." if hora else ".")
            if ok else "No pude guardar la rutina."
        )
        guardar_historial(comando, resultado, "GUARDAR_RUTINA")
        return resultado

    if intencion == "OLVIDAR":
        clave = extraer_clave_a_olvidar(comando)
        if clave:
            ok = desactivar_memoria(clave)
            resultado = f"Olvidado: '{clave}'." if ok else f"No encontré el dato '{clave}' para olvidarlo."
        else:
            resultado = "No entendí qué quieres que olvide."
        guardar_historial(comando, resultado, "OLVIDAR")
        return resultado

    if intencion == "VER_TAREAS":
        tareas = obtener_tareas_pendientes()
        if not tareas:
            resultado = "No tienes tareas pendientes."
        else:
            lineas = []
            for t in tareas:
                fecha = f" → {t['fecha_limite']}" if t["fecha_limite"] else ""
                lineas.append(f"[{t['prioridad'].upper()}]{fecha}: {t['descripcion']}")
            resultado = "Tus tareas pendientes:\n" + "\n".join(lineas)
        guardar_historial(comando, resultado, "VER_TAREAS")
        return resultado

    if intencion == "WEB":
        url = obtener_respuesta(
            f"El usuario dijo: '{comando}'. Extrae la URL completa. "
            "Responde SOLO con la URL, sin texto adicional."
        )
        resultado = abrir_web(url.strip())
        guardar_historial(comando, resultado, "WEB")
        return resultado

    if intencion == "APP":
        resultado = ejecutar_aplicacion(comando)
        guardar_historial(comando, resultado, "APP")
        return resultado

    # CONVERSACION (y cualquier fallback)
    print("Frank: Pensando...", end="\r", flush=True)
    respuesta = obtener_respuesta(comando)
    print(" " * 20, end="\r", flush=True)
    guardar_historial(comando, respuesta, intencion)
    return respuesta


# ============================================ #
# BUCLE PRINCIPAL                              #
# ============================================ #

def main():
    configurar_logging()

    parser = argparse.ArgumentParser(description="Asistente Frank")
    parser.add_argument(
        "--modo",
        choices=["voz", "texto"],
        default="texto",
        help="Modo de entrada: 'voz' (micrófono) o 'texto' (consola). Default: texto",
    )
    args = parser.parse_args()

    log.info("Sistema Frank iniciando en modo: %s", args.modo)

    nombre_usuario, _ = obtener_usuario()
    protocolos = cargar_protocolos()
    cargar_alarmas_desde_db()

    hablar(f"Sistema Frank iniciado. Hola, {nombre_usuario}.")
    print(f"\n--- Frank activo para {nombre_usuario} | modo: {args.modo} ---")
    print(f"Palabra de activación: '{PALABRA_ACTIVACION}'")
    print("Escribe 'salir' o di 'adiós frank' para terminar.")
    if protocolos:
        print(f"Protocolos cargados: {list(protocolos.keys())}\n")

    while True:
        ejecutar_alarmas_pendientes()

        try:
            if args.modo == "voz":
                frase = escuchar()
            else:
                frase = input("\n[Tú]: ").lower().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not frase:
            continue

        if frase in ("salir",) or "adios frank" in frase or "adiós frank" in frase:
            hablar("Guardando sesión. Hasta pronto.")
            log.info("Sesión terminada por el usuario.")
            break

        if "limpiar historial" in frase:
            limpiar_historial()
            hablar("Historial de conversación limpiado.")
            continue

        if PALABRA_ACTIVACION in frase:
            comando = frase.replace(PALABRA_ACTIVACION, "").strip()
            if not comando:
                print("Frank: ¿Sí? Estoy escuchando.")
                continue
            
            # Detener el habla anterior si está reproduciendo voz de fondo (para edge-tts/pyttsx3)
            try:
                from acciones import detener_habla
                detener_habla()
            except ImportError:
                pass

            respuesta = procesar_comando(comando, protocolos)
            hablar(respuesta)
        else:
            log.debug("Frase sin palabra de activación ignorada: %s", frase)


if __name__ == "__main__":
    main()
