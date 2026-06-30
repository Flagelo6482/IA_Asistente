-- Migración 002: Sistema de Memoria Dinámica para Frank
-- Ejecutar en pgAdmin contra la base de datos: asistente_db
-- Fecha: 2026-06-30

-- ============================================================
-- TABLA: memoria_usuario
-- Almacena hechos, preferencias, hábitos y objetivos del usuario.
-- Es el núcleo del sistema de memoria: clave-valor con tipo y relevancia.
-- Frank carga esto en su prompt de sistema en cada sesión.
-- ============================================================
CREATE TABLE IF NOT EXISTS memoria_usuario (
    memoria_id      SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,

    -- Tipo de memoria para clasificar y filtrar
    tipo            VARCHAR(50) NOT NULL,
    -- Valores posibles:
    --   PREFERENCIA  → le gusta/no le gusta algo (música, comida, actividades)
    --   HABITO       → algo que hace regularmente (toma agua, medita, etc.)
    --   OBJETIVO     → meta a largo plazo (bajar de peso, leer más, etc.)
    --   DATO_PERSONAL → datos sobre él (trabaja en X, estudia Y, tiene mascota)
    --   AVERSION     → cosas que no le gustan o le hacen mal
    --   CONTEXTO     → info situacional temporal (está en dieta, tiene examen)

    categoria       VARCHAR(100),              -- ej: musica, comida, ejercicio, trabajo
    clave           VARCHAR(255) NOT NULL,     -- ej: "musica favorita", "hora de dormir"
    valor           TEXT NOT NULL,             -- ej: "rock y metal", "11pm"

    -- Relevancia para decidir qué va primero en el prompt (1=baja, 10=crítica)
    relevancia      SMALLINT NOT NULL DEFAULT 5 CHECK (relevancia BETWEEN 1 AND 10),

    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    -- Evita duplicar la misma clave para el mismo usuario
    UNIQUE (usuario_id, clave)
);

CREATE INDEX IF NOT EXISTS idx_memoria_usuario_activa
    ON memoria_usuario(usuario_id, activo, relevancia DESC);


-- ============================================================
-- TABLA: rutinas
-- Actividades recurrentes con horario fijo.
-- Frank las menciona cuando son relevantes al contexto.
-- ============================================================
CREATE TABLE IF NOT EXISTS rutinas (
    rutina_id       SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,
    nombre          VARCHAR(255) NOT NULL,     -- ej: "gym", "meditación matutina"
    descripcion     TEXT,
    dias_semana     VARCHAR(100) DEFAULT 'todos',
    -- Formato: 'todos' | 'lunes' | 'lunes,miercoles,viernes' | 'fines de semana'
    hora_inicio     TIME,
    hora_fin        TIME,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_rutinas_activas
    ON rutinas(usuario_id, activo);


-- ============================================================
-- TABLA: tareas
-- Pendientes del usuario con fecha límite y prioridad.
-- Frank las menciona cuando son relevantes o están próximas a vencer.
-- ============================================================
CREATE TABLE IF NOT EXISTS tareas (
    tarea_id        SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,
    descripcion     TEXT NOT NULL,
    fecha_limite    DATE,                      -- NULL = sin fecha límite
    prioridad       VARCHAR(20) NOT NULL DEFAULT 'media',
    -- Valores: 'alta' | 'media' | 'baja'
    completada      BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
    completado_en   TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_tareas_pendientes
    ON tareas(usuario_id, completada, fecha_limite ASC NULLS LAST);


-- ============================================================
-- FUNCIÓN: actualizar timestamp automáticamente en memoria_usuario
-- ============================================================
CREATE OR REPLACE FUNCTION actualizar_timestamp_memoria()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_memoria_actualizado ON memoria_usuario;
CREATE TRIGGER trg_memoria_actualizado
    BEFORE UPDATE ON memoria_usuario
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp_memoria();
