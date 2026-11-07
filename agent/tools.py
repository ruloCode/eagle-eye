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

from pathlib import Path
from typing import Any

from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LATEST = DATA / "frames" / "latest.jpg"
MAPAS = DATA / "mapas"

# Umbral de VARI bajo el cual un píxel de vegetación cuenta como "estresado".
# TODO(rulo): calibrar con las fotos de samples/.
UMBRAL_VARI = 0.05

# Fuente de frames: la fija main.py con --source. None = data/frames/latest.jpg.
FUENTE: Path | None = None


def configurar_fuente(source: Path | None) -> None:
    """Llamado por main.py. Si `source` es una carpeta, ultimo_frame rota por sus imágenes."""
    global FUENTE
    FUENTE = source


@tool(
    "ultimo_frame",
    "Devuelve el frame más reciente del dron: su ruta relativa, la hora (HH:MM:SS) y la imagen "
    "para que la mires. Llámala siempre primero.",
    {},
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def ultimo_frame(args: dict[str, Any]) -> dict[str, Any]:
    # TODO(rulo):
    # - Si FUENTE es None: usar data/frames/latest.jpg; la `imagen` del hallazgo es el NNNN.jpg real
    #   (resolverlo comparando con el más reciente en data/frames/, no "latest.jpg").
    # - Si FUENTE es carpeta: siguiente imagen de samples/ (rotación); ruta "samples/<archivo>".
    # - Si no hay frame: devolver is_error=True con "sin frame disponible".
    # - Devolver:
    #   {"content": [
    #       {"type": "text", "text": json.dumps({"ruta": "frames/0231.jpg", "hora": "10:42:07"})},
    #       {"type": "image", "data": base64.b64encode(bytes).decode("ascii"), "mimeType": "image/jpeg"},
    #   ]}
    raise NotImplementedError("TODO(rulo): ultimo_frame")


@tool(
    "indice_vari",
    "Calcula el índice VARI = (G - R) / (G + R - B) sobre una imagen RGB de cultivo. Devuelve "
    "pct_estres (% de píxeles de vegetación con VARI bajo el umbral) y la ruta de un mapa de calor. "
    "Úsala solo si el frame es de cultivo.",
    {"path": str},
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def indice_vari(args: dict[str, Any]) -> dict[str, Any]:
    # TODO(rulo):
    # - Cargar con OpenCV/Pillow → numpy float32; separar R, G, B.
    # - VARI = (G - R) / (G + R - B); evitar división por cero (denominador ~0 → NaN, ignorar).
    # - Máscara de vegetación (p. ej. G > R y G > B) para no contar suelo/cielo como estrés.
    # - pct_estres = 100 * (#píxeles vegetación con VARI < UMBRAL_VARI) / #píxeles vegetación,
    #   redondeado a 1 decimal; 0–100.
    # - Mapa de calor: cv2.applyColorMap sobre VARI normalizado → data/mapas/<nombre>_vari.jpg.
    # - Devolver texto JSON: {"pct_estres": 14.8, "mapa": "mapas/0183_vari.jpg"}.
    # - Ruta inexistente → is_error=True.
    raise NotImplementedError("TODO(rulo): indice_vari")


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
