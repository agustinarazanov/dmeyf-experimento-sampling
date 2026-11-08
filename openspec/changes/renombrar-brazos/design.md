# Design

## Context

"Brazo" aparece en unos 350 archivos y 760 líneas:

- **Ledgers**, que son la mayoría: cada `corridas/*.csv`, `resultados.csv`, `reemplazadas.csv`, `estudios.csv`,
  `apareado.csv` y `apareado_previo.csv` tiene una columna `brazo`, y cada `hp/*.json` una clave `brazo`.
- **Código de `comun/`**: `brazos.py` es el registro, y `correr`, `consolidar`, `ledger`, `metodos` y `reporte` lo usan.
- **Scripts y tests.**
- **Texto**: docs e informes de cada experimento, `reporte.html` generados, specs vigentes, bitácoras,
  `ledger/sesiones/` (19 archivos) y cambios archivados (14 archivos).
- **El paquete de Martín**, `h3/sensibilidad_muestra/`:
  - usa `brazo` como campo de sus archivos de corrida (`sensibilidad_07.py`, `ganancia_08.py`) y en
    `referencia/grilla_06.json`;
  - 07 regenera la grilla y se detiene si no es idéntica a ese JSON;
  - `resultados/procedencia.json` tiene sha256 de los CSV de `resultados/`, que no dicen "brazo".

El aporte de Luis (`experimentos/Experimentos h3 y h4/`) no menciona "brazo". Lo mueve y lo porta
`incorporar-aportes`.

## Goals / Non-Goals

**Goals:**
- Que ningún archivo del repo ni del bucket diga "brazo", salvo las excepciones de D8.
- Que ningún número cambie, y que eso se pueda comprobar.
- Un README que sirva de puerta de entrada.

**Non-Goals:**
- Reescribir la historia de git o el tag `corridas-v1`.
- Correr nada nuevo.
- Incorporar el aporte de Luis.

## Decisions

### D1. Nombre y formas

| antes | después |
|---|---|
| `Brazo`, `BRAZOS` | `Variante`, `VARIANTES` |
| `brazo()`, `dueno_brazo()` | `variante()`, `dueno_variante()` |
| `comun/brazos.py`, `python -m comun.brazos --verificar` | `comun/variantes.py`, `python -m comun.variantes --verificar` |
| `tests/test_brazos.py` | `tests/test_variantes.py` |
| columna y clave `brazo` | `variante` |
| variables `brazo`, `params_brazo` | `variante`, `params_variante` |
| "el brazo", "los brazos", "brazos propios" | "la variante", "las variantes", "variantes propias" |

Hay que cuidar el género de artículos y adjetivos.

### D2. Ledgers: reescribir todo, sin alias

`scripts/renombrar_columna.py` reescribe la cabecera de cada CSV de ledger y la clave de cada `hp/*.json`, en el repo
y en una copia local del bucket que después se sube con `gsutil rsync`.

Su `--verificar` comprueba, para cada archivo:
- que las líneas 2..n son idénticas byte a byte;
- que la cabecera difiere solo en `brazo` → `variante`;
- en los JSON, que el resto de las claves y los valores es igual.

`comun/ledger.py` no traduce: si una cabecera dice `brazo`, falla nombrando el archivo. Así un ledger viejo no entra en
silencio a una consolidación nueva.

El script queda en `scripts/` como registro de la migración.

### D3. Texto: reemplazo en todo el repo, con revisión

1. Un script reemplaza con las reglas de D1, ordenadas de lo específico a lo general, sobre todo `git ls-files`
   excepto binarios.
2. Después se buscan problemas de concordancia: `\b(los|el|un|del|al|este|ese) variantes?\b`, y participios o
   adjetivos masculinos a menos de 30 caracteres de "variante".
3. Esos resultados se corrigen a mano.

Los archivos de `ledger/sesiones/` y de `openspec/changes/archive/` entran igual que el resto. Son texto, y ningún
proceso los lee buscando "brazo". Antes de correrlo se comprueba que `comun/tokens.py` no dependa de su contenido
literal.

