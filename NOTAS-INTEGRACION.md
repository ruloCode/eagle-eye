# Notas de integración

Aquí se deja todo lo que un frente necesita de **otra carpeta** o de `contracts/`, en vez de editarla directamente.
El dueño de la carpeta lee estas notas, decide y responde. Las más nuevas arriba.

## Plantilla

```markdown
### [AAAA-MM-DD HH:MM] <de> → <para> — <título corto>
- **Estado:** abierta | en curso | resuelta | descartada
- **Carpeta / archivo:** <p. ej. backend/api.py, contracts/api.md>
- **Qué necesito:** <una o dos frases>
- **Por qué:** <qué se rompe o qué no puedo hacer sin esto>
- **Propuesta:** <cambio concreto, ejemplo de JSON, etc.>
- **Respuesta:** <la escribe el dueño>
```

Si la nota toca `contracts/`, se resuelve entre los tres y el cambio va en un commit aparte con prefijo `contract:`.

---

## Notas

<!-- Escribe la primera nota debajo de esta línea -->

### [2026-11-07 10:57] César → todos — Ignorar auto.crt / auto.key de MediaMTX
- **Estado:** abierta
- **Carpeta / archivo:** `.gitignore` (raíz, compartido)
- **Qué necesito:** agregar `auto.crt` y `auto.key` al `.gitignore`.
- **Por qué:** MediaMTX genera esos certificados autofirmados en la raíz al arrancar (aun con TLS apagado). No deben ir a git y hoy aparecen como untracked al correr la ingesta.
- **Propuesta:** añadir dos líneas al `.gitignore`:
  ```
  auto.crt
  auto.key
  ```
- **Respuesta:** <la escribe quien corresponda>
