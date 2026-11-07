-- Esquema SQLite de Eagle Eye (data/eagle.db).
-- Dueño: César. Change de OpenSpec: add-hallazgos-api (capacidad `api-hallazgos`).
-- Debe ser idempotente (CREATE TABLE IF NOT EXISTS) porque lo aplican api.py y scripts/seed.py.

-- TODO(cesar): tabla `vuelos`
--   id               INTEGER PRIMARY KEY AUTOINCREMENT
--   inicio           TEXT (ISO 8601)
--   fin              TEXT NULL
--   presupuesto_usd  REAL

-- TODO(cesar): tabla `hallazgos` — una columna por campo de contracts/hallazgo.schema.json
--   id             INTEGER PRIMARY KEY AUTOINCREMENT
--   vuelo_id       INTEGER REFERENCES vuelos(id)
--   hora           TEXT     -- HH:MM:SS
--   imagen         TEXT
--   tipo           TEXT     -- CHECK (tipo IN ('cultivo','personas'))
--   severidad      TEXT     -- CHECK (severidad IN ('baja','media','alta'))
--   personas       INTEGER NULL
--   pct_estres     REAL NULL
--   descripcion    TEXT
--   recomendacion  TEXT
--   costo_usd      REAL
--   creado_en      TEXT DEFAULT CURRENT_TIMESTAMP

-- TODO(cesar): índice para GET /hallazgos (más reciente primero): ON hallazgos(id DESC)
