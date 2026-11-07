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
