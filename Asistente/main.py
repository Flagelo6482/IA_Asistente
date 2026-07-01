import sys
from config.database import obtener_nombre_usuario, guardar_en_historial_completo
from core.speaker import hablar, detener_habla
from core.listener import escuchar_frank
from core.brain import procesar_con_ia, extraer_clave_de_musica
from actions.automation import abrir_web, ejecutar_aplicacion, reproducir_en_youtube, enviar_whatsapp_contacto, procesar_comando_whatsapp
from actions.music_player import abrir_carpeta_de_musica
from actions.map_controller import enviar_comando_mapa

def main():
    # Obtener el nombre del usuario desde la base de datos
    nombre_usuario = obtener_nombre_usuario(usuario_id=1)
    
    print(f"\n--- Sistema Frank iniciado para {nombre_usuario} ---")
    print("Escribe/di 'salir' o 'adiós frank' para terminar la sesión.")
    print("Puedes presionar Ctrl+C en cualquier momento para abortar.")
    
    # Hablar saludo inicial si se desea
    # hablar(f"Sistema en línea. Hola {nombre_usuario}, ¿en qué puedo ayudarte hoy?")

    # Flag para controlar si se prefiere Gemini (online) u Ollama (offline)
    # Por defecto, preferiremos Ollama local para mantener todo offline si el usuario lo desea.
    preferir_offline = True

    while True:
        try:
            # Entrada híbrida (puedes cambiar a 'escuchar_frank()' para usar voz por micrófono)
            # frase = escuchar_frank()
            frase = input("\n[Tú]: ").lower().strip()
            
            if not frase:
                continue
            
            if frase == "salir" or "adiós frank" in frase or "adios frank" in frase:
                print("Entendido. Guardando sesión en base de datos y cerrando. Hasta pronto.")
                break
            
            if "frank" in frase:
                # Interrumpir el habla de Frank inmediatamente al recibir un nuevo comando
                detener_habla()
                
                # Limpiar comando quitando la palabra clave
                comando = frase.replace("frank", "").strip()
                
                if not comando:
                    print("Frank: ¿Sí? Estoy escuchando.")
                    continue
                
                # Comando de interrupción manual de voz
                if "cállate" in comando or "callate" in comando or "silencio" in comando:
                    print("Frank: (Silenciado)")
                    continue
                
                # ================================================ #
                # 1. DETECCIÓN DE COMANDOS DEL MAPA (INTEGRACIÓN)
                # ================================================ #
                if "mapa" in comando or "llévame a" in comando or "limpia el mapa" in comando:
                    if "limpia" in comando:
                        exito, resultado = enviar_comando_mapa("reset")
                        hablar(resultado)
                    elif "llévame a" in comando:
                        # Extraer distrito (ejemplo: 'llévame a ate' -> 'ate')
                        lugar = comando.replace("llévame a", "").replace("el distrito de", "").replace("distrito de", "").strip()
                        exito, resultado = enviar_comando_mapa("navigate_to", {"target": lugar, "scope": "dist"})
                        hablar(resultado)
                    elif "muestra" in comando:
                        # Extraer puntos de interés
                        if "comisaría" in comando or "comisarias" in comando or "policía" in comando:
                            poi = "police"
                        elif "colegio" in comando or "escuela" in comando:
                            poi = "school"
                        elif "hospital" in comando or "clínica" in comando or "salud" in comando:
                            poi = "hospital"
                        else:
                            poi = "all"
                        exito, resultado = enviar_comando_mapa("show_poi", {"poi": poi})
                        hablar(resultado)
                
                # ================================================ #
                # 2. DETECCIÓN DE INTENCIÓN DE WHATSAPP
                # ================================================ #
                elif "whatsapp" in comando or "mensaje" in comando or "escríbele a" in comando:
                    contacto, mensaje_extraido = procesar_comando_whatsapp(comando)
                    if contacto and mensaje_extraido:
                        resultado = enviar_whatsapp_contacto(contacto, mensaje_extraido)
                        hablar(resultado)
                        guardar_en_historial_completo(comando, resultado, 'WHATSAPP_AUTOMATION')
                    else:
                        hablar("No pude extraer el contacto o el mensaje a enviar, Frank.")
                
                # ================================================ #
                # 3. DETECCIÓN PARA REPRODUCIR MÚSICA LOCAL
                # ================================================ #
                elif "reproduce la lista" in comando or "pon la lista" in comando:
                    clave_limpia = extraer_clave_de_musica(comando)
                    print(f"Clave de lista detectada: {clave_limpia}")
                    resultado = abrir_carpeta_de_musica(clave_limpia)
                    hablar(resultado)
                    guardar_en_historial_completo(comando, resultado, 'LOCAL_MUSIC')
                
                # ================================================ #
                # 4. DETECCIÓN PARA REPRODUCIR MÚSICA EN YOUTUBE
                # ================================================ #
                elif "reproduce" in comando or "pon la musica de" in comando or "pon la música de" in comando:
                    musica = comando.replace("reproduce", "").replace("pon la musica de", "").replace("pon la música de", "").strip()
                    print(f"Frank: Buscando '{musica}' en Youtube...")
                    resultado = reproducir_en_youtube(musica)
                    hablar(resultado)
                    guardar_en_historial_completo(comando, resultado, 'YOUTUBE_MUSIC')
                
                else:
                    # Mensaje de retroalimentación visual para que el usuario sepa que está pensando y cargando el modelo en la GPU
                    print("Frank: Pensando...", end="\r", flush=True)
                    
                    # Enviar a procesamiento con IA híbrido
                    respuesta, motor_usado = procesar_con_ia(comando, preferir_offline=preferir_offline)
                    
                    # Limpiar el mensaje de pensando de la consola
                    print(" " * 20, end="\r", flush=True)
                    
                    hablar(respuesta)
                    guardar_en_historial_completo(comando, respuesta, motor_usado)
            
        except KeyboardInterrupt:
            print("\nAborting...")
            sys.exit(0)

if __name__ == "__main__":
    main()
