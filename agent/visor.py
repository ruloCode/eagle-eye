"""Visor en vivo de Eagle Eye: video del dron con baja latencia + panel del agente encima.

Dueño: Rulo. Es la "vista de piloto": el mismo video que ffplay (RTMP directo de MediaMTX, sin
pasar por el grabber ni por el agente) con los datos del dashboard dibujados encima — personas,
severidad, último hallazgo y gasto — leídos de la API cada segundo.

Uso:
    uv run python agent/visor.py                 # RTMP_URL y API_URL salen de .env
    uv run python agent/visor.py --ancho 1600    # ventana más grande
Teclas: q / Esc cierra.
"""

from __future__ import annotations

import argparse
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Opciones de FFmpeg para OpenCV: sin buffer y baja latencia (igual que ffplay -fflags nobuffer).
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS", "fflags;nobuffer|flags;low_delay|rw_timeout;5000000"
)

import cv2  # noqa: E402
import httpx  # noqa: E402
import numpy as np  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VENTANA = "Eagle Eye - vision en vivo"

# Paleta del dashboard (dashboard/styles.css).
AMARILLO = (255, 200, 0)
AZUL = (45, 107, 255)
ROJO = (255, 69, 58)
BLANCO = (255, 255, 255)
BLANCO_70 = (255, 255, 255, 178)
BLANCO_45 = (255, 255, 255, 115)
VIDRIO = (0, 0, 0, 150)
VIDRIO_BORDE = (255, 255, 255, 40)
COLOR_SEVERIDAD = {"baja": AZUL, "media": AMARILLO, "alta": ROJO}


def _fuente(rutas: list[tuple[str, int]], tam: int) -> ImageFont.FreeTypeFont:
    for ruta, indice in rutas:
        try:
            return ImageFont.truetype(ruta, tam, index=indice)
        except OSError:
            continue
    return ImageFont.load_default(tam)


def fuentes(escala: float) -> dict[str, ImageFont.FreeTypeFont]:
    neue = "/System/Library/Fonts/HelveticaNeue.ttc"
    arial_b = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    arial = "/System/Library/Fonts/Supplemental/Arial.ttf"
    mono = "/System/Library/Fonts/SFNSMono.ttf"
    negra = [(neue, 1), (arial_b, 0)]
    normal = [(neue, 0), (arial, 0)]
    m = [(mono, 0), ("/System/Library/Fonts/Menlo.ttc", 0)]
    s = lambda px: max(8, int(px * escala))  # noqa: E731
    return {
        "logo": _fuente(negra, s(30)),
        "pill": _fuente(negra, s(14)),
        "mono": _fuente(m, s(15)),
        "label": _fuente(negra, s(12)),
        "numero": _fuente(negra, s(54)),
        "medio": _fuente(negra, s(30)),
        "texto": _fuente(normal, s(17)),
        "texto_b": _fuente(negra, s(15)),
    }


