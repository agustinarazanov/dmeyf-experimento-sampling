# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
