# Design

## Context

La pantalla se proyecta durante la demo (16:9). Datos con la forma de `contracts/fixtures/estado.sample.json` y `hallazgos.sample.json`. El esqueleto de `dashboard/` ya trae las 4 secciones comentadas, el polling y el cambio de rutas para `?mock=1`.

## Goals / Non-Goals

**Goals:**
- Legible a 3 m: números grandes, semáforo claro, frame protagonista.
- Mismo código para mock y real: solo cambian las URLs.
- La página nunca se rompe: API caída, campos null o lista vacía se muestran como estados.

**Non-Goals:**
- Frameworks, bundlers o npm.
- Responsive para móvil (es una pantalla de demo 16:9).
- Controles para el dron o el agente.

## Decisions

- **Pantalla de inicio + vista en vivo** en la misma página (decisión de Daniela): el inicio es una capa fija con el ojo de águila, el visor que enfoca y el botón "Comenzar"; al pulsarlo la cámara entra al ojo (zoom) y queda la vista en vivo. `#vivo` en la URL salta el inicio. El polling corre desde el principio, así el inicio muestra si la API y el dron están listos.
- **CSS Grid a pantalla completa** (`100vh`, `overflow: hidden`): header arriba; frame ~60% a la izquierda; tarjetas y feed a la derecha. El feed tiene scroll interno si hace falta, la página nunca.
- **Paleta de marca: solo negro, amarillo y azul** (blanco solo para texto y vidrio), decisión de Daniela.
- **Semáforo por `severidad`**, no por el número, dentro de esa paleta: `baja` azul, `media` amarillo en contorno, `alta` amarillo sólido con texto negro y brillo. Así la regla vive en el agente, no se duplica.
- **Modo detectado** = `tipo` del hallazgo más reciente.
- **Estados derivados:**
  - *Sin señal*: `estado_stream == "sin_senal"` → overlay sobre el frame.
  - *Analizando*: en vivo pero el `ultimo_frame` no cambió en el último ciclo, o aún no hay hallazgos.
  - *Presupuesto agotado*: `costo_usd >= presupuesto_usd` → barra y tarjeta de gasto en amarillo y aviso.
  - *Sin conexión*: el `fetch` falla → aviso discreto, se conservan los últimos datos.
  - Campos `null` → "—".
- **Imagen**: `${API_URL}/${ultimo_frame}`; en mock no hay imágenes, se muestra un placeholder. Cambiar el `src` solo cuando cambia la ruta, para evitar parpadeo.
- **Feed**: re-render completo cada ciclo (máximo 20 elementos); los nuevos se resaltan brevemente comparando `id` con el ciclo anterior.
- `?api=<url>` permite apuntar a otra máquina sin tocar el código.

## Risks / Trade-offs

- [Rutas `samples/...` cuando el agente corre con `--source`] → la API solo sirve `data/frames/`; mostrar placeholder si la imagen da 404.
- [Fuentes o íconos externos sin internet en el lugar] → usar fuentes del sistema y emoji/SVG inline.
- [Polling cada 2 s con la API caída llena la consola] → registrar el error una sola vez por racha.
