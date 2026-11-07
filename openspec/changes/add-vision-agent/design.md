# Design

## Context

API de la Claude Agent SDK para Python verificada en la documentación oficial (code.claude.com/docs/en/agent-sdk, nov-2026); las firmas exactas están comentadas en `agent/main.py` y `agent/tools.py`. Puntos que condicionan el diseño:

- `query(prompt=..., options=ClaudeAgentOptions(...))` abre una sesión nueva por llamada.
- `output_format={"type": "json_schema", "schema": ...}` valida con JSON Schema **draft-07** y deja el resultado en `ResultMessage.structured_output`. La SDK reintenta si no cumple; si se agota, `subtype == "error_max_structured_output_retries"`.
- `ResultMessage.total_cost_usd` da el costo de la consulta; `subtype` puede ser `error_max_budget_usd` o `error_max_turns`.
- Un `query()` de un solo disparo lanza una excepción después de emitir un `ResultMessage` de error.
- Las tools `@tool` pueden devolver bloques `{"type": "image", "data": <base64>, "mimeType": "image/jpeg"}` que le llegan a Claude como imagen.

## Goals / Non-Goals

**Goals:**
- Un hallazgo válido por frame, en ≤ 4 turnos y ≤ USD 0.05.
- Tope de sesión que nunca se supera por más de una consulta.
- Correr sin dron ni API (`--source samples/ --dry-run`).

**Non-Goals:**
- Reconocimiento facial o identificación de individuos (prohibido).
- Detección de personas con un modelo local (YOLO, etc.): el conteo lo hace Claude.
- Historial o memoria entre frames.

## Decisions

- **Una consulta `query()` por frame** en lugar de `ClaudeSDKClient`: cada frame es independiente; no arrastrar contexto evita que el costo crezca con el tiempo.
- **La imagen entra por la tool `ultimo_frame`** (bloque `image`), no en el prompt: es el mecanismo documentado para imágenes en tools propias y deja el prompt fijo. La tool devuelve también `ruta` y `hora` en texto para rellenar `hora` e `imagen` sin inventarlos.
- **`tools=[]`** para quitar las built-ins (Bash, Read, …): el agente solo ve `mcp__vision__ultimo_frame`, `mcp__vision__indice_vari` y la `StructuredOutput` que añade la SDK. Menos tokens y nada fuera de control. `allowed_tools` lista las dos nuestras para que no pidan permiso.
- **Presupuesto en tres capas:** `max_turns=4` y `max_budget_usd=0.05` por consulta (SDK) + acumulador propio con `total_cost_usd`. Antes de cada consulta: si `gastado + 0.05 > PRESUPUESTO_USD`, el loop para. Se suma el costo también en consultas fallidas.
- **VARI con máscara de vegetación:** el % se calcula solo sobre píxeles verdosos para que suelo o caminos no cuenten como estrés. Umbral en `UMBRAL_VARI` (0.05 inicial, a calibrar con `samples/`). El mapa de calor va a `data/mapas/`.
- **Saltar frames repetidos:** si `latest.jpg` no cambió desde la última consulta, no se gasta en analizarlo otra vez.
- **Respaldo:** si el POST falla (conexión o ≠ 201), una línea JSON en `data/hallazgos.jsonl`.
- **Modelo** configurable con `MODELO` (por defecto `claude-sonnet-5-5`); bajar a Haiku si el costo por frame no cabe en el presupuesto.

## Risks / Trade-offs

- [Con `max_turns=4` no caben ultimo_frame + indice_vari + StructuredOutput si el modelo se desvía] → el system prompt fija el orden y el máximo de 3 llamadas; medir `num_turns` en el Hito 1.
- [`if/then` del schema rechazado por el validador de la SDK] → probar en el Hito 1; si falla, dejar nota en `NOTAS-INTEGRACION.md` para acordar en `contracts/` un schema sin condicionales (la API seguiría validando las reglas por tipo).
- [`max_budget_usd` es una estimación y puede pasarse un poco] → el tope global deja margen de una consulta.
- [Imágenes de 1024 px son caras] → el grabber ya reduce; si hace falta, reducir más en la tool antes de codificar.
- [Conteo impreciso en multitudes densas] → la severidad se basa en rangos, no en el número exacto.