class Estado:
    """Lo último que se sabe del stream (hilo de captura) y de la API (hilo de polling)."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.frame: np.ndarray | None = None
        self.frame_ts = 0.0
        self.api: dict[str, Any] | None = None
        self.hallazgo: dict[str, Any] | None = None
        self.api_ok = False
        self.vivo = True


def hilo_captura(url: str, st: Estado) -> None:
    """Lee el RTMP sin parar (quedarse siempre con el último frame = latencia mínima)."""
    while st.vivo:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while st.vivo and cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            with st.lock:
                st.frame, st.frame_ts = frame, time.time()
        cap.release()
        time.sleep(1)  # reconectar


def hilo_api(api_url: str, st: Estado) -> None:
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=2) as client:
        while st.vivo:
            try:
                est = client.get("/estado").json()
                hs = client.get("/hallazgos", params={"limit": 1}).json()
                with st.lock:
                    st.api, st.hallazgo, st.api_ok = est, (hs[0] if hs else None), True
            except (httpx.HTTPError, ValueError):
                with st.lock:
                    st.api_ok = False
            time.sleep(1)


def _envolver(draw: ImageDraw.ImageDraw, texto: str, fuente: ImageFont.FreeTypeFont, ancho: int) -> list[str]:
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=fuente) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def _segundos_desde(hora: str) -> int | None:
    try:
        h = datetime.strptime(hora, "%H:%M:%S").time()
    except (TypeError, ValueError):
        return None
    ahora = datetime.now()
    delta = (ahora - datetime.combine(ahora.date(), h)).total_seconds()
    return int(delta) if delta >= 0 else None


def dibujar_panel(w: int, h: int, f: dict, st: Estado, en_vivo: bool) -> np.ndarray:
    """Capa RGBA (w×h) con la UI del dashboard. Se recalcula ~4 veces por segundo, no por frame."""
    e = w / 1280
    px = lambda v: int(v * e)  # noqa: E731
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    with st.lock:
        api, hz, api_ok = st.api, st.hallazgo, st.api_ok

    # Degradados arriba/abajo para que el texto se lea sobre cualquier video.
    for y in range(px(90)):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, int(150 * (1 - y / px(90)))))
    for y in range(px(240)):
        d.line([(0, h - y), (w, h - y)], fill=(0, 0, 0, int(190 * (1 - y / px(240)))))

    # Header: logo · pill de estado · reloj.
    m = px(24)
    d.text((m, m), "EAGLE", font=f["logo"], fill=AMARILLO)
    xe = m + d.textlength("EAGLE ", font=f["logo"])
    caja = d.textbbox((xe, m), "EYE", font=f["logo"])
    d.rounded_rectangle((caja[0] - px(6), caja[1] - px(4), caja[2] + px(6), caja[3] + px(4)), px(6), fill=AMARILLO)
    d.text((xe, m), "EYE", font=f["logo"], fill=(0, 0, 0))

    estado_txt, color = ("EN VIVO", AZUL) if en_vivo else ("SIN SEÑAL", ROJO)
    tw = d.textlength(estado_txt, font=f["pill"])
    pw, ph = tw + px(46), px(34)
    x0, y0 = (w - pw) // 2, m
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), ph // 2, fill=color)
    d.ellipse((x0 + px(14), y0 + ph // 2 - px(5), x0 + px(24), y0 + ph // 2 + px(5)), fill=BLANCO)
    d.text((x0 + px(32), y0 + ph // 2), estado_txt, font=f["pill"], fill=BLANCO, anchor="lm")

    reloj = datetime.now().strftime("%H:%M:%S")
    d.text((w - m, m + ph // 2), reloj, font=f["mono"], fill=BLANCO, anchor="rm")
    if not api_ok:
        d.text((w - m, m + ph + px(10)), "API sin conexión", font=f["label"], fill=ROJO, anchor="ra")

    # Tarjetas abajo a la izquierda: personas · frames · gasto.
    ch, cw, gap = px(130), px(190), px(12)
    y0 = h - m - ch

    def tarjeta(x: int, titulo: str) -> None:
        d.rounded_rectangle((x, y0, x + cw, y0 + ch), px(18), fill=VIDRIO, outline=VIDRIO_BORDE, width=max(1, px(1)))
        d.text((x + px(16), y0 + px(14)), titulo, font=f["label"], fill=BLANCO_70)

    x = m
    tarjeta(x, "PERSONAS")
    personas = hz.get("personas") if hz else None
    sev = (hz or {}).get("severidad")
    d.text((x + px(16), y0 + px(32)), "—" if personas is None else str(personas), font=f["numero"],
           fill=COLOR_SEVERIDAD.get(sev, BLANCO))
    if sev:
        d.text((x + px(16), y0 + ch - px(14)), sev.upper(), font=f["label"], fill=COLOR_SEVERIDAD[sev], anchor="ls")

    x += cw + gap
    tarjeta(x, "FRAMES ANALIZADOS")
    d.text((x + px(16), y0 + px(52)), str((api or {}).get("frames_analizados", "—")), font=f["medio"], fill=BLANCO)

    x += cw + gap
    tarjeta(x, "GASTO DEL AGENTE")
    costo = float((api or {}).get("costo_usd") or 0)
    tope = float((api or {}).get("presupuesto_usd") or 2.0)
    d.text((x + px(16), y0 + px(48)), f"${costo:.2f}", font=f["medio"], fill=BLANCO)
    d.text((x + px(16), y0 + px(88)), f"de ${tope:.2f} · {100 * costo / tope:.0f} %", font=f["label"], fill=BLANCO_45)
    bx0, by = x + px(16), y0 + ch - px(18)
    d.rounded_rectangle((bx0, by, x + cw - px(16), by + px(5)), px(3), fill=(255, 255, 255, 40))
    lleno = bx0 + int((cw - px(32)) * min(costo / tope, 1))
    if lleno > bx0:
        d.rounded_rectangle((bx0, by, lleno, by + px(5)), px(3), fill=AMARILLO)

    # Último hallazgo abajo a la derecha.
    x = m + 3 * (cw + gap)
    hw = w - m - x
    d.rounded_rectangle((x, y0, w - m, y0 + ch), px(18), fill=VIDRIO, outline=VIDRIO_BORDE, width=max(1, px(1)))
    d.text((x + px(16), y0 + px(14)), "ÚLTIMO HALLAZGO", font=f["label"], fill=AMARILLO)
    if hz:
        hace = _segundos_desde(hz.get("hora", ""))
        meta = f"{hz.get('hora', '')} · {hz.get('tipo', '')}" + (f" · hace {hace}s" if hace is not None else "")
        d.text((w - m - px(16), y0 + px(14)), meta, font=f["label"], fill=BLANCO_45, anchor="ra")
        lineas = _envolver(d, hz.get("descripcion", ""), f["texto"], hw - px(32))[:3]
        for i, linea in enumerate(lineas):
            d.text((x + px(16), y0 + px(36) + i * px(22)), linea, font=f["texto"], fill=BLANCO)
        rec = "» " + hz.get("recomendacion", "")
        d.text((x + px(16), y0 + ch - px(14)), rec, font=f["texto_b"], fill=AMARILLO, anchor="ls")
    else:
        d.text((x + px(16), y0 + px(40)), "Esperando al agente…", font=f["texto"], fill=BLANCO_45)

    return np.asarray(capa)


def componer(frame: np.ndarray, capa_bgr: np.ndarray, alfa: np.ndarray) -> np.ndarray:
    return (frame.astype(np.float32) * (1 - alfa) + capa_bgr).astype(np.uint8)


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(description="Visor en vivo de Eagle Eye (video + panel del agente)")
    p.add_argument("--rtmp", default=os.getenv("RTMP_URL", "rtmp://localhost:1935/live/dron"))
    p.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"))
    p.add_argument("--ancho", type=int, default=1280, help="ancho de la ventana en px (16:9)")
    args = p.parse_args()

    w = args.ancho
    h = w * 9 // 16
    f = fuentes(w / 1280)
    st = Estado()
    threading.Thread(target=hilo_captura, args=(args.rtmp, st), daemon=True).start()
    threading.Thread(target=hilo_api, args=(args.api_url, st), daemon=True).start()

    cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(VENTANA, w, h)
    negro = np.zeros((h, w, 3), np.uint8)
    capa_bgr = alfa = None
    ultimo_panel = 0.0

    try:
        while True:
            with st.lock:
                frame, ts = st.frame, st.frame_ts
            en_vivo = frame is not None and time.time() - ts < 3

            ahora = time.time()
            if capa_bgr is None or ahora - ultimo_panel > 0.25:
                rgba = dibujar_panel(w, h, f, st, en_vivo).astype(np.float32) / 255.0
                alfa = rgba[..., 3:4]
                capa_bgr = rgba[..., 2::-1] * alfa * 255.0  # RGB→BGR premultiplicado
                ultimo_panel = ahora

            base = negro if frame is None else cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
            if not en_vivo and frame is not None:
                base = (base * 0.35).astype(np.uint8)
            cv2.imshow(VENTANA, componer(base, capa_bgr, alfa))

            tecla = cv2.waitKey(15) & 0xFF
            if tecla in (ord("q"), 27):
                break
            if cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        st.vivo = False
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
