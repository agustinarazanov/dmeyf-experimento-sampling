# Spec Delta

## MODIFIED Requirements

### Requirement: Una sesión por etapa, registrada
Cada sesión de Claude Code del repo SHALL corresponder a un experimento y a una etapa declarada (hipótesis, diseño,
código, corridas, análisis, informe, revisión) y SHALL quedar en el `ledger/tokens.csv` de ese experimento con fecha,
etapa, modelo, turnos, tokens de salida, tokens leídos de caché, contexto promedio por turno y costo equivalente a
precio de API. Una sesión SHALL pertenecer al experimento cuya bitácora (o cuyo `ledger/sesiones/costos.csv`) la
declara, y SHALL aparecer en un solo `tokens.csv`.

#### Scenario: Sesión sin etapa
- **WHEN** el registro encuentra una sesión del repo que no declara la bitácora de ningún experimento
- **THEN** la lista como `sin-etapa` en el `tokens.csv` de `conjunto` para que se clasifique a mano

#### Scenario: Sesiones anteriores a la separación
- **WHEN** se corre el registro después de separar `sampling-velocidad`
- **THEN** las sesiones ya registradas quedan en `experimentos/conjunto/ledger/tokens.csv` con la misma etapa y el
  mismo costo que tenían

#### Scenario: Sesión declarada en dos bitácoras
- **WHEN** dos experimentos declaran la misma sesión
- **THEN** el registro falla y nombra la sesión y los dos experimentos
