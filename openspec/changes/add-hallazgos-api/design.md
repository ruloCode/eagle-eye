# Design

## Context

Contrato fijado en `contracts/api.md` y `contracts/hallazgo.schema.json`. La API corre en el mismo portátil que el grabber y el agente; tráfico mínimo (1 POST cada 5 s, 2 GET cada 2 s), así que SQLite basta.

## Goals / Non-Goals

**Goals:**
- Que la API sea el único lugar donde se valida el contrato antes de guardar.
- Respuestas idénticas en forma a los fixtures, para que el dashboard pase de `?mock=1` a real sin cambios.
- Arrancar en frío sin pasos manuales (crea `data/` y las tablas).

**Non-Goals:**
- Autenticación (red local, workshop).
- Varios vuelos simultáneos o historial navegable.
- Escribir frames (los escribe el grabber).

## Decisions

- **Validación con `jsonschema` (Draft7Validator) sobre el archivo del contrato**, no con un modelo Pydantic duplicado: si el contrato cambia, la API lo sigue sin tocar código. Se separa `costo_usd` antes de validar porque el schema tiene `additionalProperties: false`. FastAPI recibe `dict` y la API responde 422 con el mensaje del validador.
- **Tabla `vuelos`**: al arrancar la API se abre un vuelo nuevo con `presupuesto_usd` del `.env`. `frames_analizados` y `costo_usd` de `/estado` son `COUNT`/`SUM` sobre el vuelo actual.
- **`estado_stream`** se lee de `data/estado.json`; si no existe, `sin_senal`.
- **`ultimo_frame`** = `imagen` del hallazgo más reciente (lo que el agente analizó), no el último frame del grabber.
- **`/frames/{archivo}`** con `FileResponse`; se rechazan nombres con `/` o `..` para no salir de `data/frames/`.
- **CORS** con `allow_origin_regex` para `localhost` y `127.0.0.1` en cualquier puerto.
- **`seed.py`** reutiliza `schema.sql` y valida los fixtures con el mismo schema; inserta del más antiguo al más reciente para que `GET /hallazgos` devuelva el orden del fixture.

## Risks / Trade-offs

- [SQLite con escritura y lectura concurrentes] → una conexión por petición; el volumen es mínimo.
- [El schema usa `if/then`] → `jsonschema` lo soporta en draft-07; cubrir con un caso de prueba.
- [`ultimo_frame` apunta a una imagen en `samples/` cuando el agente corre con `--source`] → `/frames` solo sirve `data/frames/`; anotar en `NOTAS-INTEGRACION.md` si el dashboard lo necesita.
