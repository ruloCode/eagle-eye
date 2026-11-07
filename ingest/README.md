# ingest/ — César

Recibe el video del dron y lo convierte en frames para el agente.

```
DJI Fly ──RTMP──▶ MediaMTX :1935 /live/dron ──▶ grabber.py ──▶ data/frames/NNNN.jpg + latest.jpg + data/estado.json
```

1. `mediamtx ingest/mediamtx.yml`
2. En DJI Fly: *Transmisión en vivo → RTMP* → `rtmp://<IP-del-portátil>:1935/live/dron` (celular y portátil en la misma red).
3. `uv run python ingest/grabber.py`

Sin dron (plan B): `scripts/replay.sh samples/<video>.mp4` publica en la misma URL.

Spec: `openspec/changes/add-stream-ingest/`.
