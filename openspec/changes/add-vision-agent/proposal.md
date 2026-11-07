# Proposal

## Why

Es el corazón del workshop: un agente de la Claude Agent SDK que mira lo que ve el dron y devuelve un hallazgo útil y estructurado. Debe mostrar los tres requisitos del taller —tools propias, salida estructurada y control de presupuesto— y respetar la prohibición de identificar personas.

## What Changes

- Loop cada 5 s sobre `data/frames/latest.jpg` (o sobre una carpeta con `--source`).
- Tools propias con `@tool` + `create_sdk_mcp_server`:
  - `ultimo_frame()` → ruta, hora y la imagen para que Claude la vea.
  - `indice_vari(path)` → `pct_estres` (% de píxeles de vegetación con VARI bajo el umbral) y ruta de un mapa de calor.
- `output_format` = `contracts/hallazgo.schema.json`; el hallazgo se lee de `ResultMessage.structured_output`.
- Presupuesto: `max_turns` ≤ 4, `max_budget_usd` 0.05 por consulta y tope de sesión `PRESUPUESTO_USD` (2.00); al llegar al tope el loop se detiene y lo reporta.
- System prompt en `agent/prompts/system.md`: clasificar → VARI (cultivo) o conteo (personas) → hallazgo. Nunca identificar personas.
- POST a la API con `costo_usd` (de `ResultMessage.total_cost_usd`); si la API no responde, respaldo en `data/hallazgos.jsonl`.
- Modos de trabajo independiente: `--source samples/`, `--dry-run`, `--una-vez`.

## Capabilities

### New Capabilities
- `agente-vision`: análisis de frames aéreos con la Claude Agent SDK que produce hallazgos estructurados de cultivo o personas bajo un presupuesto controlado.

### Modified Capabilities

## Impact

- Carpeta de Rulo: `agent/` (`main.py`, `tools.py`, `prompts/system.md`).
- Consume `data/frames/latest.jpg` (grabber) y `POST /hallazgos` (API); usa `contracts/hallazgo.schema.json`.
- Escribe `data/mapas/` y `data/hallazgos.jsonl`.
- Dependencias: `claude-agent-sdk`, `opencv-python`, `numpy`, `pillow`, `httpx`, `python-dotenv`. Requiere `ANTHROPIC_API_KEY` en `.env`.
