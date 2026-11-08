# Design

## Context

"Brazo" aparece en unos 350 archivos y 760 líneas. Casi todo son ledgers: cada `corridas/*.csv` y cada
`resultados.csv`, `reemplazadas.csv`, `estudios.csv` y `apareado.csv` tiene una columna `brazo`, y cada `hp/*.json` una
clave `brazo`. El resto es código de `comun/` (`brazos.py` es el registro, y `correr`, `consolidar`, `ledger`,
`metodos` y `reporte` lo usan), los scripts, los tests, los docs y los informes de cada experimento, los `reporte.html`
generados, las specs y el material histórico (bitácoras, `ledger/sesiones/`, cambios archivados).

Hay dos aportes nuevos fuera del registro:
- `experimentos/h3/sensibilidad_muestra/` (Martín): usa `brazo` como campo de sus propios archivos de corrida, y
  `referencia/` y `resultados/` tienen sha256 en `procedencia.json`.
- `experimentos/Experimentos h3 y h4/` (Luis): un script de Colab y un resumen, en una carpeta con espacios. El nombre
  del archivo quedó mal (`script_de_validaci_n_50_semillas.py`) y el resumen apunta a `validacion_50_semillas.py`.

## Goals / Non-Goals

**Goals:**
- Que todo lo que se lee hoy (código, docs, informes, reportes, README, specs) diga "variante".
- Que ningún número cambie y que eso se pueda comprobar.
- Un README que sirva de puerta de entrada: qué preguntamos, qué encontramos, dónde está cada cosa y qué sigue.

**Non-Goals:**
- Reescribir lo histórico.
- Tocar el código o los archivos con huella de Martín.
- Integrar los números de Luis a la comparación. Eso es de `h3-semillas-optuna`, que define el bloque de estudios
  exploratorios.

## Decisions

### D1. Nombre: variante

Se descartaron:
- "configuración": choca con el uso de Martín (un juego de hiperparámetros).
- "estrategia": suena a recomendación final.
- "tratamiento": "el tratamiento C" es raro.
- "condición": se confunde en el código.

Formas:

| antes | después |
|---|---|
| `Brazo`, `BRAZOS` | `Variante`, `VARIANTES` |
| `brazo()`, `dueno_brazo()`, `nombre()` | `variante()`, `dueno_variante()`, `nombre()` |
| `comun/brazos.py`, `python -m comun.brazos --verificar` | `comun/variantes.py`, `python -m comun.variantes --verificar` |
| `tests/test_brazos.py` | `tests/test_variantes.py` |
| columna y clave `brazo` | `variante` |
| "el brazo", "los brazos" | "la variante", "las variantes" (cuidar el género de artículos y adjetivos) |

### D2. Ledgers: reescribir la cabecera y leer también la vieja

Se reescribe la primera línea de cada CSV de ledger y la clave de cada `hp/*.json` con un script de un solo uso,
`scripts/renombrar_columna.py`. Tiene `--verificar`, que para cada archivo comprueba tres cosas:
- las líneas 2..n son idénticas byte a byte;
- la cabecera difiere solo en `brazo` → `variante`;
- en los JSON, el resto de las claves y los valores es igual.

`comun/ledger.py` traduce `brazo` → `variante` al leer, porque el bucket, el tag `corridas-v1` y cualquier clon viejo
siguen teniendo la cabecera anterior. Siempre escribe `variante`.

Alternativas:
- **Solo el alias, sin reescribir:** deja dos nombres para siempre en el repo.
- **Solo reescribir, sin alias:** rompe consolidar contra el bucket hasta resincronizarlo.

`apareado_previo.csv` no se reescribe: es la foto de antes de separar. Su test lo lee con el alias.

### D3. Qué es histórico y no se toca

No se tocan:
- `*/docs/bitacora.md`, salvo una entrada nueva por experimento que anota el renombre y el commit;
- `ledger/sesiones/`;
- `openspec/changes/archive/`;
- `apareado_previo.csv`;
- `experimentos/h3/sensibilidad_muestra/` completo.

Sí se toca `sampling_1/README.md` § Correspondencia de rutas: describe rutas vigentes, así que se suma
`comun/brazos.py` → `comun/variantes.py`.

