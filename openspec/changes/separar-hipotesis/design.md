# Design

## Context

Hoy todo Sampling_1 está en `experimentos/sampling-velocidad/`:

- `src/` tiene `correr.py`, `metodos.py`, `muestreo.py`, `consolidar.py` y `reporte.py`. Se importan entre sí con
  `from src import …` y fijan sus rutas con `Path(__file__).parents[1]` (`EXPERIMENTO`, `LEDGER`).
- `ledger/` tiene una sola tabla para los once brazos más `C-rep`. El `id` de cada fila empieza por el brazo, así que el
  dueño de cada fila sale del propio `id`.
- El mapa de brazos a hipótesis ya existe, pero repartido: `metodos.estudio()` y `metodos.brazo()` sacan el nombre de
  estudio y de brazo, y `reporte.HIPOTESIS` agrupa los brazos por H.
- `H3-*` usa el estudio `U*` (`metodos.estudio`), y en los finales lee `ledger/hp/U{r}.json` (`correr.ruta_hp`).
- Los scripts de VM fijan `EXP=experimentos/sampling-velocidad`, corren `python -m src.correr` desde esa carpeta con
  `PYTHONPATH=../..` y sincronizan `ledger/` contra `$BUCKET/ledger/`.
- `comun/tokens.py` toma todas las sesiones del proyecto de Claude Code y las asigna a un solo experimento.
- `tests/test_consolidar.py` agrega `experimentos/sampling-velocidad` a `sys.path`.

Los resultados están cerrados: 129 corridas válidas y el informe ya entregado. No hay corridas nuevas en este cambio.

## Goals / Non-Goals

**Goals:**
- Que cada hipótesis tenga su carpeta, su ledger y su informe, y que se pueda leer, revisar y presentar sola.
- Que lo compartido (control, estudios `U*`, corredor) tenga un único dueño y que se lea siempre de él.
- Que, después de reorganizar, los números salgan idénticos a los de antes, y que eso se compruebe automáticamente.
- Que H4 y las hipótesis siguientes entren sin tocar las carpetas `h1`–`h3`.

**Non-Goals:**
- No se vuelve a correr ningún estudio. En particular, H3 no recibe estudios propios: la falta de independencia con H1
  sigue siendo una limitación declarada.
- No se reescribe la historia: el cambio archivado, los tags, los commits y los logs de sesión quedan como están.
- No se reparte la bitácora ni el registro de tokens ya cerrados.
- No se cambia la grilla, las métricas ni las reglas de decisión.

## Decisions

### D1. Cinco carpetas hermanas: `control`, `h1`, `h2`, `h3` y `sampling_1`

```
comun/                      código compartido (+ corredor, reporte, registro de brazos)
experimentos/
  control/   C, C-rep       reglas comunes, N*, delta
  h1/        U0.5 U0.25 U0.1 U0.05       dueña de los estudios U*
  h2/        B0.5 B0.25 B0.1 GOSS
  h3/        H3-0.25 H3-0.1              lee U0.25/U0.1 de h1
  sampling_1/ (ex sampling-velocidad)    comparación, video, bitácora, tokens

  control <-- h1 <-- h3
     ^  ^             ^
     |  +---- h2      |
     +---- sampling_1 (lee todos)
```

`sampling_1` sale de `git mv experimentos/sampling-velocidad experimentos/sampling_1`. Así se conserva la historia de la
bitácora, de las sesiones y del informe. Después, las carpetas de cada hipótesis se arman extrayendo de ella.
*Alternativa descartada*: anidarlas como `sampling-velocidad/{control,h1,…}`. Contradice el pedido de una carpeta por
hipótesis bajo `experimentos/`, y la plantilla y los scripts suponen un solo nivel.
El nombre es el del experimento en el curso y en Zulip (Sampling_1): `control` y `h1`–`h4` son sus partes.
*Alternativa descartada*: `conjunto` o `resultados` para esa carpeta. `resultados` choca con `ledger/resultados.csv`
de cada experimento y la carpeta guarda más que resultados (pregunta, video, bitácora, tokens).
*Alternativa descartada*: llamar `h0` o `baseline` al control. `H0` se confunde con la hipótesis nula. `baseline` choca
con `comun/baseline.py` y no es exactamente el baseline de Bolaños, por las adaptaciones declaradas.

### D2. Registro único de brazos en `comun/brazos.py`

Una tabla declara cada brazo con su experimento dueño, su método, su tasa y su estudio, y cada estudio con su dueño:

