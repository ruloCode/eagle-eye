## Purpose

Analizar los frames del dron con un agente de la Claude Agent SDK que usa tools propias y devuelve un hallazgo estructurado de cultivo o de personas, sin identificar a nadie y sin superar el presupuesto.

## ADDED Requirements

### Requirement: Loop de análisis

El agente SHALL analizar el frame más reciente cada 5 segundos, tomándolo de `data/frames/latest.jpg` o, con `--source <carpeta>`, de las imágenes de esa carpeta.

#### Scenario: Modo en vivo

- **WHEN** el agente corre sin `--source` y el grabber está activo
- **THEN** cada 5 segundos analiza el frame más reciente y produce un hallazgo

#### Scenario: Modo fotos locales

- **WHEN** el agente corre con `--source samples/`
- **THEN** analiza las fotos de `samples/` sin necesitar el stream

#### Scenario: Frame repetido

- **WHEN** `latest.jpg` no cambió desde el análisis anterior
- **THEN** el agente no lanza una consulta nueva para ese frame

### Requirement: Tools propias

El agente SHALL exponer a Claude dos tools propias: `ultimo_frame`, que devuelve la ruta, la hora y la imagen del frame, e `indice_vari`, que devuelve `pct_estres` y la ruta de un mapa de calor para una imagen dada.

#### Scenario: Índice VARI

- **WHEN** Claude llama a `indice_vari` con la ruta de un frame de cultivo
- **THEN** recibe un `pct_estres` entre 0 y 100 y la ruta de un mapa de calor que existe en disco

#### Scenario: Sin frame disponible

- **WHEN** Claude llama a `ultimo_frame` y no hay ninguna imagen
- **THEN** la tool devuelve un error explícito y el agente no publica hallazgo

### Requirement: Salida estructurada

Cada análisis exitoso SHALL producir un hallazgo que cumple `contracts/hallazgo.schema.json`, con `hora` e `imagen` tomadas del frame analizado.

#### Scenario: Frame de cultivo

- **WHEN** el agente analiza una foto aérea de un cultivo
- **THEN** el hallazgo es válido, `tipo` es `cultivo`, `pct_estres` viene de `indice_vari` y `personas` es null

#### Scenario: Frame con gente

- **WHEN** el agente analiza una foto aérea con personas
- **THEN** el hallazgo es válido, `tipo` es `personas`, `personas` es el conteo y `pct_estres` es null

#### Scenario: Salida inválida

- **WHEN** la consulta termina sin un resultado estructurado válido
- **THEN** el agente no publica nada para ese frame y continúa con el siguiente

### Requirement: Sin identificación de personas

El agente MUST limitarse a contar personas y SHALL NOT describir rostros, rasgos, ropa distintiva ni ningún dato que permita reconocer a alguien.

#### Scenario: Descripción de un grupo

- **WHEN** el frame muestra un grupo de personas
- **THEN** `descripcion` habla de cantidad y ubicación del grupo, no de individuos

### Requirement: Presupuesto por consulta

Cada consulta SHALL limitarse a 4 turnos como máximo y a USD 0.05 de presupuesto.

#### Scenario: Consulta que excede

- **WHEN** una consulta alcanza el límite de turnos o de presupuesto
- **THEN** se corta, su costo se suma al acumulado y el loop sigue con el siguiente frame

### Requirement: Tope global de sesión

El agente SHALL llevar el costo acumulado de la sesión y MUST detener el loop antes de una consulta que pueda superar `PRESUPUESTO_USD` (2.00 por defecto), informando el gasto final.

#### Scenario: Presupuesto agotado

- **WHEN** el acumulado más USD 0.05 superaría `PRESUPUESTO_USD`
- **THEN** el loop se detiene sin lanzar otra consulta e imprime el gasto y el tope

### Requirement: Publicación con respaldo

El agente SHALL enviar cada hallazgo a `POST /hallazgos` con `costo_usd`; si la API no responde o rechaza el envío, MUST guardarlo como una línea JSON en `data/hallazgos.jsonl`. Con `--dry-run` SHALL imprimirlo en vez de enviarlo.

#### Scenario: API disponible

- **WHEN** la API responde 201
- **THEN** el hallazgo queda registrado con su `costo_usd`

#### Scenario: API caída

- **WHEN** la API no responde
- **THEN** el hallazgo se agrega a `data/hallazgos.jsonl` y el loop continúa

#### Scenario: Dry run

- **WHEN** el agente corre con `--dry-run`
- **THEN** imprime el hallazgo con `costo_usd` y no hace ninguna petición HTTP
