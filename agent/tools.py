"""Tools propias del agente de visión (in-process MCP server de la Claude Agent SDK).

Dueño: Rulo. Change de OpenSpec: add-vision-agent (capacidad `agente-vision`).

API verificada en la doc de la SDK (code.claude.com/docs/en/agent-sdk/custom-tools, nov-2026):

    def tool(name: str, description: str, input_schema: type | dict[str, Any],
             annotations: ToolAnnotations | None = None)
        -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]

    def create_sdk_mcp_server(name: str, version: str = "1.0.0",
                              tools: list[SdkMcpTool[Any]] | None = None) -> McpSdkServerConfig

- El handler es `async def h(args: dict[str, Any]) -> dict[str, Any]`.
- Devuelve {"content": [bloques], "is_error": bool (opcional)}.
  Bloques: {"type": "text", "text": ...} y
           {"type": "image", "data": <base64 sin prefijo data:>, "mimeType": "image/jpeg"}.
  Un PNG/JPEG/GIF/WebP en un bloque image le llega a Claude como entrada visual.
- En Python, `structuredContent` NO se reenvía desde @tool: los datos van como texto (JSON).
- Si el handler lanza una excepción, Claude recibe el mensaje y el loop sigue; mejor devolver
  "is_error": True con un mensaje claro.
- Nombre que ve Claude: mcp__<clave-en-mcp_servers>__<nombre-tool>. Con la clave "vision":
  mcp__vision__ultimo_frame, mcp__vision__indice_vari.
"""

from __future__ import annotations

import base64
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FRAMES = DATA / "frames"
LATEST = FRAMES / "latest.jpg"
MAPAS = DATA / "mapas"

# Umbral de VARI bajo el cual un píxel de vegetación cuenta como "estresado".
# TODO(rulo): calibrar con fotos reales de cultivo.
UMBRAL_VARI = 0.05

# Lado mayor de la imagen que se le manda a Claude (menos tokens = menos costo).
LADO_MAX = 1024

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}
PATRON_FRAME = re.compile(r"^\d{4}\.jpg$")

# Fuente de frames: la fija main.py con --source. None = data/frames/ (stream en vivo).
FUENTE: Path | None = None
_indice_rotacion = 0

# Frame elegido para la consulta en curso (lo fija main.py con siguiente_frame()).
FRAME_ACTUAL: Path | None = None


def configurar_fuente(source: Path | None) -> None:
    """Llamado por main.py. Si `source` es una carpeta, ultimo_frame rota por sus imágenes."""
    global FUENTE
    FUENTE = source.resolve() if source is not None else None


def _frame_mas_reciente() -> Path | None:
    """El NNNN.jpg de número más alto en data/frames/ (el real detrás de latest.jpg)."""
    if not FRAMES.is_dir():
        return None
    frames = sorted(p for p in FRAMES.iterdir() if PATRON_FRAME.match(p.name))
    return frames[-1] if frames else None


def _imagenes_fuente() -> list[Path]:
    if FUENTE is None or not FUENTE.is_dir():
        return []
    return sorted(p for p in FUENTE.iterdir() if p.suffix.lower() in EXTENSIONES)


def siguiente_frame() -> Path | None:
    """Elige el frame que se va a analizar y lo deja en FRAME_ACTUAL.

    - En vivo: el NNNN.jpg más reciente (main.py lo compara con el anterior para no repetir).
    - Con --source: la siguiente imagen de la carpeta, en rotación.
    """
    global FRAME_ACTUAL, _indice_rotacion
    if FUENTE is None:
        FRAME_ACTUAL = _frame_mas_reciente()
    else:
        imagenes = _imagenes_fuente()
        if not imagenes:
            FRAME_ACTUAL = None
        else:
            FRAME_ACTUAL = imagenes[_indice_rotacion % len(imagenes)]
            _indice_rotacion += 1
    return FRAME_ACTUAL


def ruta_relativa(path: Path) -> str:
    """Ruta que va en `imagen`: relativa a data/ (frames/0231.jpg) o a la raíz (samples/x.jpg)."""
    path = path.resolve()
    for base in (DATA, ROOT):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return path.name


def resolver_ruta(ruta: str) -> Path | None:
    """Inversa de ruta_relativa: busca la ruta bajo data/ y luego bajo la raíz del repo."""
    candidata = Path(ruta)
    if candidata.is_absolute():
        return candidata if candidata.is_file() else None
    for base in (DATA, ROOT):
        p = (base / candidata).resolve()
        if p.is_file() and (p.is_relative_to(DATA) or p.is_relative_to(ROOT)):
            return p
    return None


