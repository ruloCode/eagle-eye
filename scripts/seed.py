"""Carga contracts/fixtures/hallazgos.sample.json en data/eagle.db.

Dueño: César. Sirve para que el backend y el dashboard trabajen sin el agente.

Uso:
    uv run python scripts/seed.py            # agrega los fixtures a un vuelo nuevo
    uv run python scripts/seed.py --reset    # borra la base antes de cargar
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "contracts" / "fixtures" / "hallazgos.sample.json"
DB_PATH = ROOT / "data" / "eagle.db"
SCHEMA_SQL = ROOT / "backend" / "schema.sql"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="borra data/eagle.db antes de cargar")
    args = parser.parse_args()

    # TODO(cesar): crear data/ si no existe; si --reset, borrar DB_PATH.
    # TODO(cesar): aplicar SCHEMA_SQL (idempotente: CREATE TABLE IF NOT EXISTS).
    # TODO(cesar): crear un registro en `vuelos` y cargar FIXTURES ignorando el `id`,
    #              insertando del más antiguo al más reciente para que GET /hallazgos
    #              los devuelva en el mismo orden que el fixture.
    # TODO(cesar): validar cada hallazgo contra contracts/hallazgo.schema.json antes de insertar.
    raise NotImplementedError("TODO(cesar): implementar seed")


if __name__ == "__main__":
    main()
