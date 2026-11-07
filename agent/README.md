# agent/ — Rulo

Agente de visión con la Claude Agent SDK. Analiza el último frame cada 5 s y publica un hallazgo estructurado.

| Archivo | Qué |
|---|---|
| `main.py` | Loop, `ClaudeAgentOptions`, lectura de `ResultMessage` (costo + `structured_output`), POST/respaldo, tope de presupuesto. |
| `tools.py` | Tools propias `ultimo_frame` y `indice_vari` en un MCP server in-process (`mcp__vision__*`). |
| `visor.py` | Vista de piloto: video RTMP con baja latencia + panel del agente (personas, hallazgo, gasto) encima. |
| `prompts/system.md` | System prompt: clasificar → VARI o conteo → hallazgo. Nunca identificar personas. |

```bash
uv run python agent/main.py --source samples/ --dry-run --una-vez   # sin dron, sin API
uv run python agent/main.py                                         # en vivo
uv run python agent/visor.py                                        # ventana en vivo con el panel (q/Esc cierra)
```

Spec: `openspec/changes/add-vision-agent/`.

## Correr todo en otro portátil (demo)

Requisitos: `git`, [uv](https://docs.astral.sh/uv/) y MediaMTX (`brew install mediamtx`; en Windows/Linux, el binario de github.com/bluenviron/mediamtx/releases). Celular y portátil en la **misma red Wi‑Fi**.

```bash
git clone https://github.com/ruloCode/eagle-eye.git && cd eagle-eye   # o: git pull
uv sync
cp .env.example .env        # y pegar ANTHROPIC_API_KEY (pedírsela a Rulo por privado, nunca por git)
```

Cinco procesos, cada uno en su terminal:

```bash
mediamtx ingest/mediamtx.yml                 # 1. servidor RTMP :1935
uv run python ingest/grabber.py              # 2. frames → data/frames/
scripts/dev.sh                               # 3. API :8000 + dashboard :5500
uv run python agent/main.py                  # 4. agente (Claude) → POST /hallazgos
uv run python agent/visor.py                 # 5. ventana en vivo con el panel (q/Esc cierra)
```

En **DJI Fly → Transmisión en vivo → RTMP**: `rtmp://<IP-del-portátil>:1935/live/dron`
(IP en macOS: `ipconfig getifaddr en0`; en Windows: `ipconfig`). No pide clave.

- Dashboard: http://localhost:5500/dashboard/ (con datos de prueba: `?mock=1`).
- Gasto: ~$0.01 por frame con `claude-sonnet-5-5`; se detiene solo al llegar a `PRESUPUESTO_USD` (2.00).
- Si DJI Fly no conecta: misma red, firewall del portátil permitiendo el puerto 1935, o usar el hotspot del celular.
- Sin dron: `scripts/replay.sh samples/<video>.mp4` publica en la misma URL.
