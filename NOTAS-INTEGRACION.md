# Notas de integración

Aquí se deja todo lo que un frente necesita de **otra carpeta** o de `contracts/`, en vez de editarla directamente.
El dueño de la carpeta lee estas notas, decide y responde. Las más nuevas arriba.

## Plantilla

```markdown
### [AAAA-MM-DD HH:MM] <de> → <para> — <título corto>
- **Estado:** abierta | en curso | resuelta | descartada
- **Carpeta / archivo:** <p. ej. backend/api.py, contracts/api.md>
- **Qué necesito:** <una o dos frases>
- **Por qué:** <qué se rompe o qué no puedo hacer sin esto>
- **Propuesta:** <cambio concreto, ejemplo de JSON, etc.>
- **Respuesta:** <la escribe el dueño>
```

Si la nota toca `contracts/`, se resuelve entre los tres y el cambio va en un commit aparte con prefijo `contract:`.

---

## Notas

<!-- Escribe la primera nota debajo de esta línea -->

### [2026-11-07 11:10] César → Rulo y Daniela — Backend + ingesta listos para integrar
- **Estado:** abierta
- **Carpeta / archivo:** `backend/`, `ingest/`, `scripts/` (informativo)
- **Qué necesito:** que enganchen sus frentes contra la API/archivos reales.
- **Qué está listo (Hitos 1 y 2 verificados):**
  - API en `:8000`: `POST /hallazgos` (valida contra `contracts/hallazgo.schema.json`, 422 sin guardar), `GET /hallazgos?limit=`, `GET /estado`, `GET /frames/{archivo}`. Respuestas conformes a `contracts/`.
  - Grabber: `data/frames/NNNN.jpg` + `latest.jpg` (atómico), `data/estado.json` (`en_vivo`/`sin_senal` en ≤ 10 s, reconecta solo).
  - `scripts/seed.py --reset` carga los 6 fixtures; `scripts/dev.sh` levanta API + dashboard.
- **Cómo probar sin mí:**
  - Con mocks: `scripts/dev.sh` → `http://localhost:5500/dashboard/?mock=1`.
  - Con API real: `uv run python scripts/seed.py --reset && scripts/dev.sh`.
  - Plan B del stream: `mediamtx ingest/mediamtx.yml` + `scripts/replay.sh samples/<video>.mp4` + `uv run python ingest/grabber.py`.
- **Pendiente de ustedes (Hito 3):**
  - **Rulo:** T2.5/T3.1 de la API — que el agente haga `POST` real (`agent/main.py --source samples/`) y que `imagen` del hallazgo apunte a un `frames/NNNN.jpg` existente. Ya verifiqué el `POST` vía curl con el cuerpo del contrato.
  - **Daniela:** T3.1/T3.2 del dashboard — confirmar que al pasar de `?mock=1` a la API real no hace falta tocar nada (las formas coinciden) y que "sin señal"/"en vivo" se reflejan.
- **Respuesta:**
  - **Daniela (2026-11-07 11:52):** dashboard verificado contra la API real (`seed.py --reset` + `uvicorn backend.api:app`). Al pasar de `?mock=1` a la API no hubo que tocar nada: las formas coinciden. "En vivo"/"sin señal" se reflejan según `data/estado.json`; también probados `GET /frames` (sin parpadeo; 404 → foto de respaldo), presupuesto agotado (`POST` con `costo_usd` alto), API caída (aviso, conserva datos, se recupera sola) y base vacía ("analizando"). Me falta solo la prueba punta a punta con el agente de Rulo (T3.1).
  - **Rulo:** <pendiente>

### [2026-11-07 10:57] César → todos — Ignorar auto.crt / auto.key de MediaMTX
- **Estado:** abierta
- **Carpeta / archivo:** `.gitignore` (raíz, compartido)
- **Qué necesito:** agregar `auto.crt` y `auto.key` al `.gitignore`.
- **Por qué:** MediaMTX genera esos certificados autofirmados en la raíz al arrancar (aun con TLS apagado). No deben ir a git y hoy aparecen como untracked al correr la ingesta.
- **Propuesta:** añadir dos líneas al `.gitignore`:
  ```
  auto.crt
  auto.key
  ```
- **Respuesta:** <la escribe quien corresponda>
