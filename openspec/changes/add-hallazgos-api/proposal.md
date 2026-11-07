# Proposal

## Why

El agente produce hallazgos y el dashboard los muestra, pero ninguno de los dos debe conocer al otro. Una API pequeña con SQLite desacopla los frentes, valida que todo lo guardado cumpla el contrato y lleva la cuenta del gasto para el control de presupuesto.

## What Changes

- Base SQLite `data/eagle.db` con tablas `hallazgos` y `vuelos`.
- FastAPI en `:8000` con los 4 endpoints de `contracts/api.md`: `POST /hallazgos`, `GET /hallazgos`, `GET /estado`, `GET /frames/{archivo}`.
- Validación del cuerpo contra `contracts/hallazgo.schema.json`; rechazo con 422.
- Suma de `costo_usd` del vuelo actual en `GET /estado`.
- CORS abierto para `localhost`.
- `scripts/seed.py` que carga los fixtures en SQLite para trabajar sin el agente.

## Capabilities

### New Capabilities
- `api-hallazgos`: persistencia y exposición HTTP de hallazgos, estado del vuelo, gasto acumulado e imágenes de los frames.

### Modified Capabilities

## Impact

- Carpetas de César: `backend/` (`schema.sql`, `api.py`) y `scripts/seed.py`.
- Consumidores: el agente (`POST`) y el dashboard (`GET`).
- Lee `data/estado.json` y `data/frames/` del grabber.
- Dependencias: `fastapi`, `uvicorn`, `jsonschema`, `python-dotenv`.