### D4. Specs: tres requisitos cambian de nombre

MODIFIED no permite cambiar el nombre de un escenario, así que los requisitos que tienen "Brazo" en un escenario van
como REMOVED + ADDED con nombre nuevo:

| antes | después |
|---|---|
| "Tablas apareadas por semilla" | "Tablas apareadas por variante y semilla" |
| "Curvas de ganancia por brazo" | "Curvas de ganancia por variante" |
| "Se lee del dueño, no se copia" | "Se lee del dueño de la variante o del estudio, no se copia" |

El contenido es el mismo. `h3-semillas-optuna` se escribe sobre estos nombres nuevos.

### D5. Comprobar que no cambia ningún número

Antes de tocar nada, se guarda una foto:
- `python -m comun.consolidar` y `python -m comun.reporte --todos` en la rama actual;
- copia de cada `apareado.csv` y de la tabla de resultados de cada `reporte.html`, extraída con un script a CSV.

Después del renombre se repite y se compara:
- **Valores:** iguales salvo el nombre de la columna.
- **HTML:** las diferencias se limitan a "brazo"/"variante" y a la fecha de generación.
- **Informes:** `git diff --word-diff` sobre los `informe.md` no muestra cambios en ningún número.

### D6. El aporte de Luis

`git mv` a `experimentos/sampling_1/exploratorios/validacion_50_semillas/`:
- `validacion_50_semillas.py`: el script, sin cambiar el contenido;
- `resumen.md`: el resumen que escribió;
- `README.md` (nuevo).

El `README.md` cuenta:
- quién lo hizo y cuándo (6-nov);
- qué corre: 9 estrategias × 50 semillas finales, con los hiperparámetros fijos de nuestros estudios más uno de H4
  hard negatives;
- en qué se aparta del protocolo:
  1. las 50 semillas varían solo la semilla final, así que su IC no mide la suerte de Optuna;
  2. las variantes se eligieron mirando 201910;
  3. fast-retrain y hard negatives cambian la proporción de clases;
  4. no hay ledger;
  5. corre en Colab;
- que falta subir su CSV de resultados.

Va en `sampling_1` porque cruza H3, H4 y fast-retrain, y `sampling_1` es el que compara. Que la carpeta de Martín se
quede en `h3` es coherente: su estudio es solo de H3.

### D7. README

Secciones, en orden:
1. La pregunta, en dos líneas, y la respuesta corta.
2. Resultados hasta ahora: la tabla de `sampling_1/informe/informe.md` § Resultados, con la columna "variante", y la
   comparación a tiempo igual en una línea. Se copia y se cita: el README no recalcula.
3. Mapa de experimentos: la tabla actual, más `sampling_1/exploratorios/` y `h3/sensibilidad_muestra/`.
4. Estudios exploratorios: qué preguntó cada uno, el número clave y la advertencia en una línea.
5. Qué sigue: `h3-semillas-optuna` (¿la suerte de Optuna explica la ventaja de H3?) y H4.
6. Estructura, cómo correr en la Mac y en la VM: lo de hoy, con `comun.variantes`.

Después de `h3-semillas-optuna`, la sección 2 apunta a la comparación nueva.

## Risks / Trade-offs

- **[Concordancia gramatical]** Un reemplazo mecánico deja "los variantes" o "registrados" donde va femenino → grep de
  `\b(los|el|un|del|al) variante`, de `variante[s]? .{0,30}(registrados|propios|nuevos)` y lectura de los informes.
- **[Bucket desincronizado]** Las corridas viejas del bucket tienen `brazo` → alias de lectura (D2) y test que consolida
  un ledger con cabecera vieja.
- **[Diff enorme]** Unos 300 ledgers cambian una línea → un commit solo para las cabeceras, separado del código, para
  que la revisión pueda mirar el resto aparte.
- **[Huellas de Martín]** Si un reemplazo global entra en su carpeta, se rompe `procedencia.json` → el script y el
  `sed` excluyen `h3/sensibilidad_muestra/`; la verificación corre `sha256sum` contra `procedencia.json`.
