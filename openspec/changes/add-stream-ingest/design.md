# Design

## Context

DJI Fly solo publica RTMP. El portátil corre MediaMTX como servidor y el grabber lee de `rtmp://localhost:1935/live/dron`. El agente cuesta dinero por imagen, así que los frames se reducen a 1024 px y se guardan cada pocos segundos, no a 30 fps. Interfaces fijadas en `contracts/api.md` → "Interfaces de archivo".

## Goals / Non-Goals

**Goals:**
- Frames en disco con nombres crecientes y un `latest.jpg` que nunca se lee a medio escribir.
- Estado del stream fiable en ≤ 10 s.
- Grabber que sobrevive a cortes del stream sin reiniciarlo a mano.
- Plan B que alimenta el mismo RTMP.

**Non-Goals:**
- Analizar los frames (es del agente).
- Guardar video ni audio.
- Servir los frames por HTTP (es de la API).

## Decisions

- **MediaMTX** como servidor RTMP: un binario, sin dependencias, config en YAML (`ingest/mediamtx.yml`). Alternativa: nginx-rtmp, descartada por ser más pesada de instalar en macOS.
- **OpenCV `VideoCapture(url)`** con backend FFmpeg para leer el RTMP. Se lee continuamente y se guarda solo 1 de cada N s para que el buffer no acumule retraso.
- **Escritura atómica** de `latest.jpg` y `estado.json`: escribir a `*.tmp` y `os.replace`. Evita que el agente lea un JPG cortado.
- **Numeración** `NNNN.jpg` continúa desde el último archivo existente, para no pisar frames si el grabber se reinicia.
- **Reconexión**: si `read()` falla, liberar la captura y reintentar cada 2 s; mientras tanto seguir escribiendo `estado.json` (que pasará a `sin_senal` a los 10 s).
- **Intervalo**: `--intervalo` o `INTERVALO_GRABBER_S` (por defecto 4 s).

## Risks / Trade-offs

- [Latencia de DJI Fly de 2–5 s] → aceptable; el intervalo de análisis es de 5 s.
- [OpenCV sin soporte RTMP en algún entorno] → probar en el Hito 1 con `replay.sh`; si falla, leer con un subproceso de `ffmpeg` que escriba JPGs.
- [Celular y portátil en redes distintas] → documentado en `ingest/README.md`; usar el hotspot del portátil.
- Dependencia con otros frentes: ninguna. Lo que necesite de `agent/` o `dashboard/` va en `NOTAS-INTEGRACION.md`.
