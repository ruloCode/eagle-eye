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
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FRAMES = DATA / "frames"
ESTADO = DATA / "estado.json"
LATEST = FRAMES / "latest.jpg"

LADO_MAYOR_PX = 1024
TIMEOUT_SIN_SENAL_S = 10
REINTENTO_S = 2


def redimensionar(frame, lado_mayor: int = LADO_MAYOR_PX):
    """Devuelve el frame con su lado mayor a `lado_mayor` px, manteniendo proporción.

    Si el frame ya es menor o igual, lo devuelve sin tocar (no se agranda).
    """
    alto, ancho = frame.shape[:2]
    mayor = max(alto, ancho)
    if mayor <= lado_mayor:
        return frame
    escala = lado_mayor / mayor
    nuevo = (round(ancho * escala), round(alto * escala))  # cv2 usa (ancho, alto)
    return cv2.resize(frame, nuevo, interpolation=cv2.INTER_AREA)


def guardar_frame(frame, numero: int) -> Path:
    """Guarda data/frames/NNNN.jpg y actualiza latest.jpg de forma atómica.

    latest.jpg se escribe a un temporal y se renombra con os.replace, para que
    el agente nunca lea un JPG a medio escribir.
    """
    FRAMES.mkdir(parents=True, exist_ok=True)
    destino = FRAMES / f"{numero:04d}.jpg"
    frame = redimensionar(frame)
    cv2.imwrite(str(destino), frame)

    # latest.jpg atómico: temporal en la misma carpeta + os.replace.
    tmp = FRAMES / "latest.tmp.jpg"
    cv2.imwrite(str(tmp), frame)
    os.replace(tmp, LATEST)
    return destino


def siguiente_numero() -> int:
    """Siguiente NNNN a partir de los archivos que ya existen en data/frames/.

    Para no pisar frames si el grabber se reinicia. Empieza en 1.
    """
    if not FRAMES.exists():
        return 1
    numeros = []
    for p in FRAMES.glob("[0-9][0-9][0-9][0-9].jpg"):
        try:
            numeros.append(int(p.stem))
        except ValueError:
            continue
    return max(numeros, default=0) + 1


def loop(url: str, intervalo_s: float) -> None:
    """Bucle principal.

    - cv2.VideoCapture(url); si no abre o se cae, reintenta cada REINTENTO_S sin morir.
    - Lee frames continuamente (para no acumular buffer) y guarda 1 cada `intervalo_s`.
    - El estado.json (Hito 2) lo maneja escribir_estado; aquí solo se guardan frames.
    """
    FRAMES.mkdir(parents=True, exist_ok=True)
    numero = siguiente_numero()
    ultimo_guardado = 0.0
    cap = None
    print(f"Grabber: leyendo {url}, 1 frame cada {intervalo_s}s. Ctrl+C para parar.")
    try:
        while True:
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                cap = cv2.VideoCapture(url)
                if not cap.isOpened():
                    print(f"Sin stream en {url}; reintento en {REINTENTO_S}s…")
                    time.sleep(REINTENTO_S)
                    continue

            ok, frame = cap.read()
            if not ok:
                print("Lectura fallida; libero la captura y reintento…")
                cap.release()
                cap = None
                time.sleep(REINTENTO_S)
                continue

            ahora = time.monotonic()
            if ahora - ultimo_guardado >= intervalo_s:
                destino = guardar_frame(frame, numero)
                print(f"  guardado {destino.name}")
                numero += 1
                ultimo_guardado = ahora
    except KeyboardInterrupt:
        print("\nGrabber detenido.")
    finally:
        if cap is not None:
            cap.release()


def escribir_estado(estado_stream: str, ultimo_frame_ts: str | None) -> None:
    """Escribe data/estado.json (atómico)."""
    # TODO(cesar): Hito 2 (T2.2) — integrar en el loop con transición a sin_senal.
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
