# dependencias-entre-experimentos Specification

## Purpose
Define cómo un experimento usa resultados de otro (el control, un estudio de Optuna ajeno) sin copiarlos, cómo queda
declarado ese uso y qué pasa al borrar o al cambiar un experimento del que otros dependen.

## Requirements

### Requirement: Dependencias declaradas
Cada experimento SHALL declarar en su `README.md`, en una sección `## Dependencias`, de qué otros experimentos depende
y qué toma de cada uno (filas del ledger, hiperparámetros, N*, δ). Un experimento que no toma nada de otro declara la
sección vacía. Las dependencias SHALL formar un grafo sin ciclos. Los estudios `U{r}` y sus réplicas `U{r}@k` son de
`h1` (D10), y quien los usa declara `h1`, no el experimento que los corrió antes de la mudanza.

#### Scenario: Leer las dependencias de H3
- **WHEN** se abre `experimentos/h3/README.md`
- **THEN** la sección `## Dependencias` nombra a `control` (finales de `C` y de `C@1…7`, N*, δ) y a `h1` (todos los
  estudios `U{r}` y sus réplicas `U{r}@k`, r ∈ {0,5; 0,25; 0,1; 0,05})

#### Scenario: H4 deja de depender de H3
- **WHEN** se abre `experimentos/h4/README.md` después de mover los estudios `U{r}@k` a `h1`
- **THEN** la sección `## Dependencias` nombra a `control` y a `h1` (estudios `U0.05`, `U0.25` y sus `@k`), y no a `h3`
- **AND** `python -m comun.variantes --verificar` no encuentra ciclos

#### Scenario: Pares entre experimentos
- **WHEN** se abre `experimentos/sampling_1/README.md`
- **THEN** su `## Dependencias` nombra a cada experimento del que `ledger/pares.csv` lee `resultados.csv`

#### Scenario: Dependencia circular
- **WHEN** un experimento declara una dependencia de otro que ya depende de él, directa o indirectamente
- **THEN** la verificación de dependencias falla y nombra el ciclo

#### Scenario: Sección en el archivo viejo
- **WHEN** un experimento tiene `docs/diseno.md` con `## Dependencias` y no la tiene en su `README.md`
- **THEN** la verificación de dependencias falla nombrando el experimento y el archivo que tiene que tener la sección

### Requirement: Borrar o cambiar un experimento del que otros dependen
Borrar un experimento SHALL romper solo a los que lo declaran como dependencia, y la verificación de dependencias SHALL
nombrarlos. Si un experimento invalida o reemplaza filas de las que otro depende, los dependientes SHALL anotarlo en su
bitácora antes de regenerar su informe.

#### Scenario: Borrar h1
- **WHEN** se borra `experimentos/h1/`
- **THEN** `control` y `h2` siguen generando su reporte, y la verificación indica que `h3` y `sampling_1` quedan rotos

#### Scenario: Se repite el estudio del control
- **WHEN** el ledger de `control` reemplaza su estudio o sus finales
- **THEN** cada experimento que declara `control` como dependencia anota en su bitácora que sus Δ cambian

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