### D4. El paquete de Martín

Se renombra:
- el campo `brazo` en `sensibilidad_07.py` y `ganancia_08.py`;
- su clave en `referencia/grilla_06.json`;
- su generador en `busqueda.py`, para que 07 siga regenerando una grilla idéntica.

Después se recalculan las huellas de `referencia/` y `procedencia.json` que dependan de archivos modificados, si las
hay.

Los 13 tests de Martín (`tests/test_h3sm_*.py`) deben pasar. Sus corridas viejas en `DATOS_DIR` dejan de leerse, pero
`incorporar-aportes` corre 07 y 08 de nuevo.

### D5. Specs: tres requisitos cambian de nombre

MODIFIED no permite cambiar el nombre de un escenario, así que los requisitos con "Brazo" en un escenario van como
REMOVED + ADDED con nombre nuevo:

| antes | después |
|---|---|
| "Tablas apareadas por semilla" | "Tablas apareadas por variante y semilla" |
| "Curvas de ganancia por brazo" | "Curvas de ganancia por variante" |
| "Se lee del dueño, no se copia" | "Se lee del dueño de la variante o del estudio, no se copia" |

`h3-semillas-optuna` e `incorporar-aportes` se escriben sobre estos nombres.

### D6. Comprobar que no cambia ningún número

**Antes del renombre** se guarda una foto en `DATOS_DIR/renombre/antes/`:
- se corren `python -m comun.consolidar` y `python -m comun.reporte --todos`;
- se copia cada `apareado.csv` y la tabla de resultados de cada `reporte.html`, extraída a CSV.

**Después** se repite y se compara:
- **Valores:** iguales.
- **HTML:** solo cambian "brazo"/"variante" y la fecha.
- **Informes:** `git diff --word-diff` sobre los `informe.md` no muestra números.

### D7. README

Secciones, en orden:
1. La pregunta y la respuesta corta.
2. Resultados hasta ahora: la tabla de `sampling_1/informe/informe.md` § Resultados y la comparación a tiempo igual en
   una línea, copiadas con la fuente citada.
3. Mapa de experimentos.
4. Aportes de Martín y Luis: qué preguntó cada uno, su estado y en qué cambio se incorporan.
5. Qué sigue: `h3-semillas-optuna` e `incorporar-aportes` (H4).
6. Estructura y cómo correr.

Los cambios siguientes actualizan las secciones 2 a 5.

### D8. Excepciones: lo que tiene que nombrar "brazo"

Un renombre que se documenta y se protege no puede borrar la palabra vieja de todos lados. Quedan:
- la historia de git y el tag `corridas-v1`;
- `openspec/changes/renombrar-brazos/`, también una vez archivado;
- `scripts/renombrar_columna.py` y los demás scripts de la migración (`scripts/reemplazar_d1.py`,
  `scripts/foto_renombre.py`, `scripts/verificar_tokens_renombre.py`), que nombran la palabra vieja para buscarla;
- el rechazo de la cabecera vieja en `comun/ledger.py` y su test;
- el escenario "Ledger con la columna vieja" de `ledger-resultados`;
- la entrada de cada bitácora que registra el renombre;
- las menciones del nombre de este cambio, `renombrar-brazos`, en otros cambios y documentos.

La verificación final es `git grep -n -i brazo | grep -v renombrar-brazos`. Tiene que devolver solo líneas de los
archivos de esta lista.

## Risks / Trade-offs

- **[Concordancia gramatical]** Un reemplazo mecánico deja "los variantes" → grep de D3 y lectura de los informes en
  la revisión.
- **[Diff enorme]** → tres commits: cabeceras de ledgers, código y tests, y texto. Así cada uno se revisa por separado.
- **[Bucket a medias]** Si el `rsync` falla a mitad, el bucket queda mezclado y la consolidación falla por D2 →
  verificar el bucket con `--verificar` sobre una copia bajada después de subir.
- **[Clones viejos]** Un clon anterior al renombre consolida con `brazo` y el código nuevo lo rechaza → aviso en la
  bitácora de `sampling_1` y en el commit.
