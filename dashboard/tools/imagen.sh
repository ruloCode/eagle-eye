#!/usr/bin/env bash
# Genera una imagen gratis con Cloudflare Workers AI (FLUX.1 schnell) para el look and feel.
# Dueña: Daniela. Necesita CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_API_TOKEN en el .env de la raíz.
#
# Uso:
#   dashboard/tools/imagen.sh "<prompt en inglés>" <nombre> [--169] [--steps N]
# Ejemplos:
#   dashboard/tools/imagen.sh "aerial drone view of crop fields at night, dark teal, cinematic" fondo --169
#   dashboard/tools/imagen.sh "minimal eagle head emblem, flat, teal on black" logo-idea
#
# Guarda en dashboard/assets/<nombre>.jpg. --169 recorta al centro a 16:9 (para fondos).
# Gratis: 10.000 neurons/día ≈ 230 imágenes con steps=4 (máx. 8 = más calidad, ≈120/día).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$ROOT/dashboard/assets"

PROMPT="${1:-}"; NOMBRE="${2:-}"; shift 2 2>/dev/null || true
RECORTE=0; STEPS=4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --169) RECORTE=1 ;;
    --steps) STEPS="$2"; shift ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
  shift
done
[[ -z "$PROMPT" || -z "$NOMBRE" ]] && { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

# Credenciales desde .env (sin imprimirlas nunca).
if [[ -f "$ROOT/.env" ]]; then
  set -a; source <(grep -E '^CLOUDFLARE_(ACCOUNT_ID|API_TOKEN)=' "$ROOT/.env"); set +a
fi
: "${CLOUDFLARE_ACCOUNT_ID:?Falta CLOUDFLARE_ACCOUNT_ID en .env}"
: "${CLOUDFLARE_API_TOKEN:?Falta CLOUDFLARE_API_TOKEN en .env}"

mkdir -p "$OUT_DIR"
SALIDA="$OUT_DIR/$NOMBRE.jpg"
BODY="$(python3 -c 'import json,sys; print(json.dumps({"prompt": sys.argv[1], "steps": int(sys.argv[2])}))' "$PROMPT" "$STEPS")"

echo "🎨 Generando: $NOMBRE (steps=$STEPS)…"
RESP="$(curl -sS https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/black-forest-labs/flux-1-schnell \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" -d "$BODY")"

printf '%s' "$RESP" | python3 -c '
import base64, json, sys
r = json.load(sys.stdin)
img = (r.get("result") or {}).get("image") or r.get("image")
if not img:
    print("❌ Cloudflare respondió sin imagen:", json.dumps(r.get("errors") or r)[:400], file=sys.stderr); sys.exit(1)
if img.startswith("data:"): img = img.split(",", 1)[1]
open(sys.argv[1], "wb").write(base64.b64decode(img))
' "$SALIDA"
if [[ "$RECORTE" -eq 1 ]]; then
  W=$(sips -g pixelWidth "$SALIDA" | awk '/pixelWidth/{print $2}')
  sips --cropToHeightWidth $((W * 9 / 16)) "$W" "$SALIDA" >/dev/null
fi
echo "✅ $SALIDA ($(sips -g pixelWidth -g pixelHeight "$SALIDA" | awk '/pixel/{printf "%s ", $2}')px)"
