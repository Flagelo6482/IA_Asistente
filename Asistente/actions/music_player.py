import os
import random
from config.database import conectar_db
from core.speaker import hablar

def abrir_carpeta_de_musica(clave):
    """Busca la ruta de la música en la base de datos, desordena los MP3 y abre el archivo .m3u8."""
    conn = conectar_db()
    if not conn:
        return "Error de conexión con la base de datos."
        
    try:
        cur = conn.cursor()
        # Buscamos la ruta usando la clave de activación
        cur.execute("SELECT ruta_carpeta FROM biblioteca_musica WHERE clave_activacion = %s", (clave,))
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            ruta = os.path.normpath(resultado[0])
            if not os.path.exists(ruta):
                return f"La carpeta '{ruta}' configurada en pgAdmin no existe física o virtualmente."
                
            hablar(f"Entendido Frank, reproduciendo la lista {clave}.")
            
            # Listamos archivos de música compatibles
            extensiones_musicales = ('.mp3', '.mp4', '.wav', '.flac')
            archivos = [f for f in os.listdir(ruta) if f.lower().endswith(extensiones_musicales)]

            if archivos:
                # Desordenamos la lista de canciones para modo aleatorio
                random.shuffle(archivos)
                
                # Generamos lista de reproducción m3u8
                playlist_path = os.path.join(ruta, "lista_frank.m3u8")
                with open(playlist_path, "w", encoding="utf-8") as f:
                    for cancion in archivos:
                        ruta_completa = os.path.join(ruta, cancion)
                        f.write(ruta_completa + "\n")
                
                # Abrimos la lista con el reproductor predeterminado de Windows
                os.startfile(playlist_path)
                return f"He preparado la lista {clave} con {len(archivos)} canciones de forma aleatoria."
            else:
                return "La carpeta existe, pero no encontré archivos de audio compatibles (.mp3) adentro."
        else:
            return f"No encontré ninguna ruta con la clave '{clave}' en la biblioteca de música de pgAdmin."
            
    except Exception as e:
        return f"Error al procesar la lista de música: {e}"
