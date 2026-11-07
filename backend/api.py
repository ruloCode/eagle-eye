"""API de Eagle Eye (FastAPI, puerto 8000).

Dueño: César. Change de OpenSpec: add-hallazgos-api (capacidad `api-hallazgos`).
Contrato: contracts/api.md y contracts/hallazgo.schema.json.

Correr:
    uv run uvicorn backend.api:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "eagle.db"
FRAMES = DATA / "frames"
ESTADO_JSON = DATA / "estado.json"
SCHEMA_JSON = ROOT / "contracts" / "hallazgo.schema.json"
SCHEMA_SQL = Path(__file__).resolve().parent / "schema.sql"

load_dotenv(ROOT / ".env")


def presupuesto_usd() -> float:
    """PRESUPUESTO_USD del .env, por defecto 2.00."""
    try:
        return float(os.getenv("PRESUPUESTO_USD", "2.00"))
    except ValueError:
        return 2.00


# Campos del contrato en el orden en que se insertan/leen (sin id ni costo_usd).
CAMPOS_HALLAZGO = (
    "hora",
    "imagen",
    "tipo",
    "severidad",
    "personas",
    "pct_estres",
    "descripcion",
    "recomendacion",
)


def conectar() -> sqlite3.Connection:
    """Una conexión por petición; filas accesibles por nombre."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def aplicar_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))


def vuelo_actual(con: sqlite3.Connection) -> int:
    """Devuelve el id del vuelo abierto (fin IS NULL), creando uno si no hay."""
    fila = con.execute(
        "SELECT id FROM vuelos WHERE fin IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if fila is not None:
        return int(fila["id"])
    cur = con.execute(
        "INSERT INTO vuelos (inicio, presupuesto_usd) VALUES (?, ?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), presupuesto_usd()),
    )
    con.commit()
    return int(cur.lastrowid)


def init_db() -> None:
    """Crea data/, aplica el schema y asegura un vuelo abierto."""
    DATA.mkdir(parents=True, exist_ok=True)
    con = conectar()
    try:
        aplicar_schema(con)
        vuelo_actual(con)
    finally:
        con.close()


app = FastAPI(title="Eagle Eye API", version="0.1.0")

# CORS abierto para localhost (el dashboard corre en :5500).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def fila_a_hallazgo(fila: sqlite3.Row) -> dict[str, Any]:
    """Convierte una fila de `hallazgos` a la forma del contrato + id + costo_usd."""
    return {
        "id": int(fila["id"]),
        "hora": fila["hora"],
        "imagen": fila["imagen"],
        "tipo": fila["tipo"],
        "severidad": fila["severidad"],
        "personas": fila["personas"],
        "pct_estres": fila["pct_estres"],
        "descripcion": fila["descripcion"],
        "recomendacion": fila["recomendacion"],
        "costo_usd": fila["costo_usd"],
    }

# TODO(cesar): cargar SCHEMA_JSON una vez y validar con jsonschema (Draft7Validator).  # Hito 2 (T2.1)


@app.post("/hallazgos", status_code=201)
def crear_hallazgo(cuerpo: dict[str, Any]) -> dict[str, int]:
    """Guarda un hallazgo + costo_usd. 422 si no cumple el schema. Responde {"id": ...}."""
    # TODO(cesar): separar costo_usd (number ≥ 0, obligatorio), validar el resto contra el schema,
    #              insertar en `hallazgos` del vuelo actual y devolver {"id": id}.
    raise HTTPException(status_code=501, detail="TODO(cesar): POST /hallazgos")


@app.get("/hallazgos")
def listar_hallazgos(limit: int = 20) -> list[dict[str, Any]]:
    """Lista hallazgos, el más reciente primero, cada uno con `id` y `costo_usd`."""
    limit = max(1, min(limit, 100))
    con = conectar()
    try:
        filas = con.execute(
            "SELECT * FROM hallazgos ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        con.close()
    return [fila_a_hallazgo(f) for f in filas]


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
