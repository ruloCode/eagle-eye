# Proposal

## Why

Es lo que ve el público en la demo: una pantalla que, de un vistazo, diga qué está viendo el dron, si hay algo urgente y cuánto lleva gastado el agente. Debe poder construirse sin el backend (mocks) y sin herramientas de build, para iterar rápido el día del workshop.

## What Changes

- Una sola página 16:9, tema oscuro, sin scroll, en `dashboard/` (HTML/CSS/JS sin build ni npm).
- Cuatro secciones: (1) header con logo, estado del stream y modo detectado; (2) frame actual grande (~60%); (3) tarjetas: personas, % de estrés con semáforo según severidad, frames analizados, barra de gasto vs. presupuesto; (4) feed de hallazgos, los nuevos arriba.
- Estados visibles: sin señal, analizando, presupuesto agotado, sin conexión con la API y tarjetas con campos null.
- Polling cada 2 s a `GET /estado` y `GET /hallazgos`; modo `?mock=1` con `contracts/fixtures/*.json`.

## Capabilities

### New Capabilities
- `dashboard-vivo`: visualización en vivo del estado del dron, del último frame, de los indicadores y del feed de hallazgos.

### Modified Capabilities

## Impact

- Carpeta de Daniela: `dashboard/` (`index.html`, `styles.css`, `app.js`).
- Consume `GET /estado`, `GET /hallazgos` y `GET /frames/{archivo}` de la API; en mock, `contracts/fixtures/`.
- Se sirve desde la raíz del repo en `:5500` (`scripts/dev.sh --solo-web`).
