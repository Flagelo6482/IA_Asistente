import urllib.request
import urllib.error
import json

def enviar_comando_mapa(accion, parametros=None):
    """
    Envía un comando en formato JSON al servidor de control de Perú Security Map.
    Usa urllib de la biblioteca estándar para evitar instalar dependencias de red adicionales.
    """
    url = "http://localhost:3000/api/control"
    payload = {
        "command": accion,
        "params": parametros or {}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        # Timeout corto de 2 segundos para no colgar el bucle del asistente si el mapa está cerrado
        with urllib.request.urlopen(req, timeout=2) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            return True, f"Mapa actualizado: {res_json.get('status', 'Orden procesada')}"
    except urllib.error.URLError as e:
        # Se asume que el servidor del mapa no está levantado
        return False, "No se pudo comunicar con el mapa. ¿Está Perú Security Map abierto?"
    except Exception as e:
        return False, f"Error de comunicación con el mapa: {e}"
