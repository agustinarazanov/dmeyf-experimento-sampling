# registro-tokens Specification

## Purpose
Define cómo se mide el consumo de Claude Code por sesión y etapa del experimento, y contra qué línea de base se
compara, para evaluar el método de trabajo con pocos tokens.

## Requirements

### Requirement: Una sesión por etapa, registrada
Cada sesión de Claude Code del repo SHALL corresponder a un experimento y a una etapa declarada (hipótesis, diseño,
código, corridas, análisis, informe, revisión) y SHALL quedar en el `ledger/tokens.csv` de ese experimento con fecha, etapa, modelo, turnos, tokens de salida,
tokens leídos de caché, contexto promedio por turno y costo equivalente a precio de API.

#### Scenario: Sesión sin etapa
- **WHEN** el registro encuentra una sesión del repo sin etapa asignada en la bitácora
- **THEN** la lista como `sin-etapa` para que se clasifique a mano

### Requirement: Cálculo desde los transcripts locales
El registro SHALL calcularse desde los transcripts de Claude Code del repo en `~/.claude/projects/`, sin enviar nada a
servicios externos, y SHALL ser idempotente.

#### Scenario: Ejecutar dos veces
- **WHEN** se corre el registro dos veces sin sesiones nuevas
- **THEN** el CSV no cambia

### Requirement: Costo por sesión headless
Cada sesión lanzada por `scripts/etapa.sh` SHALL dejar su salida JSON en `ledger/sesiones/` y una fila en
`ledger/sesiones/costos.csv` con fecha, grupo, rol (aplicar o revisar), modelo, turnos, costo en dólares, id de sesión y
resultado, y el registro de tokens SHALL usar ese costo cuando exista en lugar de estimarlo desde el transcript.

#### Scenario: Etapa corrida con el script
- **WHEN** `scripts/etapa.sh` termina un grupo
- **THEN** `costos.csv` tiene dos filas nuevas (aplicar y revisar) con costo mayor que cero y la bitácora cita ese costo

#### Scenario: Sesión cortada por presupuesto
- **WHEN** una sesión alcanza el tope en dólares
- **THEN** la fila queda con el resultado que devuelve el JSON y el grupo no se marca como cerrado

### Requirement: Comparación contra la línea de base
El registro SHALL mostrar junto a cada etapa la línea de base de octubre (contexto promedio ~400.000 tokens por turno,
costo equivalente ~US$ 694 por 2.509 turnos) y el objetivo del proyecto (contexto promedio menor a 100.000 tokens por
turno).

#### Scenario: Etapa que supera el objetivo
- **WHEN** una etapa cierra con contexto promedio mayor al objetivo
- **THEN** el resumen la marca y la bitácora anota qué la infló