| brazo | dueño | estudio | dueño del estudio |
|---|---|---|---|
| `C`, `C-rep` | control | `C` | control |
| `U0.5` … `U0.05` | h1 | `U{r}` | h1 |
| `B0.5` … `B0.1`, `GOSS` | h2 | `B{f}`, `GOSS` | h2 |
| `H3-0.25`, `H3-0.1` | h3 | `U0.25`, `U0.1` | h1 |

De ese registro salen `metodos.estudio()`, `metodos.brazo()`, `reporte.HIPOTESIS`, el destino de cada fila y las
dependencias implícitas. La sección `## Dependencias` de cada `diseno.md` la escribe una persona. Una verificación
(`python -m comun.brazos --verificar`) compara lo declarado con lo que el registro implica, busca ciclos y lista qué se
rompe si falta una carpeta.
*Alternativa descartada*: un archivo de configuración por experimento (`experimento.yaml`). Reparte la misma
información en cinco lugares y obliga a leerlos todos para saber de quién es un estudio.

### D3. Corredor, métodos, consolidación y reporte pasan a `comun/`

Se mueven `correr.py`, `metodos.py`, `muestreo.py`, `consolidar.py` y `reporte.py` a `comun/`. Las rutas dejan de
salir de `__file__` y salen del registro: `comun.rutas.ledger(exp) = RAIZ / "experimentos" / exp / "ledger"`.
- `correr`: se invoca como `python -m comun.correr …` desde la raíz. La fila va a `ledger(dueño(brazo))` y los hp a
  `ledger(dueño(estudio))/hp/`. El flag `--hp` se mantiene para casos manuales.
- `consolidar --experimento X`: lee las filas de X y los finales de `C` en `ledger(control)`, y escribe
  `ledger(X)/apareado.csv`. N* se calcula siempre desde `control`. Sin argumento, consolida todos.
- `reporte --experimento X`: genera `experimentos/X/informe/reporte.html`. Para un `hN` incluye la intro de su
  `hipotesis.md`, sus brazos contra el control y sus bandas. Para `sampling_1` incluye la tabla de todos los brazos, la
  curva tiempo-ganancia, tiempo igual y enlaces a cada `hN/informe/reporte.html`. Con `--todos` genera los cinco.
- Las funciones de figuras y tablas que ya existen (`fig_bandas`, `tabla_brazos`, `tiempo_igual`,
  `seccion_hipotesis`) no cambian de lógica, solo reciben las filas ya filtradas.
*Alternativa descartada*: dejar el corredor en `control/src/`. Haría que todo el código dependa de una carpeta de
resultados, y `control` dejaría de ser solo C.

### D4. Separar el ledger con un script verificable de una sola vez

`scripts/separar_ledger.py --origen experimentos/sampling_1/ledger` reparte filas y archivos por dueño según D2:
`resultados.csv`, `estudios.csv` y `reemplazadas.csv` se filtran por `brazo`, `hp/` por estudio, y `curvas/`,
`corridas/` y `predicciones/` por el prefijo del `id`. Con `--verificar`, comprueba que no se perdió ni se duplicó
ningún `id` (spec `ledger-resultados`). Después se regenera cada `apareado.csv` y se compara con el original.
Lo que no tiene brazo queda en `sampling_1/ledger/`: `exploracion/`, `sesiones/` y `tokens.csv`. El `apareado.csv`
original se guarda como `sampling_1/ledger/apareado_previo.csv`, como referencia para la comparación.
El script queda en el repo (no se borra) como registro de cómo se hizo la separación.
*Alternativa descartada*: copiar sin borrar del origen. Deja dos fuentes de verdad, contra la spec "se lee del dueño".

### D5. Documentos: se reparten por sección, sin reescribir

| origen (`sampling_1/docs/` o `informe/`) | destino |
|---|---|
| `hipotesis.md` § Control, § Métricas y reglas comunes | `control/docs/hipotesis.md` |
| `hipotesis.md` § H1 / § H2 / § H3 | `hN/docs/hipotesis.md` (con referencia a `control` para las reglas) |
| `hipotesis.md` § H4 | `sampling_1/docs/hipotesis.md`, como pendiente (sin carpeta hasta que la tome el integrante) |
| `hipotesis.md` § Pregunta, § Respuesta al tutor, § Limitaciones comunes | `sampling_1/docs/hipotesis.md` |
| `diseno.md` § Brazos, § Grilla (por fila) | el `diseno.md` del dueño, más `## Dependencias` |
| `diseno.md` § Estudios compartidos | `h1/docs/diseno.md` y `h3/docs/diseno.md` |
| `diseno.md` § Máquina, § Parámetros fijos, § Métricas | `control/docs/diseno.md` |
| `diseno.md` § Reparto y fases, § Estimación, § Tutor | `sampling_1/docs/diseno.md` |
| `informe.md` § Resultados (bullet de cada H, filas de la tabla) | `hN/informe/informe.md` |
| `informe.md` resto, `decisiones.md`, `guion.md` | quedan en `sampling_1/informe/` |

