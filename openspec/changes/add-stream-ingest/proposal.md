# Proposal

## Why

El agente necesita imágenes recientes del dron sin depender de la app DJI Fly ni del ritmo del video. La ingesta convierte el stream RTMP en archivos JPG pequeños y un estado del stream que la API y el dashboard pueden leer. Si DJI Fly no conecta el día del workshop, necesitamos un plan B que no cambie el resto del pipeline.

## What Changes

- Configuración de MediaMTX que recibe RTMP en `:1935/live/dron`.
- Grabber con OpenCV que guarda 1 frame cada N segundos (configurable, por defecto 4) en `data/frames/NNNN.jpg`, con el lado mayor a 1024 px.
- `data/frames/latest.jpg` siempre apunta al último frame (escritura atómica).
- `data/estado.json` con `estado_stream` (`en_vivo` / `sin_senal`) y `ultimo_frame_ts`; pasa a `sin_senal` si llevan más de 10 s sin frames.
- `scripts/replay.sh` (ya escrito en el scaffold) como plan B: retransmite un video al mismo RTMP.

## Capabilities

### New Capabilities
- `ingesta-video`: recepción del stream RTMP del dron, extracción periódica de frames, estado del stream y plan B de retransmisión.

### Modified Capabilities

## Impact

- Carpetas de César: `ingest/` (`mediamtx.yml`, `grabber.py`) y `scripts/replay.sh`.
- Produce las interfaces de archivo de `contracts/api.md` que consumen el agente (`latest.jpg`) y la API (`frames/`, `estado.json`).
- Dependencias: MediaMTX (binario), ffmpeg (plan B), `opencv-python`, `python-dotenv`.
