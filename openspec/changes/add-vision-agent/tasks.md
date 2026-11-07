# Tasks — add-vision-agent (Rulo)

Solo se edita `agent/`. Lo que haga falta de otras carpetas va en `NOTAS-INTEGRACION.md`.
Firmas de la SDK ya verificadas en los comentarios de `agent/main.py` y `agent/tools.py`.

## 1. Hito 1 (10:15) — corre solo con mocks

- [ ] 1.1 `uv sync`, copiar `.env.example` a `.env` con `ANTHROPIC_API_KEY`; verificar con `uv run python -c "import claude_agent_sdk"`
- [ ] 1.2 Poner 3–5 fotos en `samples/` (cultivo y personas)
- [ ] 1.3 Implementar `ultimo_frame` en modo `--source` (rotación por la carpeta, texto `{ruta, hora}` + bloque `image`); verificar llamando al handler desde un script corto
- [ ] 1.4 Implementar `indice_vari` (VARI con máscara de vegetación, `pct_estres` 0–100, mapa de calor en `data/mapas/`); verificar con una foto de cultivo que el % es razonable y el mapa se abre
- [ ] 1.5 Implementar `construir_opciones` (`tools=[]`, `allowed_tools`, `max_turns=4`, `max_budget_usd=0.05`, `output_format` con el schema) y `analizar_frame`; verificar con `uv run python agent/main.py --source samples/ --dry-run --una-vez` que imprime un hallazgo válido
- [ ] 1.6 Verificar un frame de cultivo (`pct_estres` numérico, `personas` null) y uno de personas (`personas` entero, `pct_estres` null); anotar `num_turns` y costo por frame
- [ ] 1.7 Si el schema con `if/then` falla en la SDK, dejar nota en `NOTAS-INTEGRACION.md` (no editar `contracts/`)

## 2. Hito 2 (11:00) — se conecta con el contrato real

- [ ] 2.1 Implementar `publicar` con `httpx` (POST con `costo_usd`) y respaldo en `data/hallazgos.jsonl`; verificar con la API de César arriba (201) y apagada (línea nueva en el jsonl)
- [ ] 2.2 Implementar `loop` cada 5 s con acumulador de costo y tope `PRESUPUESTO_USD`; verificar con `--presupuesto 0.10` que se detiene y lo reporta
- [ ] 2.3 Implementar `ultimo_frame` en modo en vivo sobre `data/frames/latest.jpg`, con `imagen` = `frames/NNNN.jpg` real; verificar con `scripts/replay.sh` + grabber
- [ ] 2.4 Saltar frames repetidos; verificar que con el stream pausado no se gastan consultas
- [ ] 2.5 Afinar `agent/prompts/system.md` con las fotos de prueba; verificar que ninguna `descripcion` menciona rasgos de personas

## 3. Hito 3 (11:50) — integración de punta a punta y pulido

- [ ] 3.1 Volar el dron (o `replay.sh`) con grabber + API + dashboard; verificar que los hallazgos aparecen en el dashboard en menos de 10 s
- [ ] 3.2 Revisar el gasto real contra el presupuesto en `GET /estado` y ajustar `MODELO`/intervalo si hace falta
- [ ] 3.3 Imprimir en consola un resumen por frame (hora, tipo, severidad, costo, acumulado) para la demo
- [ ] 3.4 Verificar contra `contracts/` y actualizar `NOTAS-INTEGRACION.md`
