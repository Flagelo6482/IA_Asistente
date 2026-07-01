import psycopg2
import os
from dotenv import load_dotenv

# Cargar configuración del .env
load_dotenv()

def conectar_db():
    """Establece conexión con la base de datos PostgreSQL local."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            client_encoding='utf8'
        )
        return conn
    except Exception as e:
        print(f"Error conectando a pgAdmin: {e}")
        return None

def obtener_nombre_usuario(usuario_id=1):
    """Obtiene el nombre del usuario desde la base de datos."""
    conn = conectar_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM usuarios WHERE usuario_id = %s", (usuario_id,))
            resultado = cur.fetchone()
            cur.close()
            conn.close()
            return resultado[0] if resultado else "Usuario"
        except Exception as e:
            print(f"Error al obtener nombre de usuario: {e}")
            if conn: conn.close()
    return "Usuario"

def guardar_en_historial_completo(comando, respuesta, intencion='CONSULTA_GENERAL'):
    """Guarda la interacción en el historial de base de datos, mapeando la intención a llaves válidas."""
    # Mapa de normalización para asegurar conformidad con la clave foránea en cat_intenciones
    mapa_intenciones = {
        'WHATSAPP_AUTOMATION': 'WHATSAPP_SEND',
        'WHATSAPP_SEND': 'WHATSAPP_SEND',
        'LOCAL_MUSIC': 'MUSICA_PEDIDO',
        'YOUTUBE_MUSIC': 'MUSICA_PEDIDO',
        'MUSICA_PEDIDO': 'MUSICA_PEDIDO',
        'DIETA_CONSULTA': 'DIETA_CONSULTA',
        'DIETA_LOG': 'DIETA_LOG',
        'ANIMO_NEGATIVO': 'ANIMO_NEGATIVO',
        'ARC_FACIAL_CONTROL': 'ARC_FACIAL_CONTROL',
        'CONSULTA_GENERAL': 'CONSULTA_GENERAL',
        'OLLAMA_LOCAL': 'CONSULTA_GENERAL',
        'GEMINI_CLOUD': 'CONSULTA_GENERAL',
        'OLLAMA_LOCAL_FALLBACK': 'CONSULTA_GENERAL',
    }
    
    intencion_valida = mapa_intenciones.get(intencion, 'CONSULTA_GENERAL')
    
    conn = conectar_db()
    if conn:
        try:
            cur = conn.cursor()
            query = """
                INSERT INTO historial_interacciones 
                (usuario_id, dispositivo_id, comando_original, respuesta_frank, intencion_detectada) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(query, (1, 1, comando, respuesta, intencion_valida))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error al guardar historial: {e}")
            if conn: conn.close()
