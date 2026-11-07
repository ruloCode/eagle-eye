# Contrato de la API — Eagle Eye

Base: `http://localhost:8000` (variable `API_URL`). JSON en UTF-8. Dueño de la implementación: César (`backend/`).
Este archivo es **territorio compartido**: solo se cambia con acuerdo de los tres, en un commit aparte con prefijo `contract:`.

El formato del hallazgo está en [`hallazgo.schema.json`](hallazgo.schema.json). Ejemplos reales en [`fixtures/`](fixtures/).

---

## `POST /hallazgos`

Lo llama el agente después de analizar cada frame.

**Cuerpo:** un hallazgo válido según `hallazgo.schema.json` **más** `costo_usd` (number ≥ 0, costo de esa consulta; lo agrega el agente a partir de `ResultMessage.total_cost_usd`).

```json
{
  "hora": "10:46:12",
  "imagen": "frames/0226.jpg",
  "tipo": "cultivo",
  "severidad": "alta",
  "personas": null,
  "pct_estres": 37.4,
  "descripcion": "Franja amarilla extensa en el lote este, compatible con estrés hídrico o falla de riego.",
  "recomendacion": "Revisar goteo del lote este hoy mismo.",
  "costo_usd": 0.0271
}
```

**Respuestas:**

| Código | Cuándo | Cuerpo |
|---|---|---|
| `201` | Guardado | `{"id": 5}` |
| `422` | No cumple el schema (campo faltante, campo extra, enum inválido, `descripcion` > 140, etc.) o falta `costo_usd` | `{"detail": "<motivo>"}` |

Validación: se separa `costo_usd` y el resto se valida contra `hallazgo.schema.json` tal cual (incluye `additionalProperties: false` y las reglas `tipo` → `personas`/`pct_estres`).

---

## `GET /hallazgos?limit=20`

Lista de hallazgos, **el más reciente primero**. `limit` opcional, por defecto 20, máximo 100.

```json
[
  { "id": 6, "hora": "10:47:32", "imagen": "frames/0246.jpg", "tipo": "personas", "severidad": "alta",
    "personas": 58, "pct_estres": null, "descripcion": "…", "recomendacion": "…", "costo_usd": 0.0184 }
]
```

Cada elemento = hallazgo + `id` (integer) + `costo_usd`. Ejemplo completo: [`fixtures/hallazgos.sample.json`](fixtures/hallazgos.sample.json).

---

## `GET /estado`

```json
{
  "estado_stream": "en_vivo",
  "frames_analizados": 6,
  "costo_usd": 0.1248,
  "presupuesto_usd": 2.0,
  "ultimo_frame": "frames/0246.jpg"
}
```

| Campo | Tipo | Origen |
|---|---|---|
| `estado_stream` | `"en_vivo"` \| `"sin_senal"` | `data/estado.json` del grabber. Si el archivo no existe → `"sin_senal"`. |
| `frames_analizados` | integer | Cantidad de hallazgos del vuelo actual. |
| `costo_usd` | number | Suma de `costo_usd` de los hallazgos del vuelo actual. |
| `presupuesto_usd` | number | `PRESUPUESTO_USD` del `.env` (por defecto 2.00). |
| `ultimo_frame` | string \| null | `imagen` del hallazgo más reciente, o null si no hay. |

El dashboard deriva de aquí el estado "presupuesto agotado" (`costo_usd >= presupuesto_usd`).

---

## `GET /frames/{archivo}`

Sirve la imagen `data/frames/{archivo}` (`image/jpeg`). `404` si no existe. No permite rutas con `..` ni `/`.
Para pintar un hallazgo: `GET {API_URL}/` + `imagen` → `/frames/0226.jpg`.

---

## CORS

Abierto para orígenes `http://localhost:*` y `http://127.0.0.1:*` (el dashboard se sirve en `:5500`).

---

## Interfaces de archivo (ingesta → agente/API)

Todo bajo `data/` (en `.gitignore`, se crea al correr).

| Archivo | Escribe | Lee | Formato |
|---|---|---|---|
| `data/frames/NNNN.jpg` | grabber | API (`/frames`) | JPEG, lado mayor 1024 px, numeración con 4 dígitos que crece. |
| `data/frames/latest.jpg` | grabber | agente | Copia del último frame (escritura atómica: escribir a temporal y renombrar). |
| `data/estado.json` | grabber | API | `{"estado_stream": "en_vivo"\|"sin_senal", "ultimo_frame_ts": "<ISO 8601>"}`. Si pasan > 10 s sin frames nuevos → `"sin_senal"`. |
| `data/eagle.db` | API | API | SQLite (tablas `hallazgos`, `vuelos`). |
| `data/hallazgos.jsonl` | agente | humanos / `seed.py` | Respaldo: una línea por hallazgo + `costo_usd` cuando la API no responde. |

## Modo mock

- Dashboard: `?mock=1` lee `contracts/fixtures/estado.sample.json` y `contracts/fixtures/hallazgos.sample.json` en vez de la API.
- Backend: `scripts/seed.py` carga `fixtures/hallazgos.sample.json` en SQLite (ignorando el `id`).
