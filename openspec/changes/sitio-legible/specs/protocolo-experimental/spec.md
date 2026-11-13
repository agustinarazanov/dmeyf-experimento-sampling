# Spec Delta

## MODIFIED Requirements

### Requirement: Un experimento, una carpeta
Cada experimento SHALL vivir en `experimentos/<nombre>/` con la misma estructura: un `README.md` con la hipótesis, el
diseño, los resultados y las conclusiones; `docs/bitacora.md`; `ledger/`; `figuras/` con las figuras generadas; y
`scripts/` o `src/` solo si los necesita. El nombre SHALL ser un identificador válido de Python (`h1`, no `h-1`).
Además de `comun/` y de su propia carpeta, SHALL depender solo de los experimentos que declara (ver
`dependencias-entre-experimentos`). El código compartido (datos, baseline, ganancia, ledger, tokens, corredor, métodos,
consolidación, reporte) SHALL vivir en `comun/`.

#### Scenario: Agregar un experimento nuevo
- **WHEN** un integrante copia `plantilla/` a `experimentos/<nombre>/`, completa las secciones Idea, Predicción y
  Diseño de su `README.md` y registra sus variantes
- **THEN** el experimento aparece en el README del repo y sus corridas se registran en su propio `ledger/`. Ningún
  archivo de otro experimento cambia, salvo el registro de variantes en `comun/`

#### Scenario: Cambio en código común
- **WHEN** se modifica algo en `comun/`
- **THEN** el commit lo dice en el mensaje y cada experimento activo anota en su bitácora si lo afecta

### Requirement: Hipótesis escritas antes de ejecutar
El experimento SHALL tener en su `README.md`, antes de la primera corrida real, la pregunta y cada hipótesis con su
predicción cuantitativa y su regla de decisión (qué resultado la confirma y cuál la refuta), en la sección Predicción.
También SHALL tener el baseline de control sin modificar salvo la variable experimental. La sección Predicción SHALL NOT
cambiar después de la primera corrida real. Cualquier cambio posterior se anota en la bitácora, y el historial de git de
la sección prueba la fecha.

#### Scenario: Corrida sin hipótesis aprobada
- **WHEN** se intenta registrar una corrida real en el ledger y la sección Predicción del `README.md` no tiene la etapa
  marcada como revisada en `docs/bitacora.md`
- **THEN** la corrida se considera exploratoria y se registra con `etapa = exploracion`, no como evidencia

#### Scenario: Hipótesis con regla de decisión
- **WHEN** se lee cualquier hipótesis del README
- **THEN** se encuentra una predicción con umbral numérico y la métrica que la decide (por ejemplo, "la ganancia media
  apareada en 201910 no cae más que un desvío entre semillas")

#### Scenario: Probar que la predicción es previa
- **WHEN** alguien quiere saber si la predicción de H1 se escribió antes de correr
- **THEN** la sección Predicción indica la fecha y el commit en que quedó fijada, anterior a la primera fila real del
  ledger de `h1`

### Requirement: Diseño experimental explícito
El diseño SHALL fijar, en la sección Diseño del `README.md`, la grilla completa (métodos, tasas, semillas, trials de
optimización), las métricas, el procedimiento de comparación apareada por semilla y el tipo de máquina. El reparto de
corridas SHALL describirse por máquina y por fase, no por persona.

#### Scenario: Grilla reproducible por cualquier integrante
- **WHEN** un integrante lee la sección Diseño y el ledger
- **THEN** puede identificar qué configuraciones faltan y lanzarlas con el corredor sin consultar a nadie

### Requirement: Comunicación con el tutor desde los documentos
El post al tópico `sampling_1` y cualquier respuesta posterior SHALL derivarse de las secciones Predicción y Diseño de
los `README.md`, y las devoluciones del curso SHALL volcarse en la bitácora con la fecha y el id del mensaje de Zulip.

#### Scenario: Devolución del tutor
- **WHEN** una devolución en Zulip pide un cambio en el diseño
- **THEN** se actualiza la sección Diseño, se anota en la bitácora y, si cambia la grilla, se marcan las corridas
  previas como de la versión anterior

### Requirement: El control es un experimento
El control (`C`) y su réplica (`C-rep`) SHALL vivir en `experimentos/control/`, con las reglas comunes de decisión (G,
Δ, δ, T, A, N*, veredictos) en su `README.md`. Las hipótesis SHALL enlazar esas reglas en lugar de repetirlas. Cambiar
una regla común SHALL anotarse en la bitácora de `control` y en la de cada experimento que depende de él.

#### Scenario: Leer la regla de decisión de H2
- **WHEN** se abre `experimentos/h2/README.md`
- **THEN** encuentra su variable, su predicción y su regla de confirmación, y para δ y los veredictos hay un enlace a
  `experimentos/control/README.md`

### Requirement: Ideas que vienen de mirar el test
Una variante que se registra a partir de un resultado ya visto en 201910 SHALL declararlo en la sección Predicción de su
`README.md`, y las Limitaciones de su experimento y de Resultados SHALL listarla. Su predicción y su regla se escriben
igual que las demás, antes de correr.

#### Scenario: H4 viene del aporte de Luis
- **WHEN** se lee `experimentos/h4/README.md`
- **THEN** dice que las variantes salieron de estrategias elegidas mirando 201910, y que el resultado de H4 no cuenta con
  un mes de test que no se haya mirado

### Requirement: Adaptaciones del baseline declaradas
Cada apartamiento del baseline (208135 y su hilo) o de una indicación del curso en Zulip SHALL quedar escrito, con el
id del mensaje y el motivo, en `control/README.md` o en la sección Diseño que corresponda. Solo los que no son la
variable de una hipótesis ni están justificados en el diseño SHALL figurar entre las limitaciones de los README y del
guion.

#### Scenario: Apartamiento que es la hipótesis
- **WHEN** se lee por qué `H3` no reoptimiza para el dataset del final, frente al "siempre OP" (211718)
- **THEN** la sección Diseño de `h3/README.md` lo explica con el id 211718 (reoptimizar con todo convertiría a `H3` en
  el control), y § Limitaciones no lo lista

#### Scenario: Apartamiento que se convierte en variante
- **WHEN** la sección Diseño de `h4` cita 211718 para `H4F`
- **THEN** remite a `H4O-0.5`, que optimiza sobre el mismo set con el que entrena, y el contraste entre las dos sale en
  el README de `h4` como resultado, no como limitación

#### Scenario: Aclaración nueva en Zulip
- **WHEN** aparece en Zulip una aclaración del baseline que el repo no cumple
- **THEN** la bitácora de `sampling_1` la anota con su id y, hasta que se corrija, se justifique en el diseño o se declare
  como limitación, la revisión de la etapa informe (`docs/revision.md` § 5) tiene un ✗ abierto
