"""API de Eagle Eye (FastAPI, puerto 8000).

Dueño: César. Change de OpenSpec: add-hallazgos-api (capacidad `api-hallazgos`).
Contrato: contracts/api.md y contracts/hallazgo.schema.json.

Correr:
    uv run uvicorn backend.api:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "eagle.db"
FRAMES = DATA / "frames"
ESTADO_JSON = DATA / "estado.json"
SCHEMA_JSON = ROOT / "contracts" / "hallazgo.schema.json"
SCHEMA_SQL = Path(__file__).resolve().parent / "schema.sql"

app = FastAPI(title="Eagle Eye API", version="0.1.0")

# CORS abierto para localhost (el dashboard corre en :5500).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO(cesar): al arrancar, crear data/ y aplicar schema.sql; abrir o crear el vuelo actual.
# TODO(cesar): cargar SCHEMA_JSON una vez y validar con jsonschema (Draft7Validator).
# TODO(cesar): leer PRESUPUESTO_USD del .env (python-dotenv), por defecto 2.00.


@app.post("/hallazgos", status_code=201)
def crear_hallazgo(cuerpo: dict[str, Any]) -> dict[str, int]:
    """Guarda un hallazgo + costo_usd. 422 si no cumple el schema. Responde {"id": ...}."""
    # TODO(cesar): separar costo_usd (number ≥ 0, obligatorio), validar el resto contra el schema,
    #              insertar en `hallazgos` del vuelo actual y devolver {"id": id}.
    raise HTTPException(status_code=501, detail="TODO(cesar): POST /hallazgos")


@app.get("/hallazgos")
def listar_hallazgos(limit: int = 20) -> list[dict[str, Any]]:
    """Lista hallazgos, el más reciente primero, cada uno con `id` y `costo_usd`."""
    # TODO(cesar): limitar a 1..100; ORDER BY id DESC.
    raise HTTPException(status_code=501, detail="TODO(cesar): GET /hallazgos")


@app.get("/estado")
def estado() -> dict[str, Any]:
    """{estado_stream, frames_analizados, costo_usd, presupuesto_usd, ultimo_frame}."""
    # TODO(cesar): estado_stream desde data/estado.json ("sin_senal" si no existe);
    #              frames_analizados y costo_usd = COUNT/SUM del vuelo actual.
    raise HTTPException(status_code=501, detail="TODO(cesar): GET /estado")


@app.get("/frames/{archivo}")
def frame(archivo: str):
    """Sirve data/frames/{archivo}. 404 si no existe; rechaza rutas con '..' o '/'."""
    # TODO(cesar): FileResponse(FRAMES / archivo, media_type="image/jpeg").
    raise HTTPException(status_code=501, detail="TODO(cesar): GET /frames/{archivo}")
