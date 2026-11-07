# contrato-hallazgo Specification

## Purpose

Verdad compartida de Eagle Eye: define el formato del hallazgo que el agente produce por cada frame, la prohibición de identificar personas y el control de presupuesto. La API y el dashboard dependen de este contrato; solo cambia con acuerdo de los tres dueños.

## Requirements

### Requirement: Formato del hallazgo

Todo hallazgo SHALL cumplir `contracts/hallazgo.schema.json` (JSON Schema draft-07): los ocho campos `hora`, `imagen`, `tipo`, `severidad`, `personas`, `pct_estres`, `descripcion` y `recomendacion` son obligatorios y no se admiten campos extra.

#### Scenario: Hallazgo completo es válido

- **WHEN** un hallazgo trae los ocho campos con tipos y rangos correctos
- **THEN** la validación contra el schema pasa

#### Scenario: Campo extra es rechazado

- **WHEN** un hallazgo trae un campo que no está en el schema, por ejemplo `confianza`
- **THEN** la validación falla

#### Scenario: Campo faltante es rechazado

- **WHEN** un hallazgo omite `pct_estres` en vez de enviarlo en null
- **THEN** la validación falla

### Requirement: Restricciones de valores

El hallazgo SHALL usar `hora` en formato HH:MM:SS, `tipo` en {`cultivo`, `personas`}, `severidad` en {`baja`, `media`, `alta`}, `pct_estres` entre 0 y 100, `personas` entero ≥ 0, `descripcion` de máximo 140 caracteres y `recomendacion` de máximo 80.

#### Scenario: Descripción demasiado larga

- **WHEN** `descripcion` tiene 141 caracteres
- **THEN** la validación falla

#### Scenario: Severidad fuera del enum

- **WHEN** `severidad` es `critica`
- **THEN** la validación falla

### Requirement: Campos según el tipo

Un hallazgo de tipo `cultivo` SHALL traer `pct_estres` numérico y `personas` en null; uno de tipo `personas` SHALL traer `personas` entero y `pct_estres` en null.

#### Scenario: Cultivo con pct_estres

- **WHEN** `tipo` es `cultivo`, `pct_estres` es 14.8 y `personas` es null
- **THEN** la validación pasa

#### Scenario: Personas con pct_estres

- **WHEN** `tipo` es `personas` y `pct_estres` no es null
- **THEN** la validación falla

### Requirement: Prohibición de reconocimiento facial

El sistema SHALL limitarse a contar personas. Ningún componente MUST realizar reconocimiento facial, identificar individuos ni describir rasgos que permitan reconocer a alguien.

#### Scenario: Frame con personas

- **WHEN** el agente analiza un frame con gente
- **THEN** el hallazgo solo contiene el conteo y una descripción de la distribución, sin rasgos, rostros ni datos identificables

#### Scenario: Petición de identificar

- **WHEN** alguien pide al sistema reconocer o seguir a una persona concreta
- **THEN** el sistema no lo hace

### Requirement: Control de presupuesto

Cada consulta del agente SHALL usar `max_turns` ≤ 4 y `max_budget_usd` = 0.05, y la sesión SHALL tener un tope global `PRESUPUESTO_USD` (2.00 por defecto). El costo de cada consulta MUST registrarse como `costo_usd`.

#### Scenario: Se alcanza el tope global

- **WHEN** el gasto acumulado más el costo máximo de una consulta superaría `PRESUPUESTO_USD`
- **THEN** el agente no lanza más consultas y reporta que el presupuesto se agotó

#### Scenario: Costo visible

- **WHEN** el dashboard consulta `GET /estado`
- **THEN** recibe `costo_usd` acumulado y `presupuesto_usd`
