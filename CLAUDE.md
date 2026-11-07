# Eagle Eye 🦅 — reglas para agentes

Agente de visión por computador para un dron DJI Mini 3 Pro. Dos modos: **cultivo** (índice VARI sobre RGB) y **personas** (conteo, **sin reconocimiento facial ni identificación de individuos**). Workshop de 3 horas de la Claude Agent SDK: tres personas en paralelo, cada una con su agente.

## Equipo y propiedad

| Persona | Rol | Es dueña de | Rama | Change de OpenSpec |
|---|---|---|---|---|
| Rulo | Agente + dron | `agent/` | `feat/agent` | `add-vision-agent` |
| César | Ingesta + base de datos + API | `ingest/`, `backend/`, `scripts/` | `feat/backend` | `add-stream-ingest`, `add-hallazgos-api` |
| Daniela | Diseño + dashboard | `dashboard/` | `feat/dashboard` | `add-live-dashboard` |

## Reglas (obligatorias)

1. **Cada agente solo edita la carpeta de su dueño.** Si necesitas algo de otra carpeta, deja una nota en `NOTAS-INTEGRACION.md` (hay plantilla) en vez de editarla.
2. **`contracts/` es territorio compartido:** solo se cambia con acuerdo de los tres, en un commit aparte con el prefijo `contract:`. Lo mismo para `openspec/specs/` (la spec base `contrato-hallazgo`).
3. **Cada parte corre sola, con mocks**, sin las otras dos:
   - Dashboard: `?mock=1` lee `contracts/fixtures/*.json`.
   - Agente: `--source samples/` analiza fotos locales; `--dry-run` imprime el JSON en vez de hacer POST.
   - Backend: `scripts/seed.py` carga los fixtures en SQLite.
4. **Nada de secretos en git.** `ANTHROPIC_API_KEY` va en `.env` (ver `.env.example`).
5. **Commits pequeños con Conventional Commits:** `feat(agent): …`, `feat(backend): …`, `feat(ingest): …`, `feat(dashboard): …`, `fix(...)`, `contract: …`.
6. Los `TODO(<dueño>)` marcan lo que falta implementar. No borres un TODO de otro dueño.

## Puertos y rutas

| Qué | Dónde |
|---|---|
| MediaMTX (RTMP) | `rtmp://localhost:1935/live/dron` |
| API (FastAPI) | `http://localhost:8000` |
| Dashboard (estático) | `http://localhost:5500/dashboard/` (y `?mock=1`) — se sirve desde la raíz del repo |
| Frames | `data/frames/NNNN.jpg`, `data/frames/latest.jpg` (lado mayor 1024 px) |
| Estado del stream | `data/estado.json` → `sin_senal` si pasan > 10 s sin frames |
| Base de datos | `data/eagle.db` (SQLite) |
| Respaldo del agente | `data/hallazgos.jsonl` |

## Contrato

- Hallazgo: `contracts/hallazgo.schema.json` (JSON Schema draft-07; es el `output_format` de la SDK). 8 campos obligatorios: `hora`, `imagen`, `tipo` (`cultivo`|`personas`), `severidad` (`baja`|`media`|`alta`), `personas` (int|null), `pct_estres` (0–100|null), `descripcion` (≤140), `recomendacion` (≤80). Sin campos extra.
- Endpoints: `contracts/api.md` (`POST /hallazgos`, `GET /hallazgos`, `GET /estado`, `GET /frames/{archivo}`).
- Presupuesto del agente: `max_turns` ≤ 4, `max_budget_usd=0.05` por consulta, tope de sesión `PRESUPUESTO_USD` (2.00).

## Stack

- Python 3.11+ con **uv** (`uv sync`, `uv run …`). Dependencias en `pyproject.toml`.
- Dashboard: HTML/CSS/JS **sin build y sin npm**.
- Specs y tareas: **OpenSpec** en `openspec/`. Para trabajar tu frente: `/opsx:apply <tu-change>`. Marca las tareas `- [x]` en `tasks.md` a medida que las terminas.

## Hitos del día

- **10:15** — Hito 1: cada frente corre solo con mocks.
- **11:00** — Hito 2: se conecta con el contrato real. Merge a `main`.
- **11:45** — Merge a `main` para integración.
- **11:50** — Hito 3: punta a punta y pulido.
