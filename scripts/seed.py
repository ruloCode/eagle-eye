"""Carga contracts/fixtures/hallazgos.sample.json en data/eagle.db.

Dueño: César. Sirve para que el backend y el dashboard trabajen sin el agente.

Uso:
    uv run python scripts/seed.py            # agrega los fixtures a un vuelo nuevo
    uv run python scripts/seed.py --reset    # borra la base antes de cargar
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "contracts" / "fixtures" / "hallazgos.sample.json"
DB_PATH = ROOT / "data" / "eagle.db"
SCHEMA_SQL = ROOT / "backend" / "schema.sql"
SCHEMA_JSON = ROOT / "contracts" / "hallazgo.schema.json"

# Mismos campos del contrato (sin id ni costo_usd), en orden de inserción.
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="borra data/eagle.db antes de cargar")
    args = parser.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.reset and DB_PATH.exists():
        DB_PATH.unlink()

    schema = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    # Del más antiguo al más reciente: el fixture viene del más reciente (id alto) primero.
    fixtures = sorted(fixtures, key=lambda h: h["id"])

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        cur = con.execute(
            "INSERT INTO vuelos (inicio, presupuesto_usd) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), 2.00),
        )
        vuelo_id = int(cur.lastrowid)

        insertados = 0
        for item in fixtures:
            # Validamos el hallazgo (sin id ni costo_usd) contra el contrato.
            cuerpo = {k: v for k, v in item.items() if k not in ("id", "costo_usd")}
            errores = sorted(validator.iter_errors(cuerpo), key=lambda e: e.path)
            if errores:
                raise SystemExit(
                    f"Fixture inv\u00e1lido (id={item.get('id')}): {errores[0].message}"
                )
            valores = [cuerpo[c] for c in CAMPOS_HALLAZGO]
            con.execute(
                "INSERT INTO hallazgos "
                "(vuelo_id, hora, imagen, tipo, severidad, personas, pct_estres, "
                " descripcion, recomendacion, costo_usd) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [vuelo_id, *valores, item["costo_usd"]],
            )
            insertados += 1
        con.commit()
    finally:
        con.close()

    print(f"Cargados {insertados} hallazgos en {DB_PATH} (vuelo {vuelo_id}).")


if __name__ == "__main__":
    main()
