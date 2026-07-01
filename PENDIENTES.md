# PENDIENTES AL LLEGAR A LA PC LOCAL

## PASO 1 — Base de datos (pgAdmin)
Ejecutar los SQL en orden en la base de datos `asistente_db`:

- [ ] `Asistente/migrations/001_patrones_alarmas.sql`  
      → Crea tablas: `patrones_usuario`, `recordatorios`

- [ ] `Asistente/migrations/002_memoria_dinamica.sql`  
      → Crea tablas: `memoria_usuario`, `rutinas`, `tareas`

> **Cómo:** pgAdmin → clic derecho en `asistente_db` → Query Tool → abrir archivo → F5

---

## PASO 2 — Instalar nuevas dependencias
Desde la carpeta `Asistente/`:

```bash
.\frank_env\Scripts\activate
pip install -r requirements.txt
```

> Agrega: `langchain-ollama`, `ollama`, `pyautogui`, `edge-tts`, `playsound`

---

## PASO 3 — Elegir la voz de Frank
Ejecutar el probador de voces (doble clic o desde consola):

```
Asistente/scripts/instalar_voces.bat
```

Escucha las 6 voces y anota el ID de la que más te guste.  
Luego agrégala a tu `.env`:

```
FRANK_VOZ=es-PE-AlexNeural
```

---

## PASO 4 — Verificar que Ollama está corriendo
Antes de iniciar Frank, asegúrate de que Ollama esté activo:

```bash
ollama serve
```

> Si ya está corriendo como servicio, no necesitas hacerlo.  
> Para verificar: `ollama list` debe mostrar el modelo `llama3`.

---

## PASO 5 — Probar Frank
```bash
cd Asistente
.\frank_env\Scripts\activate
python main.py
```

Prueba estos comandos para verificar que todo funciona:

- `frank recuerda que me gusta el rock` → debe guardar en BD
- `frank voy al gym los lunes a las 6am` → debe guardar rutina
- `frank tengo que pagar el internet el 15` → debe guardar tarea
- `frank muéstrame mis tareas` → debe listar tareas
- `frank reproduce algo de nirvana` → debe abrir YouTube

---

## NOTAS ADICIONALES

- El `.env` real (con contraseñas) **no está en el repo** — está solo en tu PC local.
  Copia `.env.example` → `.env` y rellena los valores reales.
- `frank_env/` tampoco está en el repo — recrear con `python -m venv frank_env`.
- El archivo `Asistente/archive/prueba_0.py` es el código original. Puedes borrarlo cuando confirmes que `main.py` funciona bien.
