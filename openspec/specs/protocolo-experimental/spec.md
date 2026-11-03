# protocolo-experimental Specification

## Purpose
Define cómo se formula, revisa y documenta cada experimento del repo por etapas del método científico, de modo que cada
decisión quede escrita antes de ejecutarse, cada etapa tenga una revisión que la cierre y cualquier persona pueda agregar
un experimento nuevo sin tocar los existentes.

## Requirements

### Requirement: Un experimento, una carpeta
Cada experimento SHALL vivir en `experimentos/<nombre>/` con la misma estructura (`docs/`, `ledger/`, `informe/`, y
`scripts/` o `src/` solo si los necesita), con un nombre que sea un identificador válido de Python (`h1`, no `h-1`).
Además de `comun/` y de su propia carpeta, SHALL depender solo de los experimentos que declara (ver
`dependencias-entre-experimentos`). El código compartido (datos, baseline, ganancia, ledger, tokens, corredor, métodos,
consolidación, reporte) SHALL vivir en `comun/`.

#### Scenario: Agregar un experimento nuevo
- **WHEN** un integrante copia `plantilla/` a `experimentos/<nombre>/`, completa `docs/hipotesis.md` y registra sus
  brazos
- **THEN** el experimento aparece en el README del repo y sus corridas se registran en su propio `ledger/`. Ningún
  archivo de otro experimento cambia, salvo el registro de brazos en `comun/`

#### Scenario: Cambio en código común
- **WHEN** se modifica algo en `comun/`
- **THEN** el commit lo dice en el mensaje y cada experimento activo anota en su bitácora si lo afecta

### Requirement: Hipótesis escritas antes de ejecutar
El experimento SHALL tener en `docs/hipotesis.md`, antes de la primera corrida real, la pregunta, cada hipótesis con su
predicción cuantitativa y su regla de decisión (qué resultado la confirma y cuál la refuta), y el baseline de control
sin modificar salvo la variable experimental.

#### Scenario: Corrida sin hipótesis aprobada
- **WHEN** se intenta registrar una corrida real en el ledger y `docs/hipotesis.md` no tiene la etapa marcada como
  revisada en `docs/bitacora.md`
- **THEN** la corrida se considera exploratoria y se registra con `etapa = exploracion`, no como evidencia

#### Scenario: Hipótesis con regla de decisión
- **WHEN** se lee cualquier hipótesis del documento
- **THEN** se encuentra una predicción con umbral numérico y la métrica que la decide (por ejemplo, "la ganancia media
  apareada en 201910 no cae más que un desvío entre semillas")

### Requirement: Diseño experimental explícito
El diseño SHALL fijar, en `docs/diseno.md`, la grilla completa (métodos, tasas, semillas, trials de optimización), las
métricas, el procedimiento de comparación apareada por semilla, el tipo de máquina y el reparto de corridas entre las
tres personas.

#### Scenario: Grilla reproducible por cualquier integrante
- **WHEN** un integrante lee `docs/diseno.md` y el ledger
- **THEN** puede identificar qué configuraciones faltan y lanzarlas con el corredor sin consultar a nadie

### Requirement: Revisión que cierra cada etapa
Cada etapa (hipótesis, diseño, código, resultados, informe) SHALL cerrarse con una revisión registrada en
`docs/bitacora.md` que use la lista de `docs/revision.md`, hecha en una sesión limpia (interactiva o la sesión de revisión de `scripts/etapa.sh`) o por otro integrante,
con fecha y hallazgos.

#### Scenario: Etapa cerrada
- **WHEN** la bitácora marca una etapa como revisada
- **THEN** existe una entrada con fecha, quién revisó, qué ítems de la lista se verificaron y qué se corrigió

#### Scenario: Revisión que encuentra un problema
- **WHEN** la revisión de resultados detecta una inconsistencia (por ejemplo, tiempos medidos en máquinas distintas)
- **THEN** las corridas afectadas se marcan como inválidas en el ledger y la etapa no se cierra hasta repetirlas

### Requirement: Lo que necesita a una persona se declara, no se improvisa
Una sesión headless que encuentra una tarea que requiere a una persona (una respuesta del tutor, una decisión de diseño,
un reparto entre personas) SHALL escribir `BLOQUEADO` con el motivo en `ledger/sesiones/bloqueo.txt` y terminar sin marcar la
tarea, y el loop de etapas SHALL detenerse ahí.

#### Scenario: Etapa que necesita una VM
- **WHEN** una tarea requiere una VM
- **THEN** la sesión la usa solo a través del `scripts/vm.sh` del experimento, que la borra al terminar, y verifica
  antes de cerrar que no quedó ninguna VM encendida

#### Scenario: Etapa que necesita al tutor
- **WHEN** una tarea depende de una respuesta del tutor que no llegó
- **THEN** la sesión escribe el bloqueo con el motivo y `scripts/etapa.sh` termina con código 2

### Requirement: Comunicación con el tutor desde los documentos
El post al tópico `sampling_1` y cualquier respuesta posterior SHALL derivarse de `docs/hipotesis.md` y
`docs/diseno.md`, y las devoluciones del tutor SHALL volcarse en la bitácora con la fecha y el id del mensaje de Zulip.

#### Scenario: Devolución del tutor
- **WHEN** el tutor pide un cambio en el diseño
- **THEN** se actualiza el documento, se anota en la bitácora y, si cambia la grilla, se marcan las corridas previas
  como de la versión anterior

### Requirement: El control es un experimento
El control (`C`) y su réplica (`C-rep`) SHALL vivir en `experimentos/control/`, con las reglas comunes de decisión (G,
Δ, δ, T, A, N*, veredictos) en su `docs/hipotesis.md`. Las hipótesis SHALL citar esas reglas en lugar de repetirlas.
Cambiar una regla común SHALL anotarse en la bitácora de `control` y en la de cada experimento que depende de él.

#### Scenario: Leer la regla de decisión de H2
- **WHEN** se abre `experimentos/h2/docs/hipotesis.md`
- **THEN** encuentra su variable, su predicción y su regla de confirmación, y para δ y los veredictos hay una
  referencia a `experimentos/control/docs/hipotesis.md`

### Requirement: Una hipótesis, una carpeta
Cada hipótesis con brazos propios SHALL tener su experimento (`h1`, `h2`, `h3`, …). La comparación entre hipótesis, la
respuesta a la pregunta del tutor y el guion del video SHALL vivir en `experimentos/sampling_1/`, que depende de todos los
demás y del que no depende ninguno.

#### Scenario: Agregar H4
- **WHEN** el integrante que lleva H4 la incorpora
- **THEN** crea `experimentos/h4/` declarando `control` como dependencia, y `sampling_1` la suma a su comparación sin
  que cambie ninguna carpeta `h1`–`h3`
