# agent/ — Rulo

Agente de visión con la Claude Agent SDK. Analiza el último frame cada 5 s y publica un hallazgo estructurado.

| Archivo | Qué |
|---|---|
| `main.py` | Loop, `ClaudeAgentOptions`, lectura de `ResultMessage` (costo + `structured_output`), POST/respaldo, tope de presupuesto. |
| `tools.py` | Tools propias `ultimo_frame` y `indice_vari` en un MCP server in-process (`mcp__vision__*`). |
| `prompts/system.md` | System prompt: clasificar → VARI o conteo → hallazgo. Nunca identificar personas. |

```bash
uv run python agent/main.py --source samples/ --dry-run --una-vez   # sin dron, sin API
uv run python agent/main.py                                         # en vivo
```

Spec: `openspec/changes/add-vision-agent/`.
