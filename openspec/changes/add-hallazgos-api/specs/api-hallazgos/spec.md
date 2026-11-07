## Purpose

Guardar los hallazgos del agente en SQLite y exponerlos por HTTP junto con el estado del stream, el gasto acumulado y las imágenes de los frames, validando todo contra el contrato compartido.

## ADDED Requirements

### Requirement: Persistencia en SQLite

La API SHALL guardar los hallazgos en `data/eagle.db` con las tablas `hallazgos` y `vuelos`, creándolas si no existen al arrancar.

#### Scenario: Arranque en frío

- **WHEN** la API arranca sin `data/eagle.db`
- **THEN** crea la base con las tablas `hallazgos` y `vuelos` y abre un vuelo nuevo

### Requirement: Registrar hallazgo

`POST /hallazgos` SHALL aceptar un hallazgo válido más `costo_usd` (number ≥ 0), guardarlo en el vuelo actual y responder 201 con `{"id": <entero>}`.

#### Scenario: Hallazgo válido

- **WHEN** el agente envía un hallazgo de cultivo válido con `costo_usd` 0.027
- **THEN** la API responde 201 con un `id` nuevo y el hallazgo aparece en `GET /hallazgos`

### Requirement: Validación contra el contrato

`POST /hallazgos` SHALL validar el cuerpo, sin `costo_usd`, contra `contracts/hallazgo.schema.json` y MUST responder 422 sin guardar nada si no cumple o si falta `costo_usd`.

#### Scenario: Campo extra

- **WHEN** el cuerpo incluye un campo `confianza`
- **THEN** la API responde 422 y no guarda el hallazgo

#### Scenario: Enum inválido

- **WHEN** `tipo` es `animales`
- **THEN** la API responde 422

#### Scenario: Falta costo

- **WHEN** el cuerpo es un hallazgo válido sin `costo_usd`
- **THEN** la API responde 422

### Requirement: Listar hallazgos

`GET /hallazgos` SHALL devolver los hallazgos del más reciente al más antiguo, cada uno con `id` y `costo_usd`, limitados por `limit` (por defecto 20, máximo 100).

#### Scenario: Orden y límite

- **WHEN** hay 30 hallazgos y se pide `GET /hallazgos?limit=5`
- **THEN** la respuesta tiene 5 elementos y el primero es el de `id` más alto

### Requirement: Estado y gasto

`GET /estado` SHALL devolver `estado_stream`, `frames_analizados`, `costo_usd` (suma del vuelo actual), `presupuesto_usd` y `ultimo_frame`, con la forma de `contracts/fixtures/estado.sample.json`.

#### Scenario: Suma de costos

- **WHEN** se registraron tres hallazgos con `costo_usd` 0.02, 0.03 y 0.01
- **THEN** `GET /estado` devuelve `frames_analizados` 3 y `costo_usd` 0.06

#### Scenario: Grabber apagado

- **WHEN** no existe `data/estado.json`
- **THEN** `estado_stream` es `sin_senal`

### Requirement: Servir frames

`GET /frames/{archivo}` SHALL servir la imagen de `data/frames/` y MUST responder 404 si no existe o si el nombre intenta salir de esa carpeta.

#### Scenario: Frame existente

- **WHEN** se pide `GET /frames/0231.jpg` y el archivo existe
- **THEN** la API responde 200 con `image/jpeg`

#### Scenario: Ruta maliciosa

- **WHEN** se pide un archivo con `..` en el nombre
- **THEN** la API responde 404 sin leer fuera de `data/frames/`

### Requirement: CORS para localhost

La API SHALL permitir peticiones de orígenes `http://localhost` y `http://127.0.0.1` en cualquier puerto.

#### Scenario: Dashboard en otro puerto

- **WHEN** el dashboard servido en `http://localhost:5500` hace `GET /estado`
- **THEN** el navegador recibe la respuesta sin error de CORS

### Requirement: Carga de fixtures

`scripts/seed.py` SHALL cargar `contracts/fixtures/hallazgos.sample.json` en la base, validando cada hallazgo, de modo que `GET /hallazgos` devuelva el mismo orden que el fixture.

#### Scenario: Seed sobre base vacía

- **WHEN** se ejecuta `scripts/seed.py --reset`
- **THEN** `GET /hallazgos` devuelve 6 hallazgos en el orden del fixture y `GET /estado` muestra `frames_analizados` 6
