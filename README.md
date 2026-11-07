# Eagle Eye 🦅

Agente de visión por computador para un dron **DJI Mini 3 Pro**, construido en un workshop de 3 horas de la **Claude Agent SDK**. Analiza en vivo lo que ve el dron en dos modos:

- **Cultivo:** salud visible de las plantas (zonas amarillas/estresadas, huecos de siembra, maleza) con el índice **VARI = (G − R) / (G + R − B)** (la cámara es RGB, no hay NDVI).
- **Personas:** conteo para seguridad o aforo. **Sin reconocimiento facial ni identificación de individuos.**

El MVP muestra los tres requisitos del workshop: **tools propias**, **salida estructurada** y **control de presupuesto** (`max_budget_usd`, `max_turns`).

## Cómo funciona

```
Dron → RC-N1 + celular (DJI Fly) → RTMP → MediaMTX (portátil, :1935 /live/dron)
     → grabber (OpenCV) guarda 1 frame cada N s en data/frames/
     → agente (Claude Agent SDK) analiza el último frame → JSON estructurado
     → POST a la API (FastAPI, :8000) → SQLite
     → dashboard web (:5500) que consulta la API cada 2 s
```

| Carpeta | Dueño | Qué hay |
|---|---|---|
| `contracts/` | los tres | JSON Schema del hallazgo, contrato de la API, fixtures |
| `agent/` | Rulo | agente SDK, tools `ultimo_frame` e `indice_vari`, system prompt |
| `ingest/` | César | MediaMTX + grabber |
| `backend/` | César | SQLite + FastAPI |
| `scripts/` | César | `replay.sh` (plan B), `dev.sh`, `seed.py` |
| `dashboard/` | Daniela | HTML/CSS/JS sin build |
| `openspec/` | los tres | specs y un change por frente |

Reglas de equipo, puertos y rutas: [`CLAUDE.md`](CLAUDE.md). Contrato: [`contracts/api.md`](contracts/api.md).

## Requisitos

- Python 3.11+ y [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- ffmpeg (`brew install ffmpeg`) y MediaMTX (`brew install mediamtx`) — solo para la ingesta
- Node ≥ 20.19 + OpenSpec (`npm i -g @fission-ai/openspec@latest`) — para `/opsx:*`
- `ANTHROPIC_API_KEY` en `.env` (copia `.env.example`)

## Arrancar tu frente

```bash
git clone git@github.com:ruloCode/eagle-eye.git && cd eagle-eye && git checkout feat/<frente>
cp .env.example .env      # y pon tu ANTHROPIC_API_KEY
uv sync                   # Daniela no lo necesita
claude                    # → /opsx:apply <tu-change>
```

| Persona | Rama | Change |
|---|---|---|
| Rulo | `feat/agent` | `add-vision-agent` |
| César | `feat/backend` | `add-stream-ingest`, luego `add-hallazgos-api` |
| Daniela | `feat/dashboard` | `add-live-dashboard` |

## Correr cada parte sola (mocks)

```bash
# Dashboard con fixtures (sin API, sin Python deps)
scripts/dev.sh --solo-web            # → http://localhost:5500/dashboard/?mock=1

# Agente con fotos locales, imprime el JSON
uv run python agent/main.py --source samples/ --dry-run --una-vez

# Backend con datos de prueba
uv run python scripts/seed.py --reset
uv run uvicorn backend.api:app --reload --port 8000
```

## Correr todo

```bash
mediamtx ingest/mediamtx.yml                 # 1. servidor RTMP
uv run python ingest/grabber.py              # 2. frames
scripts/dev.sh                               # 3. API :8000 + dashboard :5500
uv run python agent/main.py                  # 4. agente
```

En DJI Fly: *Transmisión en vivo → RTMP* → `rtmp://<IP-del-portátil>:1935/live/dron` (celular y portátil en la misma red; lo más fiable es el hotspot del portátil).

## Plan B: sin dron

Si el RTMP de DJI Fly no conecta, retransmite un video grabado al mismo servidor. El resto del pipeline no cambia.

```bash
scripts/replay.sh samples/vuelo.mp4             # en bucle hasta Ctrl+C
scripts/replay.sh samples/vuelo.mp4 --once      # una sola vez
```

## OpenSpec

```bash
openspec list                         # changes activos
openspec show add-vision-agent        # ver un change
openspec validate add-vision-agent    # validar
```

Spec base compartida: `openspec/specs/contrato-hallazgo/spec.md`. En Claude Code, `/opsx:apply <change>` trabaja las tareas de `tasks.md`, agrupadas por hito (10:15 mocks · 11:00 contrato real · 11:50 punta a punta).

## Integración

- **11:00** — merge de `feat/agent`, `feat/backend` y `feat/dashboard` a `main` (Hito 2: contrato real).
- **11:45** — segundo merge a `main` para la integración de punta a punta (Hito 3, 11:50).
- Antes de cada merge: `git fetch && git rebase origin/main` en tu rama y revisa `NOTAS-INTEGRACION.md`.
- **Si hay conflicto en `contracts/`, se resuelve entre los tres**, y el cambio va en un commit aparte con prefijo `contract:`.
- Conflictos fuera de `contracts/` no deberían ocurrir: cada uno solo toca su carpeta.

```bash
git checkout main && git pull
git merge --no-ff feat/backend && git merge --no-ff feat/agent && git merge --no-ff feat/dashboard
git push origin main
```

### Si hay que recrear el repo remoto

```bash
gh repo create eagle-eye --private --source . --remote origin
git push -u origin main feat/agent feat/backend feat/dashboard
```