def _jpeg_reducido(path: Path) -> bytes:
    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((LADO_MAX, LADO_MAX))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()


@tool(
    "ultimo_frame",
    "Devuelve el frame más reciente del dron: su ruta relativa, la hora (HH:MM:SS) y la imagen "
    "para que la mires. Llámala siempre primero.",
    {},
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def ultimo_frame(args: dict[str, Any]) -> dict[str, Any]:
    frame = FRAME_ACTUAL or siguiente_frame()
    if frame is None or not frame.is_file():
        return {"content": [{"type": "text", "text": "sin frame disponible"}], "is_error": True}
    try:
        datos = _jpeg_reducido(frame)
    except OSError as e:
        return {"content": [{"type": "text", "text": f"no se pudo leer el frame: {e}"}], "is_error": True}

    if FUENTE is None:
        hora = datetime.fromtimestamp(frame.stat().st_mtime).strftime("%H:%M:%S")
    else:
        hora = datetime.now().strftime("%H:%M:%S")
    meta = {"ruta": ruta_relativa(frame), "hora": hora}
    return {
        "content": [
            {"type": "text", "text": json.dumps(meta)},
            {"type": "image", "data": base64.b64encode(datos).decode("ascii"), "mimeType": "image/jpeg"},
        ]
    }


def calcular_vari(path: Path) -> tuple[float, Path]:
    """VARI = (G - R) / (G + R - B) con máscara de vegetación. Devuelve (pct_estres, ruta_mapa)."""
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"no se pudo abrir la imagen {path}")
    b, g, r = (bgr[..., i].astype(np.float32) for i in range(3))

    denom = g + r - b
    with np.errstate(divide="ignore", invalid="ignore"):
        vari = np.where(np.abs(denom) > 1e-3, (g - r) / denom, np.nan)
    vari = np.clip(vari, -1.0, 1.0)

    # Vegetación: el verde domina o, si está estresada, el amarillo (R≈G) domina sobre el azul.
    vegetacion = (g > b) & (g >= r * 0.85) & ~np.isnan(vari)
    n_veg = int(vegetacion.sum())
    if n_veg == 0:
        pct = 0.0
    else:
        estresados = int((vegetacion & (vari < UMBRAL_VARI)).sum())
        pct = round(100.0 * estresados / n_veg, 1)

    # Mapa de calor: VARI [-1, 1] → [0, 255]; lo que no es vegetación queda oscuro.
    norm = np.nan_to_num((vari + 1.0) * 127.5, nan=0.0).astype(np.uint8)
    # JET: azul = VARI bajo (estrés), rojo = VARI alto (vegetación sana).
    mapa = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    mapa[~vegetacion] = (mapa[~vegetacion] * 0.25).astype(np.uint8)

    MAPAS.mkdir(parents=True, exist_ok=True)
    destino = MAPAS / f"{path.stem}_vari.jpg"
    cv2.imwrite(str(destino), mapa)
    return min(max(pct, 0.0), 100.0), destino


@tool(
    "indice_vari",
    "Calcula el índice VARI = (G - R) / (G + R - B) sobre una imagen RGB de cultivo. Devuelve "
    "pct_estres (% de píxeles de vegetación con VARI bajo el umbral) y la ruta de un mapa de calor. "
    "Úsala solo si el frame es de cultivo.",
    {"path": str},
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def indice_vari(args: dict[str, Any]) -> dict[str, Any]:
    ruta = str(args.get("path", "")).strip()
    path = resolver_ruta(ruta) if ruta else None
    if path is None:
        return {"content": [{"type": "text", "text": f"ruta inexistente: {ruta!r}"}], "is_error": True}
    try:
        pct, mapa = calcular_vari(path)
    except Exception as e:  # noqa: BLE001 — se le devuelve el error a Claude
        return {"content": [{"type": "text", "text": f"error calculando VARI: {e}"}], "is_error": True}
    resultado = {"pct_estres": pct, "mapa": ruta_relativa(mapa)}
    return {"content": [{"type": "text", "text": json.dumps(resultado)}]}


# Clave del servidor en ClaudeAgentOptions.mcp_servers → prefijo mcp__vision__*.
SERVIDOR = "vision"

servidor_vision = create_sdk_mcp_server(
    name="eagle-eye-vision",
    version="0.1.0",
    tools=[ultimo_frame, indice_vari],
)

TOOLS_PERMITIDAS = [
    f"mcp__{SERVIDOR}__ultimo_frame",
    f"mcp__{SERVIDOR}__indice_vari",
]
