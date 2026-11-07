# samples/

Pon aquí **3–5 fotos aéreas de prueba** (cultivo y personas), en `.jpg` o `.png`.

- Al menos 2 de **cultivo** (idealmente con alguna zona amarilla, hueco o maleza).
- Al menos 2 de **personas** (vista cenital, sin rostros reconocibles).

Las usa el agente en modo `--source samples/` para trabajar sin dron:

```bash
uv run python agent/main.py --source samples/ --dry-run
```

Un video para el plan B (`scripts/replay.sh`) también puede ir aquí, pero los `.mp4`/`.mov` están en `.gitignore`: compártelos por fuera de git.
