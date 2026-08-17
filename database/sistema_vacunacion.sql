-- =====================================================
-- Sistema de Vacunación - Script de creación de BD (v2)
-- Motor: SQLite
-- APLICACION pasa a completarse con datos provenientes del CSV del SISA .
-- y se relaciona con LOTE  y con VACUNATORIO por nombre.
-- =====================================================

PRAGMA foreign_keys = ON;

-- =====================================================
-- VACUNATORIO
-- =====================================================
CREATE TABLE VACUNATORIO (
    id_vacunatorio  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,   -- UNIQUE: nombre exacto que viene del CSV del SISA
    direccion       TEXT NOT NULL,
    telefono        TEXT,
    es_central      INTEGER NOT NULL DEFAULT 0 CHECK (es_central IN (0,1))
);

-- =====================================================
-- USUARIO
-- =====================================================
CREATE TABLE USUARIO (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    apellido        TEXT NOT NULL,
    usuario         TEXT NOT NULL UNIQUE,
    contrasena      TEXT NOT NULL,
    id_vacunatorio  INTEGER NOT NULL,
    FOREIGN KEY (id_vacunatorio) REFERENCES VACUNATORIO(id_vacunatorio)
);

-- =====================================================
-- VACUNA (carga dinámica)
-- =====================================================
CREATE TABLE VACUNA (
    id_vacuna           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT NOT NULL UNIQUE,
    fabricante          TEXT,
    dosis_requeridas    INTEGER NOT NULL DEFAULT 1,
    dosis_por_ampolla   INTEGER NOT NULL DEFAULT 1
);

-- =====================================================
-- LOTE
-- =====================================================
CREATE TABLE LOTE (
    id_lote             INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_lote         TEXT NOT NULL,
    fecha_vencimiento   TEXT NOT NULL,   -- YYYY-MM-DD
    cantidad_ampollas   INTEGER NOT NULL,
    id_vacuna           INTEGER NOT NULL,
    id_vacunatorio      INTEGER NOT NULL,
    FOREIGN KEY (id_vacuna) REFERENCES VACUNA(id_vacuna),
    FOREIGN KEY (id_vacunatorio) REFERENCES VACUNATORIO(id_vacunatorio)
);

-- =====================================================
-- AMPOLLA
-- =====================================================
CREATE TABLE AMPOLLA (
    id_ampolla              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_apertura          TEXT,        -- YYYY-MM-DD HH:MM:SS
    dosis_disponibles       INTEGER NOT NULL,
    id_lote                 INTEGER NOT NULL,
    id_vacunatorio_actual   INTEGER NOT NULL,
    FOREIGN KEY (id_lote) REFERENCES LOTE(id_lote),
    FOREIGN KEY (id_vacunatorio_actual) REFERENCES VACUNATORIO(id_vacunatorio)
);

-- =====================================================
-- TRANSFERENCIA
-- =====================================================
CREATE TABLE TRANSFERENCIA (
    id_transferencia        INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_remito            TEXT NOT NULL UNIQUE,
    fecha                    TEXT NOT NULL,  -- YYYY-MM-DD HH:MM:SS
    id_vacunatorio_origen    INTEGER NOT NULL,
    id_vacunatorio_destino   INTEGER NOT NULL,
    id_usuario               INTEGER NOT NULL,
    observaciones            TEXT,
    FOREIGN KEY (id_vacunatorio_origen) REFERENCES VACUNATORIO(id_vacunatorio),
    FOREIGN KEY (id_vacunatorio_destino) REFERENCES VACUNATORIO(id_vacunatorio),
    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),
    CHECK (id_vacunatorio_origen <> id_vacunatorio_destino)
);

-- =====================================================
-- TRANSFERENCIA_DETALLE (PK compuesta)
-- =====================================================
CREATE TABLE TRANSFERENCIA_DETALLE (
    id_transferencia    INTEGER NOT NULL,
    id_ampolla          INTEGER NOT NULL,
    PRIMARY KEY (id_transferencia, id_ampolla),
    FOREIGN KEY (id_transferencia) REFERENCES TRANSFERENCIA(id_transferencia),
    FOREIGN KEY (id_ampolla) REFERENCES AMPOLLA(id_ampolla)
);

-- =====================================================
-- APLICACION
-- se completa por importación del CSV del Registro Federal de
-- Vacunación Nominalizado (SISA). id_lote puede quedar NULL
-- si el número de lote del CSV no coincide con ningún LOTE
-- cargado en el sistema.
-- =====================================================
CREATE TABLE APLICACION (
    id_aplicacion       INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_aplicacion    TEXT NOT NULL,   -- YYYY-MM-DD
    vacuna_nombre       TEXT NOT NULL,   -- tal cual viene del CSV
    esquema             TEXT,
    dosis               TEXT,            -- "1er Dosis", "Refuerzo", "Unica Dosis", etc.
    paciente_nombre     TEXT,
    sexo                TEXT,
    dni                 TEXT,
    id_vacunatorio      INTEGER NOT NULL,
    region_sanitaria    TEXT,
    departamento        TEXT,
    id_lote             INTEGER,         -- NULL si el número de lote del CSV no coincide con ningún LOTE cargado en el sistema
    tipo_edad           TEXT,
    edad                INTEGER,
    fecha_registro      TEXT,
    excepcion           TEXT,
    usuario_sisa        TEXT,            -- "Cuenta del usuario" del CSV (dato externo)
    FOREIGN KEY (id_vacunatorio) REFERENCES VACUNATORIO(id_vacunatorio),
    FOREIGN KEY (id_lote) REFERENCES LOTE(id_lote)
);

-- =====================================================
-- Índices  para consultas frecuentes
-- =====================================================
CREATE INDEX idx_lote_vacuna ON LOTE(id_vacuna);
CREATE INDEX idx_ampolla_vacunatorio ON AMPOLLA(id_vacunatorio_actual);
CREATE INDEX idx_aplicacion_vacunatorio ON APLICACION(id_vacunatorio);
CREATE INDEX idx_aplicacion_lote ON APLICACION(id_lote);
CREATE INDEX idx_aplicacion_fecha ON APLICACION(fecha_aplicacion);