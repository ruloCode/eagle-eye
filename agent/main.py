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
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

# Imports reales de la SDK que vas a usar:
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

import tools
from tools import SERVIDOR, TOOLS_PERMITIDAS, configurar_fuente, servidor_vision

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "hallazgo.schema.json"
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"
RESPALDO_JSONL = ROOT / "data" / "hallazgos.jsonl"

INTERVALO_S = 5
MAX_TURNS = 4
BUDGET_POR_CONSULTA_USD = 0.05


def cargar_schema() -> dict[str, Any]:
    """Schema del contrato apto para output_format.

    La API rechaza allOf/anyOf/oneOf en el nivel superior del schema ("input_schema does not support
    oneOf, allOf, or anyOf at the top level"), así que se quita el allOf con los if/then del contrato
    y esa regla se revisa en Python con cumple_tipo(). contracts/ no se toca (ver NOTAS-INTEGRACION.md).
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for clave in ("allOf", "anyOf", "oneOf", "$id"):
        schema.pop(clave, None)
    return schema


def cumple_tipo(h: dict[str, Any]) -> bool:
    """La regla del allOf del contrato: cultivo → personas null y pct_estres número; personas → al revés."""
    if h.get("tipo") == "cultivo":
        return h.get("personas") is None and isinstance(h.get("pct_estres"), (int, float))
    if h.get("tipo") == "personas":
        return isinstance(h.get("personas"), int) and h.get("pct_estres") is None
    return False


def construir_opciones(modelo: str) -> ClaudeAgentOptions:
    """Arma ClaudeAgentOptions: solo nuestras tools, salida estructurada y presupuesto por consulta."""
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        model=modelo,
        mcp_servers={SERVIDOR: servidor_vision},
        allowed_tools=TOOLS_PERMITIDAS,
        tools=[],  # sin Bash/Read/etc.: solo nuestras tools
        max_turns=MAX_TURNS,
        max_budget_usd=BUDGET_POR_CONSULTA_USD,
        output_format={"type": "json_schema", "schema": cargar_schema()},
        cwd=str(ROOT),
        # Aislamiento: sin ~/.claude/settings, CLAUDE.md, MCPs, plugins ni skills del usuario.
        # Sin esto, cada consulta arrastra ~27k tokens de contexto ajeno (≈ $0.16/frame en Sonnet).
        setting_sources=[],
        strict_mcp_config=True,
        skills=[],
    )


async def analizar_frame(opciones: ClaudeAgentOptions) -> tuple[dict[str, Any] | None, float, str]:
    """Una consulta = un frame. Devuelve (hallazgo | None, costo_usd, subtype)."""
    hallazgo: dict[str, Any] | None = None
    costo, subtype = 0.0, "sin_resultado"
    try:
        async for msg in query(prompt="Analiza el último frame del dron.", options=opciones):
            if isinstance(msg, ResultMessage):
                costo = msg.total_cost_usd or 0.0
                subtype = msg.subtype
                if msg.subtype == "success" and isinstance(msg.structured_output, dict):
                    if cumple_tipo(msg.structured_output):
                        hallazgo = msg.structured_output
                    else:
                        subtype = "no_cumple_tipo"
    except Exception as e:  # noqa: BLE001
        # query() lanza después de un ResultMessage de error; el costo ya quedó registrado arriba.
        if subtype in ("sin_resultado", "success"):
            subtype = f"excepcion: {e}"
    return hallazgo, costo, subtype


def _respaldar(cuerpo: dict[str, Any]) -> None:
    RESPALDO_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with RESPALDO_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(cuerpo, ensure_ascii=False) + "\n")


async def publicar(hallazgo: dict[str, Any], costo_usd: float, api_url: str, dry_run: bool) -> None:
    """POST {api_url}/hallazgos con hallazgo + costo_usd; si falla, respaldo en data/hallazgos.jsonl."""
    cuerpo = {**hallazgo, "costo_usd": round(costo_usd, 6)}
    if dry_run:
        print(json.dumps(cuerpo, ensure_ascii=False, indent=2))
        return
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{api_url.rstrip('/')}/hallazgos", json=cuerpo, timeout=3)
        if r.status_code == 201:
            return
        print(f"  ⚠ API respondió {r.status_code}: {r.text[:200]} → respaldo en {RESPALDO_JSONL.name}")
    except httpx.HTTPError as e:
        print(f"  ⚠ API no disponible ({e.__class__.__name__}) → respaldo en {RESPALDO_JSONL.name}")
    _respaldar(cuerpo)


async def loop(args: argparse.Namespace) -> None:
    """Loop principal cada INTERVALO_S, con tope global de presupuesto."""
    opciones = construir_opciones(args.modelo)
    gastado = 0.0
    anterior: Path | None = None
    modo = f"--source {args.source}" if args.source else "en vivo (data/frames/)"
    print(f"🦅 Eagle Eye — modelo {args.modelo}, {modo}, presupuesto ${args.presupuesto:.2f}"
          f"{' [dry-run]' if args.dry_run else ''}")

    while True:
        if gastado + BUDGET_POR_CONSULTA_USD > args.presupuesto:
            print(f"Presupuesto agotado: ${gastado:.4f} de ${args.presupuesto:.2f}")
            break

        frame = tools.siguiente_frame()
        if frame is None:
            print("  … sin frame disponible")
        elif args.source is None and frame == anterior:
            pass  # mismo frame que la vuelta anterior: no gastar otra consulta
        else:
            anterior = frame
            hallazgo, costo, subtype = await analizar_frame(opciones)
            gastado += costo
            hora = datetime.now().strftime("%H:%M:%S")
            if hallazgo:
                extra = (f"{hallazgo['personas']} personas" if hallazgo["tipo"] == "personas"
                         else f"{hallazgo['pct_estres']}% estrés")
                print(f"[{hora}] {frame.name} → {hallazgo['tipo']} · {hallazgo['severidad']} · {extra}"
                      f" · ${costo:.4f} (acum ${gastado:.4f})")
                await publicar(hallazgo, costo, args.api_url, args.dry_run)
            else:
                print(f"[{hora}] {frame.name} → sin hallazgo ({subtype}) · ${costo:.4f} (acum ${gastado:.4f})")

        if args.una_vez:
            break
        await asyncio.sleep(INTERVALO_S)


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
