# Tasks — add-live-dashboard (Daniela)

Solo se edita `dashboard/`. Lo que haga falta de otras carpetas va en `NOTAS-INTEGRACION.md`.
Para verlo: `scripts/dev.sh --solo-web` → http://localhost:5500/dashboard/?mock=1 (no necesita uv).

## 1. Hito 1 (10:15) — corre solo con mocks

- [x] 1.1 Layout en `styles.css`: grid 16:9 a pantalla completa, tema oscuro, sin scroll; verificar a 1920×1080 y 1280×720 que no aparece barra de scroll
- [x] 1.2 Header (logo, estado del stream, modo detectado); verificar con `?mock=1` que muestra "en vivo" y el modo del primer hallazgo del fixture
- [x] 1.3 Tarjetas: personas, % de estrés con semáforo por `severidad`, frames analizados, barra de gasto; verificar con `?mock=1` que la barra marca ~6 % (0.1248 / 2.00) y los null salen como "—"
- [x] 1.4 Feed de hallazgos (hora, tipo, severidad, descripción, recomendación), los nuevos arriba; verificar que salen los 6 del fixture en orden
- [x] 1.5 Frame grande con placeholder cuando no hay imagen; verificar en mock que no aparece el ícono de imagen rota

## 2. Hito 2 (11:00) — se conecta con el contrato real

- [x] 2.1 Probar contra la API de César (`scripts/seed.py --reset` + `uv run uvicorn backend.api:app`); verificar que `/dashboard/` sin `?mock=1` muestra lo mismo que en mock
- [x] 2.2 Imagen real desde `GET /frames/{archivo}`, cambiando el `src` solo si cambia la ruta; verificar que no parpadea en cada ciclo
- [x] 2.3 Estado sin conexión: apagar la API y verificar que aparece el aviso, se conservan los datos y vuelve solo al encender la API
- [x] 2.4 Estados sin señal y presupuesto agotado; verificar editando una copia local del fixture (`estado_stream: "sin_senal"`, `costo_usd: 2.0`)
- [x] 2.5 Estado analizando (en vivo sin hallazgos nuevos); verificar con la base vacía

## 3. Hito 3 (11:50) — integración de punta a punta y pulido

- [ ] 3.1 Con grabber + agente + API corriendo, verificar que un hallazgo nuevo aparece arriba del feed y se resalta en ≤ 2 s
- [ ] 3.2 Pulido visual para proyección: tamaños legibles a 3 m, contraste del semáforo, animación sutil al llegar un hallazgo
- [ ] 3.3 Ensayo de la demo en el proyector o pantalla real
- [ ] 3.4 Verificar contra `contracts/` y actualizar `NOTAS-INTEGRACION.md`
