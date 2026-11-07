#!/usr/bin/env bash
# Plan B de Eagle Eye: si el RTMP de DJI Fly no conecta, retransmite un video
# grabado al mismo servidor RTMP (MediaMTX). El resto del pipeline no cambia.
#
# Uso:
#   scripts/replay.sh <video> [rtmp_url] [--once]
#
# Ejemplos:
#   scripts/replay.sh samples/vuelo-cultivo.mp4
#   scripts/replay.sh samples/vuelo.mp4 rtmp://localhost:1935/live/dron --once
#
# Por defecto el video se repite en bucle hasta Ctrl+C.
# RTMP_URL se toma (en este orden) del 2.º argumento, de la variable de entorno,
# del .env de la raíz o del valor por defecto.

set -euo pipefail

DEFAULT_RTMP_URL="rtmp://localhost:1935/live/dron"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

VIDEO=""
RTMP_ARG=""
LOOP=1

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage 0 ;;
    --once) LOOP=0 ;;
    rtmp://*|rtmps://*) RTMP_ARG="$arg" ;;
    -*) echo "Opción desconocida: $arg" >&2; usage 1 ;;
    *)
      if [[ -z "$VIDEO" ]]; then VIDEO="$arg"
      else echo "Argumento de más: $arg" >&2; usage 1
      fi
      ;;
  esac
done

[[ -z "$VIDEO" ]] && { echo "Falta el video." >&2; usage 1; }
[[ -f "$VIDEO" ]] || { echo "No existe el archivo: $VIDEO" >&2; exit 1; }

# RTMP_URL desde .env si no viene por argumento ni por entorno.
if [[ -z "$RTMP_ARG" && -z "${RTMP_URL:-}" && -f "$ROOT_DIR/.env" ]]; then
  ENV_RTMP="$(grep -E '^RTMP_URL=' "$ROOT_DIR/.env" | tail -n1 | cut -d= -f2- | tr -d '"'"'"' ' || true)"
  [[ -n "$ENV_RTMP" ]] && RTMP_URL="$ENV_RTMP"
fi
TARGET="${RTMP_ARG:-${RTMP_URL:-$DEFAULT_RTMP_URL}}"

command -v ffmpeg >/dev/null 2>&1 || {
  echo "ffmpeg no está instalado. En macOS: brew install ffmpeg" >&2
  exit 1
}

# Aviso (no bloqueante) si no hay nada escuchando en el puerto RTMP.
HOSTPORT="${TARGET#rtmp*://}"; HOSTPORT="${HOSTPORT%%/*}"
HOST="${HOSTPORT%%:*}"; PORT="${HOSTPORT##*:}"
[[ "$PORT" == "$HOST" ]] && PORT=1935
if command -v nc >/dev/null 2>&1 && ! nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
  echo "⚠️  No hay nada escuchando en $HOST:$PORT. ¿Está corriendo MediaMTX? (ver ingest/README.md)" >&2
fi

LOOP_ARGS=()
[[ "$LOOP" -eq 1 ]] && LOOP_ARGS=(-stream_loop -1)

echo "▶ Retransmitiendo $VIDEO → $TARGET $([[ $LOOP -eq 1 ]] && echo '(en bucle, Ctrl+C para parar)')"

# -re: lee a velocidad real (como si fuera en vivo).
# H.264 + FLV es lo que espera RTMP. Sin audio: el pipeline no lo usa.
# -g 30: un keyframe por segundo aprox., para que el grabber enganche rápido.
exec ffmpeg -hide_banner -loglevel warning \
  -re ${LOOP_ARGS[@]+"${LOOP_ARGS[@]}"} -i "$VIDEO" \
  -an \
  -c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p -g 30 \
  -f flv "$TARGET"
