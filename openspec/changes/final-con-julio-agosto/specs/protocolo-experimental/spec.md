## ADDED Requirements

### Requirement: Adaptaciones del baseline declaradas
Cada apartamiento del baseline (208135 y las aclaraciones de su hilo) o de una indicación de un tutor en Zulip SHALL
quedar escrito en `control/docs/hipotesis.md` o en el `docs/diseno.md` que corresponda, con el id del mensaje y el motivo,
y SHALL figurar entre las limitaciones del informe de `sampling_1`, del guion y del informe de cada hipótesis afectada.

#### Scenario: Adaptaciones vigentes
- **WHEN** se lee `experimentos/sampling_1/informe/informe.md` § Limitaciones
- **THEN** aparecen, cada una con su id de Zulip: la decisión por ganancia en test al corte N\* frente a "métrica auc"
  (208135); `H3` y `H4F` sin reoptimizar para el dataset del final frente al "siempre OP" (211718); y los
  hiperparámetros elegidos con cuatro meses usados en un final de seis (211210)

#### Scenario: Aclaración nueva en Zulip
- **WHEN** aparece en Zulip una aclaración del baseline que el repo no cumple
- **THEN** la bitácora de `sampling_1` la anota con su id y, hasta que se corrija o se declare como limitación, la
  revisión de la etapa informe (`docs/revision.md` § 5) tiene un ✗ abierto
