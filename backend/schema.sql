-- Esquema SQLite de Eagle Eye (data/eagle.db).
-- Dueño: César. Change de OpenSpec: add-hallazgos-api (capacidad `api-hallazgos`).
-- Debe ser idempotente (CREATE TABLE IF NOT EXISTS) porque lo aplican api.py y scripts/seed.py.

CREATE TABLE IF NOT EXISTS vuelos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio           TEXT NOT NULL,            -- ISO 8601
    fin              TEXT,                      -- NULL mientras el vuelo está abierto
    presupuesto_usd  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS hallazgos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    vuelo_id       INTEGER NOT NULL REFERENCES vuelos(id),
    hora           TEXT NOT NULL,              -- HH:MM:SS
    imagen         TEXT NOT NULL,
    tipo           TEXT NOT NULL CHECK (tipo IN ('cultivo', 'personas')),
    severidad      TEXT NOT NULL CHECK (severidad IN ('baja', 'media', 'alta')),
    personas       INTEGER,
    pct_estres     REAL,
    descripcion    TEXT NOT NULL,
    recomendacion  TEXT NOT NULL,
    costo_usd      REAL NOT NULL,
    creado_en      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- GET /hallazgos devuelve el más reciente primero (ORDER BY id DESC).
CREATE INDEX IF NOT EXISTS idx_hallazgos_id_desc ON hallazgos(id DESC);
