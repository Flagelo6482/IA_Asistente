"""
Script para escuchar y elegir la voz de Frank.
Ejecutar: python probar_voces.py

Requiere: pip install edge-tts playsound
"""
import asyncio
import os
import edge_tts

TEXTO_PRUEBA = (
    "Hola, soy Frank, tu asistente virtual personal. "
    "Estoy listo para ayudarte con lo que necesites."
)

VOCES_RECOMENDADAS = [
    ("es-PE-AlexNeural",   "Masculina - Perú (Alex)"),
    ("es-PE-CamilaNeural", "Femenina  - Perú (Camila)"),
    ("es-MX-JorgeNeural",  "Masculina - México (Jorge)"),
    ("es-MX-DaliaNeural",  "Femenina  - México (Dalia)"),
    ("es-ES-AlvaroNeural", "Masculina - España (Álvaro)"),
    ("es-AR-TomasNeural",  "Masculina - Argentina (Tomás)"),
]


async def reproducir_voz(texto: str, voz: str, archivo: str):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(archivo)


def probar(voz_id: str, descripcion: str):
    archivo = f"_prueba_voz_{voz_id}.mp3"
    print(f"\n  Reproduciendo: {descripcion} ({voz_id})")
    asyncio.run(reproducir_voz(TEXTO_PRUEBA, voz_id, archivo))
    os.startfile(archivo)
    input("  [Enter para continuar con la siguiente voz...]")
    try:
        os.remove(archivo)
    except Exception:
        pass


def main():
    print("=" * 55)
    print("  PROBADOR DE VOCES PARA FRANK")
    print("=" * 55)
    print(f'\n  Texto de prueba: "{TEXTO_PRUEBA}"\n')

    for i, (voz_id, descripcion) in enumerate(VOCES_RECOMENDADAS, 1):
        print(f"  [{i}] {descripcion}")

    print("\n  Escucharás cada voz una por una.")
    print("  Anota el número de la que más te guste.\n")
    input("  [Enter para comenzar...]")

    for voz_id, descripcion in VOCES_RECOMENDADAS:
        probar(voz_id, descripcion)

    print("\n" + "=" * 55)
    print("  Voces disponibles:")
    for i, (voz_id, descripcion) in enumerate(VOCES_RECOMENDADAS, 1):
        print(f"  [{i}] {descripcion} → {voz_id}")
    print("\n  Copia el ID de la voz elegida y pégalo en tu .env:")
    print("  FRANK_VOZ=es-PE-AlexNeural")
    print("=" * 55)


if __name__ == "__main__":
    main()
