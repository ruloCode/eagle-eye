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
from fastapi.responses import FileResponse
from jsonschema import Draft7Validator

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

# Validador del contrato cargado una vez (Draft7Validator sobre el archivo compartido).
_SCHEMA = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
VALIDADOR = Draft7Validator(_SCHEMA)


@app.post("/hallazgos", status_code=201)
def crear_hallazgo(cuerpo: dict[str, Any]) -> dict[str, int]:
    """Guarda un hallazgo + costo_usd. 422 si no cumple el schema. Responde {"id": ...}."""
    if not isinstance(cuerpo, dict):
        raise HTTPException(status_code=422, detail="El cuerpo debe ser un objeto JSON.")

    # costo_usd es obligatorio y va aparte: el schema tiene additionalProperties: false.
    if "costo_usd" not in cuerpo:
        raise HTTPException(status_code=422, detail="Falta costo_usd.")
    costo_usd = cuerpo["costo_usd"]
    if isinstance(costo_usd, bool) or not isinstance(costo_usd, (int, float)) or costo_usd < 0:
        raise HTTPException(status_code=422, detail="costo_usd debe ser un number ≥ 0.")

    hallazgo = {k: v for k, v in cuerpo.items() if k != "costo_usd"}
    errores = sorted(VALIDADOR.iter_errors(hallazgo), key=lambda e: list(e.path))
    if errores:
        raise HTTPException(status_code=422, detail=errores[0].message)

    con = conectar()
    try:
        vuelo_id = vuelo_actual(con)
        valores = [hallazgo[c] for c in CAMPOS_HALLAZGO]
        cur = con.execute(
            "INSERT INTO hallazgos "
            "(vuelo_id, hora, imagen, tipo, severidad, personas, pct_estres, "
            " descripcion, recomendacion, costo_usd) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [vuelo_id, *valores, costo_usd],
        )
        con.commit()
        return {"id": int(cur.lastrowid)}
    finally:
        con.close()


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
    # estado_stream desde data/estado.json; si no existe o no se puede leer -> sin_senal.
    estado_stream = "sin_senal"
    if ESTADO_JSON.exists():
        try:
            datos = json.loads(ESTADO_JSON.read_text(encoding="utf-8"))
            if datos.get("estado_stream") == "en_vivo":
                estado_stream = "en_vivo"
        except (json.JSONDecodeError, OSError):
            estado_stream = "sin_senal"

    con = conectar()
    try:
        vuelo_id = vuelo_actual(con)
        fila = con.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(costo_usd), 0) AS total "
            "FROM hallazgos WHERE vuelo_id = ?",
            (vuelo_id,),
        ).fetchone()
        ultima = con.execute(
            "SELECT imagen FROM hallazgos WHERE vuelo_id = ? ORDER BY id DESC LIMIT 1",
            (vuelo_id,),
        ).fetchone()
    finally:
        con.close()

    return {
        "estado_stream": estado_stream,
        "frames_analizados": int(fila["n"]),
        "costo_usd": round(float(fila["total"]), 4),
        "presupuesto_usd": presupuesto_usd(),
        "ultimo_frame": ultima["imagen"] if ultima is not None else None,
    }


@app.get("/frames/{archivo}")
def frame(archivo: str):
    """Sirve data/frames/{archivo}. 404 si no existe; rechaza rutas con '..' o '/'."""
    # Rechazar cualquier intento de salir de data/frames/ ('..', '/', separadores).
    if archivo != Path(archivo).name or ".." in archivo or not archivo:
        raise HTTPException(status_code=404, detail="No encontrado.")
    destino = (FRAMES / archivo).resolve()
    try:
        destino.relative_to(FRAMES.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="No encontrado.")
    if not destino.is_file():
        raise HTTPException(status_code=404, detail="No encontrado.")
    return FileResponse(destino, media_type="image/jpeg")
