# Tasks — add-stream-ingest (César)

Solo se editan `ingest/` y `scripts/`. Lo que haga falta de otras carpetas va en `NOTAS-INTEGRACION.md`.

## 1. Hito 1 (10:15) — corre solo con mocks

- [x] 1.1 Instalar MediaMTX (`brew install mediamtx`) y arrancar con `mediamtx ingest/mediamtx.yml`; verificar que escucha en `:1935` (`nc -z localhost 1935`)
- [x] 1.2 Poner un video de prueba en `samples/` y correr `scripts/replay.sh samples/<video>.mp4`; verificar que MediaMTX registra la publicación en `live/dron`
- [x] 1.3 Implementar `redimensionar` y `guardar_frame` en `ingest/grabber.py`; verificar con un frame suelto que el JPG queda con lado mayor 1024 px
- [x] 1.4 Implementar `siguiente_numero`; verificar que tras reiniciar el grabber no se sobrescriben frames
- [x] 1.5 Implementar el `loop` con intervalo configurable; verificar con `replay.sh` que aparecen `data/frames/NNNN.jpg` cada ~4 s y con `--intervalo 2` cada ~2 s

## 2. Hito 2 (11:00) — se conecta con el contrato real

- [x] 2.1 Escritura atómica de `data/frames/latest.jpg` (temporal + `os.replace`); verificar abriendo `latest.jpg` en bucle mientras corre el grabber sin errores de JPG truncado
- [x] 2.2 Implementar `escribir_estado` con `estado_stream` y `ultimo_frame_ts` (ISO 8601); verificar que `data/estado.json` coincide con `contracts/api.md`
- [x] 2.3 Paso a `sin_senal`: cortar `replay.sh` y verificar que `estado.json` cambia en ≤ 10 s y el grabber sigue vivo
- [x] 2.4 Reconexión: volver a lanzar `replay.sh` y verificar que el estado vuelve a `en_vivo` sin reiniciar el grabber
- [ ] 2.5 Probar con el dron real: DJI Fly → RTMP a la IP del portátil; anotar en `ingest/README.md` la IP/red usada y la latencia observada — BLOQUEADA: requiere el dron físico. El pipeline quedó validado con replay.sh (plan B), que alimenta el mismo RTMP.

## 3. Hito 3 (11:50) — integración de punta a punta y pulido

- [ ] 3.1 Con el agente corriendo en vivo, verificar que lee `latest.jpg` y que `imagen` del hallazgo apunta a un `frames/NNNN.jpg` existente — BLOQUEADA: requiere el agente de Rulo. `latest.jpg` quedó verificado (lectura concurrente sin truncar).
- [ ] 3.2 Verificar que el dashboard muestra "sin señal" al cortar el stream y vuelve a "en vivo" al reanudarlo — BLOQUEADA: requiere el dashboard de Daniela. La transición en `estado.json` (≤ 10 s) quedó verificada.
- [x] 3.3 Ensayar el plan B completo (dron apagado, `replay.sh` en bucle) durante 2 minutos sin intervención
- [x] 3.4 Verificar contra `contracts/` y actualizar `NOTAS-INTEGRACION.md`
