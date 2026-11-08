## ADDED Requirements

### Requirement: Se lee del dueño de la variante o del estudio, no se copia
Un resultado que pertenece a otro experimento SHALL leerse de su ledger, a través del registro de variantes y estudios. No
SHALL copiarse al ledger propio. Cada variante y cada estudio SHALL tener un único experimento dueño, que es el que lo
corre y lo guarda.

#### Scenario: Final de H3
- **WHEN** se corre un final de `H3-0.25`
- **THEN** los hiperparámetros se leen de `experimentos/h1/ledger/hp/U0.25.json` y la fila se escribe en
  `experimentos/h3/ledger/`

#### Scenario: Variante sin dueño
- **WHEN** se pide correr o reportar una variante que no está en el registro
- **THEN** el comando falla antes de cargar datos y nombra la variante

## REMOVED Requirements

### Requirement: Se lee del dueño, no se copia
**Reason**: renombre de "brazo" a "variante"; un escenario cambia de nombre y MODIFIED no lo permite.
**Migration**: reemplazada por "Se lee del dueño de la variante o del estudio, no se copia", con el mismo contenido y "variante" en lugar de "brazo".
