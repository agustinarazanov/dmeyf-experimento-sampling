# Spec Delta

## Purpose

Define cómo se mide el consumo de Claude Code por sesión y etapa del experimento, y contra qué línea de base se
compara, para evaluar el método de trabajo con pocos tokens.

## ADDED Requirements

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

### Requirement: Comparación contra la línea de base
El registro SHALL mostrar junto a cada etapa la línea de base de octubre (contexto promedio ~400.000 tokens por turno,
costo equivalente ~US$ 694 por 2.509 turnos) y el objetivo del proyecto (contexto promedio menor a 100.000 tokens por
turno).

#### Scenario: Etapa que supera el objetivo
- **WHEN** una etapa cierra con contexto promedio mayor al objetivo
- **THEN** el resumen la marca y la bitácora anota qué la infló
