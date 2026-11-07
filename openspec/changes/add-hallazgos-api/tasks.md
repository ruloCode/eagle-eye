# Tasks — add-hallazgos-api (César)

Solo se editan `backend/` y `scripts/`. Lo que haga falta de otras carpetas va en `NOTAS-INTEGRACION.md`.

## 1. Hito 1 (10:15) — corre solo con mocks

- [x] 1.1 Completar `backend/schema.sql` (tablas `vuelos` y `hallazgos`, `CREATE TABLE IF NOT EXISTS`); verificar aplicándolo dos veces con `sqlite3 data/eagle.db < backend/schema.sql` sin errores
- [x] 1.2 Al arrancar `backend/api.py`: crear `data/`, aplicar el schema y abrir un vuelo; verificar con `uv run uvicorn backend.api:app --port 8000` sobre una carpeta `data/` vacía
- [x] 1.3 Implementar `scripts/seed.py` (con `--reset`) validando contra el schema; verificar que carga 6 filas con `sqlite3 data/eagle.db "select count(*) from hallazgos"`
- [x] 1.4 Implementar `GET /hallazgos` (orden descendente, `limit` 1–100); verificar con `curl localhost:8000/hallazgos?limit=3` que la forma coincide con `contracts/fixtures/hallazgos.sample.json`

## 2. Hito 2 (11:00) — se conecta con el contrato real

- [x] 2.1 Implementar `POST /hallazgos` con `jsonschema` Draft7Validator sobre `contracts/hallazgo.schema.json`; verificar 201 con un hallazgo del fixture (sin `id`) y 422 con un campo extra, un enum inválido, `descripcion` de 141 caracteres y sin `costo_usd`
- [x] 2.2 Implementar `GET /estado` (estado de `data/estado.json`, COUNT/SUM del vuelo, `PRESUPUESTO_USD`); verificar que la forma coincide con `contracts/fixtures/estado.sample.json` y que sin `estado.json` devuelve `sin_senal`
- [x] 2.3 Implementar `GET /frames/{archivo}` con protección de rutas; verificar 200 con un frame real, 404 con uno inexistente y 404 con `..`
- [x] 2.4 Verificar CORS: desde `http://localhost:5500/dashboard/` el navegador no muestra errores de CORS
- [x] 2.5 Probar `uv run python agent/main.py --source samples/ --una-vez` contra la API (o un `curl` con el mismo cuerpo); verificar que aparece en `GET /hallazgos` — verificado vía curl con el cuerpo del contrato (201 → aparece primero en GET /hallazgos). Prueba con el agente real de Rulo queda para el Hito 3 (integración), cuando exista `agent/`.

## 3. Hito 3 (11:50) — integración de punta a punta y pulido

- [ ] 3.1 Con grabber + agente + dashboard corriendo, verificar que `frames_analizados` y `costo_usd` suben en `GET /estado` y el dashboard los refleja
- [ ] 3.2 Verificar que `scripts/dev.sh` levanta API y dashboard con un solo comando
- [ ] 3.3 Revisar que la API no se cae si el agente envía basura (422) ni si falta `data/estado.json`
- [ ] 3.4 Verificar contra `contracts/` y actualizar `NOTAS-INTEGRACION.md`
