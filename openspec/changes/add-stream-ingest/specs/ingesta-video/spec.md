## Purpose

Recibir el video RTMP del dron, convertirlo en frames JPG periódicos y exponer el estado del stream para el agente, la API y el dashboard, con un plan B de retransmisión.

## ADDED Requirements

### Requirement: Recepción RTMP

El sistema SHALL aceptar un stream RTMP publicado en `rtmp://<host>:1935/live/dron`.

#### Scenario: DJI Fly publica

- **WHEN** DJI Fly publica en `rtmp://<IP-del-portátil>:1935/live/dron`
- **THEN** el servidor acepta la publicación y el stream queda disponible para el grabber

### Requirement: Extracción periódica de frames

El grabber SHALL guardar un frame cada N segundos (configurable, por defecto 4) en `data/frames/NNNN.jpg`, con numeración creciente de 4 dígitos y el lado mayor a 1024 px.

#### Scenario: Llega el stream

- **WHEN** hay un stream activo durante 20 segundos con el intervalo por defecto
- **THEN** aparecen al menos 4 archivos nuevos `data/frames/NNNN.jpg` cuyo lado mayor mide 1024 px

#### Scenario: Intervalo configurado

- **WHEN** se arranca el grabber con un intervalo de 2 segundos
- **THEN** los frames nuevos aparecen aproximadamente cada 2 segundos

#### Scenario: Reinicio del grabber

- **WHEN** el grabber se reinicia y ya existe `data/frames/0040.jpg`
- **THEN** el siguiente frame se guarda como `0041.jpg` o superior, sin sobrescribir los anteriores

### Requirement: Último frame disponible

El grabber SHALL mantener `data/frames/latest.jpg` como copia del último frame guardado, reemplazándolo de forma que nunca se lea un archivo incompleto.

#### Scenario: Lectura concurrente

- **WHEN** el agente lee `latest.jpg` mientras el grabber guarda un frame nuevo
- **THEN** el agente obtiene una imagen JPG completa, sea la anterior o la nueva

### Requirement: Estado del stream

El grabber SHALL escribir `data/estado.json` con `estado_stream` (`en_vivo` o `sin_senal`) y `ultimo_frame_ts` en ISO 8601. El estado MUST pasar a `sin_senal` cuando pasen más de 10 segundos sin frames nuevos.

#### Scenario: Stream activo

- **WHEN** se guardó un frame hace menos de 10 segundos
- **THEN** `estado.json` tiene `estado_stream` igual a `en_vivo`

#### Scenario: Se corta el stream

- **WHEN** el stream se interrumpe
- **THEN** en máximo 10 segundos `estado.json` tiene `estado_stream` igual a `sin_senal` y el grabber sigue corriendo

#### Scenario: Vuelve el stream

- **WHEN** el stream vuelve después de un corte
- **THEN** el grabber reanuda la captura sin reiniciarlo a mano y el estado vuelve a `en_vivo`

### Requirement: Plan B de retransmisión

El sistema SHALL ofrecer un comando que retransmita un video grabado al mismo endpoint RTMP, de modo que el resto del pipeline funcione sin cambios.

#### Scenario: Sin dron

- **WHEN** se ejecuta `scripts/replay.sh samples/vuelo.mp4` con MediaMTX corriendo
- **THEN** el grabber produce frames igual que con el dron real

#### Scenario: Video inexistente

- **WHEN** se ejecuta `scripts/replay.sh` con una ruta que no existe
- **THEN** el comando termina con un mensaje de error y código distinto de cero
