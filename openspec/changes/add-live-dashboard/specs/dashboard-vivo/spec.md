## Purpose

Mostrar en una sola pantalla, en vivo, qué ve el dron, qué encontró el agente, si hay algo urgente y cuánto presupuesto lleva gastado, tanto con la API real como con datos de prueba.

## ADDED Requirements

### Requirement: Pantalla única 16:9

El dashboard SHALL ser una sola página con tema oscuro que ocupa la ventana completa en 16:9 sin scroll de página.

#### Scenario: Proyección en 1920×1080

- **WHEN** se abre el dashboard en una ventana de 1920×1080
- **THEN** las cuatro secciones se ven completas y la página no tiene barra de scroll

### Requirement: Header con estado

El header SHALL mostrar el logo de Eagle Eye, el estado del stream (en vivo o sin señal) y el modo detectado (cultivo o personas) según el hallazgo más reciente.

#### Scenario: Stream en vivo con cultivo

- **WHEN** `estado_stream` es `en_vivo` y el último hallazgo es de tipo `cultivo`
- **THEN** el header indica "en vivo" y modo cultivo

### Requirement: Frame actual

El dashboard SHALL mostrar el frame del último hallazgo en grande, ocupando cerca del 60% del ancho.

#### Scenario: Frame nuevo

- **WHEN** `ultimo_frame` cambia en `GET /estado`
- **THEN** la imagen grande se actualiza en el siguiente ciclo

#### Scenario: Imagen no disponible

- **WHEN** la imagen del frame no se puede cargar
- **THEN** se muestra un placeholder en vez de una imagen rota

### Requirement: Tarjetas de indicadores

El dashboard SHALL mostrar tarjetas con personas, % de estrés, frames analizados y una barra de gasto frente al presupuesto. La tarjeta de estrés MUST colorearse según `severidad` usando solo la paleta de marca (negro, amarillo y azul): baja azul, media amarillo en contorno, alta amarillo sólido con texto negro.

#### Scenario: Cultivo con severidad alta

- **WHEN** el último hallazgo es de cultivo con `pct_estres` 37.4 y `severidad` `alta`
- **THEN** la tarjeta de estrés muestra 37.4 % en amarillo sólido (nivel alta)

#### Scenario: Campos null

- **WHEN** el último hallazgo es de personas y `pct_estres` es null
- **THEN** la tarjeta de estrés muestra "—" sin error

#### Scenario: Barra de gasto

- **WHEN** `costo_usd` es 0.50 y `presupuesto_usd` es 2.00
- **THEN** la barra de gasto se ve al 25 %

### Requirement: Feed de hallazgos

El dashboard SHALL listar los hallazgos recientes con los nuevos arriba, mostrando hora, tipo, severidad, descripción y recomendación.

#### Scenario: Llega un hallazgo

- **WHEN** aparece un hallazgo nuevo en `GET /hallazgos`
- **THEN** se muestra primero en el feed en el siguiente ciclo

### Requirement: Estados del sistema

El dashboard SHALL mostrar de forma visible los estados sin señal, analizando, presupuesto agotado y sin conexión con la API, sin dejar de funcionar.

#### Scenario: Sin señal

- **WHEN** `estado_stream` es `sin_senal`
- **THEN** se muestra un aviso "Sin señal" sobre el frame

#### Scenario: Presupuesto agotado

- **WHEN** `costo_usd` es mayor o igual a `presupuesto_usd`
- **THEN** se muestra un aviso de presupuesto agotado

#### Scenario: API caída

- **WHEN** las peticiones a la API fallan
- **THEN** se muestra un aviso de sin conexión, se conservan los últimos datos y el polling continúa

### Requirement: Polling y modo mock

El dashboard SHALL consultar `GET /estado` y `GET /hallazgos` cada 2 segundos. Con `?mock=1` SHALL leer `contracts/fixtures/estado.sample.json` y `contracts/fixtures/hallazgos.sample.json` en vez de la API.

#### Scenario: Modo mock

- **WHEN** se abre `/dashboard/?mock=1` sin la API corriendo
- **THEN** el dashboard muestra los 6 hallazgos de prueba y el estado de prueba sin errores

#### Scenario: Modo real

- **WHEN** se abre `/dashboard/` con la API corriendo
- **THEN** el dashboard hace una consulta a cada endpoint cada 2 segundos