Los textos se mueven tal cual y se ajustan solo las referencias cruzadas. Cada `hN/docs/bitacora.md` y la de
`control` abren con una entrada que apunta a `sampling_1/docs/bitacora.md` para la historia anterior al 2-nov y declara
la etapa hipótesis como revisada en esa fecha. Así se cumple "hipótesis escritas antes de ejecutar" sin reescribir
fechas.

### D6. Tokens: una sesión pertenece a quien la declara

`comun/tokens.py` deja de asignar todas las sesiones del proyecto a un solo experimento. Junta las declaraciones de
todas las bitácoras y de todos los `costos.csv` del repo. Cada sesión va al experimento que la declara; las que no
declara nadie van a `sampling_1` como `sin-etapa`; si dos la declaran, falla. Sin `--experimento`, regenera todos los
`tokens.csv`. Esta sesión (exploración y propuesta de la separación) se declara en `sampling_1` como etapa `diseno`.

### D7. Scripts de VM a la raíz

`vm.sh` y `lanzar_fase.sh` pasan a `scripts/`. En la VM corren `python -m comun.correr` desde la raíz, y se
sincroniza `experimentos/*/ledger/` contra `$BUCKET/experimentos/<exp>/ledger/`. Los `faseN.txt` históricos quedan en
`sampling_1/scripts/` como registro y no se vuelven a lanzar. El bucket viejo (`$BUCKET/ledger/`) no se toca; las
predicciones locales ya repartidas por D4 son la copia de trabajo.

## Risks / Trade-offs

- [Un import o una ruta que se olvida y que solo falla en la VM] → el smoke test de la Mac (`--filas 20000`) se corre
  para un brazo de cada experimento antes de dar el cambio por cerrado. Se agrega un test que importa `comun.correr` y
  resuelve el destino de cada brazo del registro.
- [La regeneración da números distintos por un filtro mal hecho] → la verificación de D4 compara `apareado.csv` fila
  por fila contra `apareado_previo.csv`, y el reporte de `sampling_1` debe dar la misma tabla que `informe.md`. Si
  difiere, el cambio no se cierra.
- [`git mv` más extracciones dejan la historia de `hN/` cortada] → aceptado: `git log --follow` sigue los archivos
  movidos; para lo extraído, la bitácora de cada `hN` apunta al commit de la separación.
- [El registro en `comun/` se vuelve un punto que toca todo experimento nuevo] → es una tabla de una línea por brazo,
  y ese cambio en `comun/` se anuncia en el commit como cualquier otro.
- [Las referencias viejas a `sampling-velocidad` en `CLAUDE.md`, `README.md`, `docs/metodo.md` y la plantilla] → una
  tarea las actualiza todas y un `grep` sin coincidencias fuera de lo histórico lo verifica.
- [Más carpetas, más contexto por sesión] → cada sesión lee solo el experimento de su etapa. Es lo que se busca:
  menos tokens por turno.

## Migration Plan

1. `git mv` a `sampling_1` y commit (solo el renombre, para que git lo siga).
2. Mover el código a `comun/` y agregar el registro y las rutas; tests verdes con el ledger todavía en `sampling_1`.
3. Separar el ledger con `--verificar`; consolidar cada experimento y comparar con `apareado_previo.csv`.
4. Repartir los documentos y escribir las secciones `## Dependencias`; correr `comun.brazos --verificar`.
5. Generar los cinco reportes y comparar la tabla de `sampling_1` con `informe.md`.
6. Tokens, scripts de VM, README, CLAUDE.md, `docs/metodo.md` y plantilla.

Vuelta atrás: cada paso es un commit propio y el ledger original queda en el commit del paso 1. Para volver, alcanza con
`git revert` de los pasos posteriores. Las predicciones (fuera de git) se recuperan del bucket viejo, que no se toca.
