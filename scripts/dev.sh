#!/usr/bin/env bash
# Levanta la API (FastAPI, :8000) y sirve el dashboard estático (:5500).
# El dashboard se sirve desde la raíz del repo para que ?mock=1 pueda leer
# contracts/fixtures/*.json.
#
# Uso: scripts/dev.sh            → API + dashboard
#      scripts/dev.sh --solo-web → solo dashboard (no necesita uv ni Python deps)
#
# Dashboard: http://localhost:5500/dashboard/        (API real)
#            http://localhost:5500/dashboard/?mock=1 (fixtures)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5500}"

PIDS=()
cleanup() {
  for pid in ${PIDS[@]+"${PIDS[@]}"}; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

mkdir -p data/frames

if [[ "${1:-}" != "--solo-web" ]]; then
  command -v uv >/dev/null 2>&1 || {
    echo "uv no está instalado: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo "(o usa scripts/dev.sh --solo-web para servir solo el dashboard)" >&2
    exit 1
  }
  echo "▶ API       → http://localhost:$API_PORT"
  uv run uvicorn backend.api:app --reload --port "$API_PORT" &
  PIDS+=($!)
fi

echo "▶ Dashboard → http://localhost:$WEB_PORT/dashboard/  (mock: ?mock=1)"
python3 -m http.server "$WEB_PORT" --bind 127.0.0.1 &
PIDS+=($!)

wait
