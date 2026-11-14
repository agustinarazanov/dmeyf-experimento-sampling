# Spec Delta

## MODIFIED Requirements

### Requirement: Dependencias declaradas
Cada experimento SHALL declarar en su `README.md`, en una sección `## Dependencias`, de qué otros experimentos depende
y qué toma de cada uno (filas del ledger, hiperparámetros, N*, δ). Un experimento que no toma nada de otro declara la
sección vacía. Las dependencias SHALL formar un grafo sin ciclos.

#### Scenario: Leer las dependencias de H3
- **WHEN** se abre `experimentos/h3/README.md`
- **THEN** la sección `## Dependencias` nombra a `control` (finales de `C`, N*, δ) y a `h1` (estudios `U0.25` y
  `U0.1`)

#### Scenario: Dependencia circular
- **WHEN** un experimento declara una dependencia de otro que ya depende de él, directa o indirectamente
- **THEN** la verificación de dependencias falla y nombra el ciclo

#### Scenario: Sección en el archivo viejo
- **WHEN** un experimento tiene `docs/diseno.md` con `## Dependencias` y no la tiene en su `README.md`
- **THEN** la verificación de dependencias falla nombrando el experimento y el archivo que tiene que tener la sección
