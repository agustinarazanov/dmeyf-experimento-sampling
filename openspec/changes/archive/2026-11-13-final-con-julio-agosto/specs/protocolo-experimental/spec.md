## ADDED Requirements

### Requirement: Adaptaciones del baseline declaradas
Cada apartamiento del baseline (208135 y su hilo) o de una indicación de un tutor en Zulip SHALL quedar escrito, con el
id del mensaje y el motivo, en `control/docs/hipotesis.md` o en el `docs/diseno.md` que corresponda. Solo los que no son
la variable de una hipótesis ni están justificados en el diseño SHALL figurar entre las limitaciones de los informes y
del guion.

#### Scenario: Apartamiento que es la hipótesis
- **WHEN** se lee por qué `H3` no reoptimiza para el dataset del final, frente al "siempre OP" (211718)
- **THEN** `h3/docs/diseno.md` lo explica con el id 211718 (reoptimizar con todo convertiría a `H3` en el control), y
  § Limitaciones no lo lista

#### Scenario: Apartamiento que se convierte en variante
- **WHEN** el diseño de `h4` cita 211718 para `H4F`
- **THEN** remite a `H4O-0.5`, que optimiza sobre el mismo set con el que entrena, y el contraste entre las dos sale en
  el informe de `h4` como resultado, no como limitación

#### Scenario: Aclaración nueva en Zulip
- **WHEN** aparece en Zulip una aclaración del baseline que el repo no cumple
- **THEN** la bitácora de `sampling_1` la anota con su id y, hasta que se corrija, se justifique en el diseño o se declare
  como limitación, la revisión de la etapa informe (`docs/revision.md` § 5) tiene un ✗ abierto
