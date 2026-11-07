"""Grabber: lee el stream RTMP y guarda 1 frame cada N segundos.

Dueño: César. Change de OpenSpec: add-stream-ingest (capacidad `ingesta-video`).

Contrato (ver contracts/api.md, "Interfaces de archivo"):
- Escribe data/frames/NNNN.jpg (4 dígitos, creciente) con el lado mayor a 1024 px.
- Mantiene data/frames/latest.jpg (escritura atómica: temporal + os.replace).
- Escribe data/estado.json: {"estado_stream": "en_vivo"|"sin_senal", "ultimo_frame_ts": ISO 8601}.
- Si pasan > 10 s sin frames nuevos → "sin_senal".

Uso:
    uv run python ingest/grabber.py                     # RTMP_URL del .env
    uv run python ingest/grabber.py --intervalo 2
    uv run python ingest/grabber.py --url rtmp://localhost:1935/live/dron
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FRAMES = DATA / "frames"
ESTADO = DATA / "estado.json"

LADO_MAYOR_PX = 1024
TIMEOUT_SIN_SENAL_S = 10


def redimensionar(frame, lado_mayor: int = LADO_MAYOR_PX):
    """Devuelve el frame con su lado mayor a `lado_mayor` px, manteniendo proporción."""
    # TODO(cesar): cv2.resize con INTER_AREA si el frame es más grande.
    raise NotImplementedError


def guardar_frame(frame, numero: int) -> Path:
    """Guarda data/frames/NNNN.jpg y actualiza latest.jpg de forma atómica."""
    # TODO(cesar): cv2.imwrite a NNNN.jpg; copiar a latest.tmp.jpg y os.replace → latest.jpg.
    raise NotImplementedError


def escribir_estado(estado_stream: str, ultimo_frame_ts: str | None) -> None:
    """Escribe data/estado.json (atómico)."""
    # TODO(cesar)
    raise NotImplementedError


def siguiente_numero() -> int:
    """Siguiente NNNN a partir de los archivos que ya existen en data/frames/."""
    # TODO(cesar): para no pisar frames si el grabber se reinicia.
    raise NotImplementedError


def loop(url: str, intervalo_s: float) -> None:
    """Bucle principal.

    TODO(cesar):
    - cv2.VideoCapture(url); si no abre o se cae, reintentar cada 2 s sin morir.
    - Leer frames continuamente (para no acumular buffer) y guardar 1 cada `intervalo_s`.
    - Actualizar estado.json en cada iteración: "sin_senal" si han pasado
      > TIMEOUT_SIN_SENAL_S desde el último frame guardado.
    """
    raise NotImplementedError


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Grabber de frames de Eagle Eye")
    parser.add_argument("--url", default=os.getenv("RTMP_URL", "rtmp://localhost:1935/live/dron"))
    parser.add_argument(
        "--intervalo",
        type=float,
        default=float(os.getenv("INTERVALO_GRABBER_S", "4")),
        help="segundos entre frames guardados (por defecto 4)",
    )
    args = parser.parse_args()
    FRAMES.mkdir(parents=True, exist_ok=True)
    loop(args.url, args.intervalo)


if __name__ == "__main__":
    main()
