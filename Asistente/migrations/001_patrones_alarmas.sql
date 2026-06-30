-- Migración 001: Tablas de patrones de usuario y recordatorios
-- Ejecutar en pgAdmin contra la base de datos: asistente_db
-- Fecha: 2026-06-30

-- ============================================================
-- TABLA: patrones_usuario
-- Registra correlaciones de comportamiento del usuario.
-- Ejemplo: "después de consultar su peso, siempre pide la playlist del gym"
-- ============================================================
CREATE TABLE IF NOT EXISTS patrones_usuario (
    patron_id          SERIAL PRIMARY KEY,
    usuario_id         INTEGER NOT NULL,
    evento_disparador  VARCHAR(255) NOT NULL,  -- ej: 'CONSULTA_GENERAL', 'MUSICA_LOCAL'
    accion_siguiente   VARCHAR(255) NOT NULL,  -- ej: 'MUSICA_LOCAL', 'WHATSAPP'
    clave_accion       VARCHAR(100) DEFAULT '', -- ej: 'gym', '01'
    conteo             INTEGER NOT NULL DEFAULT 1,
    ultima_vez         TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_patrones_usuario
    ON patrones_usuario(usuario_id, evento_disparador);


-- ============================================================
-- TABLA: recordatorios
-- Alarmas y recordatorios programados por el usuario.
-- Frank los carga al iniciar y los dispara a la hora indicada.
-- ============================================================
CREATE TABLE IF NOT EXISTS recordatorios (
    recordatorio_id  SERIAL PRIMARY KEY,
    usuario_id       INTEGER NOT NULL,
    descripcion      VARCHAR(500) NOT NULL,
    hora_alarma      TIME NOT NULL,             -- formato HH:MM:SS
    dias_semana      VARCHAR(50) DEFAULT 'todos', -- 'todos' | 'lunes,miercoles,viernes'
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en        TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_recordatorios_activos
    ON recordatorios(usuario_id, activo);


-- ============================================================
-- DATOS INICIALES DE EJEMPLO (opcional, comentar si no se necesitan)
-- ============================================================
-- INSERT INTO recordatorios (usuario_id, descripcion, hora_alarma)
-- VALUES (1, 'Levantarse para el gym', '05:20:00');

-- INSERT INTO recordatorios (usuario_id, descripcion, hora_alarma)
-- VALUES (1, 'Tomar agua', '08:00:00');
