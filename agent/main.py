"""Agente de visión de Eagle Eye (Claude Agent SDK).

Dueño: Rulo. Change de OpenSpec: add-vision-agent (capacidad `agente-vision`).

Uso:
    uv run python agent/main.py                          # loop sobre data/frames/latest.jpg, POST a la API
    uv run python agent/main.py --source samples/        # fotos locales en vez del stream
    uv run python agent/main.py --source samples/ --dry-run --una-vez

Requisitos del workshop que esto muestra: tools propias (agent/tools.py), salida estructurada
(output_format = contracts/hallazgo.schema.json) y control de presupuesto (max_turns, max_budget_usd,
tope global PRESUPUESTO_USD).

---------------------------------------------------------------------------------------------------
API de la SDK (verificada en code.claude.com/docs/en/agent-sdk/python y .../structured-outputs,
nov-2026). NO inventar otras.

    async def query(*, prompt: str | AsyncIterable[dict[str, Any]],
                    options: ClaudeAgentOptions | None = None,
                    transport: Transport | None = None) -> AsyncIterator[Message]
      - Cada llamada es una sesión nueva (bien para nosotros: 1 frame = 1 consulta, sin contexto viejo).
      - Un query() de un solo disparo LANZA una excepción después de emitir un ResultMessage de error
        (p. ej. error_max_budget_usd, error_max_turns). Hay que envolverlo en try/except.

    @dataclass ClaudeAgentOptions:
        system_prompt: str | {"type": "file", "path": "..."} | ... = None
        mcp_servers: dict[str, McpServerConfig] = {}
        allowed_tools: list[str] = []      # auto-aprueba; NO restringe
        tools: list[str] | None            # disponibilidad de built-ins; [] = sin built-ins (solo MCP)
        permission_mode: "default" | "acceptEdits" | "plan" | "dontAsk" | "bypassPermissions" | "auto"
        max_turns: int | None = None
        max_budget_usd: float | None = None  # estimación del cliente; puede pasarse un poco → dejar margen
        model: str | None = None
        output_format: dict | None = None    # {"type": "json_schema", "schema": {...}}  (JSON Schema draft-07)
        cwd: str | Path | None = None

    @dataclass ResultMessage:
        subtype: str   # "success" | "error_during_execution" | "error_max_turns"
                       # | "error_max_budget_usd" | "error_max_structured_output_retries"
        is_error: bool
        num_turns: int
        total_cost_usd: float | None
        usage: dict | None
        result: str | None             # texto final solo si subtype == "success"
        structured_output: Any = None  # dict validado contra el schema si se pasó output_format

  Éxito = subtype == "success" AND structured_output no es None (puede venir success sin structured_output:
  tratarlo como fallo).
  Con output_format aparece una tool "StructuredOutput" que no definimos: no mostrarla como paso del agente.
---------------------------------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Imports reales de la SDK que vas a usar:
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query  # noqa: F401

from tools import SERVIDOR, TOOLS_PERMITIDAS, configurar_fuente, servidor_vision  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "hallazgo.schema.json"
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"
RESPALDO_JSONL = ROOT / "data" / "hallazgos.jsonl"

INTERVALO_S = 5
MAX_TURNS = 4
BUDGET_POR_CONSULTA_USD = 0.05


def cargar_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def construir_opciones(modelo: str) -> ClaudeAgentOptions:
    """Arma ClaudeAgentOptions.

    TODO(rulo): devolver algo como:

        ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
            model=modelo,
            mcp_servers={SERVIDOR: servidor_vision},
            allowed_tools=TOOLS_PERMITIDAS,
            tools=[],                              # sin Bash/Read/etc.: solo nuestras tools
            max_turns=MAX_TURNS,                   # ≤ 4
            max_budget_usd=BUDGET_POR_CONSULTA_USD,  # 0.05 por consulta
            output_format={"type": "json_schema", "schema": cargar_schema()},
            cwd=str(ROOT),
        )
    """
    raise NotImplementedError("TODO(rulo): construir_opciones")


async def analizar_frame(opciones: ClaudeAgentOptions) -> tuple[dict[str, Any] | None, float, str]:
    """Una consulta = un frame. Devuelve (hallazgo | None, costo_usd, subtype).

    TODO(rulo):
        hallazgo, costo, subtype = None, 0.0, "sin_resultado"
        try:
            async for msg in query(prompt="Analiza el último frame del dron.", options=opciones):
                if isinstance(msg, ResultMessage):
                    costo = msg.total_cost_usd or 0.0
                    subtype = msg.subtype
                    if msg.subtype == "success" and msg.structured_output:
                        hallazgo = msg.structured_output
        except Exception as e:
            # query() lanza después de un ResultMessage de error; el costo ya quedó registrado arriba.
            ...
        return hallazgo, costo, subtype
    """
    raise NotImplementedError("TODO(rulo): analizar_frame")


async def publicar(hallazgo: dict[str, Any], costo_usd: float, api_url: str, dry_run: bool) -> None:
    """POST {api_url}/hallazgos con hallazgo + costo_usd.

    TODO(rulo):
    - dry_run → imprimir el JSON (indentado) y salir.
    - httpx.AsyncClient().post(..., timeout=3); si falla (conexión o != 201) → append a
      data/hallazgos.jsonl (una línea JSON por hallazgo, con costo_usd).
    """
    raise NotImplementedError("TODO(rulo): publicar")


async def loop(args: argparse.Namespace) -> None:
    """Loop principal cada INTERVALO_S.

    TODO(rulo):
    - gastado = 0.0; antes de cada consulta, si gastado + BUDGET_POR_CONSULTA_USD > presupuesto:
      imprimir "Presupuesto agotado: $X de $Y" y salir del loop (no lanzar otra consulta).
    - analizar_frame → sumar costo (también en errores) → si hay hallazgo, publicar.
    - Saltar el frame si es el mismo que el anterior (no gastar dos veces en la misma imagen).
    - --una-vez: una sola iteración.
    - Imprimir en cada vuelta: hora, tipo, severidad, costo de la consulta y acumulado.
    """
    raise NotImplementedError("TODO(rulo): loop")


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Agente de visión de Eagle Eye")
    parser.add_argument("--source", type=Path, default=None, help="carpeta con fotos (p. ej. samples/)")
    parser.add_argument("--dry-run", action="store_true", help="imprime el JSON en vez de hacer POST")
    parser.add_argument("--una-vez", action="store_true", help="analiza un solo frame y termina")
    parser.add_argument("--modelo", default=os.getenv("MODELO", "claude-sonnet-5-5"))
    parser.add_argument(
        "--presupuesto",
        type=float,
        default=float(os.getenv("PRESUPUESTO_USD", "2.00")),
        help="tope global de la sesión en USD",
    )
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"))
    args = parser.parse_args()

    configurar_fuente(args.source)
    asyncio.run(loop(args))


if __name__ == "__main__":
    main()
