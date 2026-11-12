# Método de trabajo

Vale para todos los experimentos del repo. Cada experimento vive en `experimentos/<nombre>/`. Depende solo de `comun/`
y de su propia carpeta, y se puede borrar sin romper a los demás. Si un cambio toca `comun/`, el mensaje del commit lo
dice y cada experimento activo anota en su bitácora si lo afecta.

## Etapas

Hipótesis, diseño, código, corridas, análisis, informe. Cada etapa:

1. Arranca en una sesión nueva de Claude Code, a partir de los artefactos de `openspec/` y de la bitácora del
   experimento.
2. Termina con una revisión en sesión limpia (una sesión nueva, un subagente `general-purpose` o un integrante que no la
   ejecutó), usando la lista de `docs/revision.md`. No se cierra con un ✗ abierto.
3. Se cierra en `docs/bitacora.md` del experimento con el formato de cierre: fecha, sesión, revisor, hallazgos,
   correcciones, tokens y devolución del tutor.

## Modelo por etapa

- Opus: hipótesis, diseño, revisiones e informe.
- Sonnet: código, tablas y tareas mecánicas.
- Fable: solo si una decisión de diseño lo amerita.

## Tokens

- Salidas largas a archivo, nunca al chat. Leerlas con `head`, `tail` o un resumen.
- Subagentes solo para búsquedas o revisiones sin contexto.
- Lo repetido va a scripts. Las corridas las hace la VM, no una conversación.
- `/clear` al cerrar cada etapa.
- Las etapas que no necesitan a una persona se corren headless en vez de a mano: `scripts/etapas.sh <exp> <cambio>`
  recorre todos los grupos pendientes de `tasks.md`; `scripts/etapa.sh <grupo> …` corre uno solo (lo usa `etapas.sh`).
- `comun/tokens.py` escribe el `ledger/tokens.csv` de cada experimento. Clasifica cada sesión según la etapa que declara
  la bitácora de algún experimento (o su `ledger/sesiones/costos.csv`); la que nadie declara va a `sampling_1` y si dos
  la declaran falla.
- Objetivo: menos de 100.000 tokens de contexto por turno. La línea de base de octubre ronda los 400.000.

## Agregar un experimento

1. Copiar `plantilla/` a `experimentos/<nombre>/`.
2. Completar `docs/hipotesis.md` (citando las reglas de `control`) y abrir la bitácora con la etapa hipótesis.
3. Declarar `## Dependencias` en `docs/diseno.md`: de qué experimentos lee (`control` como mínimo).
4. Registrar sus variantes y estudios en `comun/variantes.py` (variante → dueño, método, tasa, estudio; estudio → dueño) y
   anunciarlo en el commit. `python -m comun.variantes --verificar` compara las dependencias declaradas con las que
   implica el registro, busca ciclos y lista qué se rompe si falta una carpeta.
5. Sumarlo a la tabla de experimentos del `README.md`.

Los pasos completos, con ejemplos, están en § Agregar una hipótesis.

## Agregar una hipótesis

Guía para quien suma una hipótesis (`h4`, …) sin tocar las de otros. Todo se corre desde la raíz del repo.

### 1. Qué va en cada carpeta

```
comun/                    código y registro compartidos: variantes.py, correr.py, consolidar.py, reporte.py,
                          metodos.py, muestreo.py, rutas.py, tokens.py, datos/baseline/ganancia/ledger
experimentos/
  control/                el control C (y C-rep) y las reglas comunes: G, Δ, δ, T, A, N*, veredictos
  h1/ h2/ h3/             una hipótesis cada una: docs/ (hipotesis, diseno, bitacora), ledger/, informe/
  sampling_1/             el experimento conjunto: compara a todas contra `control`; fases de VM, informe y video
plantilla/                la estructura vacía de un experimento
```

- Cada hipótesis es dueña de **su** carpeta y de **su** `ledger/`: escribe ahí las filas de sus variantes y los
  hiperparámetros de sus estudios. No se editan ni se commitean cambios en las carpetas ni los ledgers de `control`, `h1`–`h3`
  ni `sampling_1`; si hace falta algo de ellos, se lee. Única excepción: sumar la línea `` - `hN` `` a `## Dependencias` de
  `sampling_1/docs/diseno.md` (el conjunto depende de todas las hipótesis y `--verificar` lo exige; ver paso 3).
- Lo único compartido que se edita es `comun/`, y el cambio se anuncia en el mensaje del commit.

### 2. Pasos, en orden

1. Tomar el siguiente `hN` libre (`ls experimentos/`). El nombre tiene que ser un identificador válido: letras
   minúsculas, dígitos y `_`, sin guiones ni espacios (`h4`, no `h-4`).
2. `cp -r plantilla experimentos/hN`, reemplazar `<experimento>` por `hN` en los títulos de `docs/` y completar
   `docs/hipotesis.md`: variable, métrica que decide, predicción y reglas
   de confirmación y refutación. Las definiciones de G, Δ, δ, T, A, N* y los veredictos se **citan** de
   [`control/docs/hipotesis.md`](../experimentos/control/docs/hipotesis.md), no se copian. Abrir `docs/bitacora.md`
   con una primera entrada bajo `## Entradas` (`### AAAA-MM-DD — apertura`, quién, sesión y etapa `hipotesis`); los
   cierres de etapa siguen el formato que trae la plantilla.
3. En `docs/diseno.md` completar las variantes, la grilla y el resto, y declarar `## Dependencias`: la plantilla ya trae
   `control` (finales de `C`, N* y δ); sumar un experimento más por cada estudio ajeno que se use (ver 3). Agregar además
   `` - `hN` `` a `## Dependencias` de `experimentos/sampling_1/docs/diseno.md`: es la única línea que se toca fuera de
   `hN/` y `comun/`.
4. Registrar en `comun/variantes.py`, y anunciarlo en el commit:
   - cada variante en `VARIANTES`: `Variante(nombre, "hN", método, tasa, estudio)`;
   - cada estudio de Optuna propio en `ESTUDIOS`: `"nombre": "hN"`.
   Por ejemplo, una variante ficticia de `h9` con la tasa 0,02: `Variante("U0.02", "h9", "uniforme", 0.02, "U0.02")` dentro de
   la lista de `VARIANTES` y `"U0.02": "h9"` en `ESTUDIOS` (`Variante` es la `NamedTuple` de ese mismo archivo; `nombre("uniforme",
   0.02)` ya devuelve `U0.02`, así que no hace falta tocar nada más). Los nombres de variante y de estudio no se repiten
   entre hipótesis.
   Si la variante es de un `(método, tasa)` nuevo, `nombre()` tiene que saber nombrarlo, y un método nuevo además va en
   `comun/metodos.py` (`METODOS`, `FUNCIONES`, `validar`).
5. `python -m comun.variantes --verificar`: pasa si sale con código 0 y no imprime ninguna línea `PROBLEMA` (lo que sí
   imprime siempre son las líneas "si falta experimentos/X/ se rompen: …"). Falla si falta la sección
   `## Dependencias`, si no coincide con lo que implica el registro, si hay un ciclo o si falta una carpeta; también
   lista qué se rompe si falta cada carpeta.
6. Correr: `python -m comun.correr --metodo M --tasa R --semilla S --etapa optimizar|final` (primero con `--filas 20000`
   en la Mac; en la VM, `scripts/vm.sh`). La fila va al ledger del dueño de la variante.
7. `python -m comun.consolidar --experimento hN` arma `resultados.csv`, `estudios.csv` y `apareado.csv` de `hN` (las filas
   salen de `ledger/corridas/`, así que hace falta haber corrido al menos el control y una variante), y
   `python -m comun.reporte --experimento hN` su `informe/reporte.html`.
8. Escribir el `informe/informe.md` de `hN` con su veredicto y sus limitaciones. No hace falta tocar `h1`–`h3`:
   `python -m comun.reporte --experimento sampling_1` toma las hipótesis del registro, así que `hN` aparece sola en la
   comparación conjunta (hay que regenerar ese reporte, no editarlo a mano). Para probar sin pisar el reporte versionado,
   `python -m comun.reporte --experimento sampling_1 --salida /tmp/reporte.html` (fuera de `informe/` los enlaces
   relativos a los otros reportes no abren; para revisar el contenido alcanza).
9. Sumar el experimento al sitio: copiar en `defaults:` de `_config.yml` las entradas de otra hipótesis (por ejemplo las
   de `h4`) cambiando la ruta y los títulos. La sección del sitio y el orden salen de `parent` y `nav_order`. Para una
   hipótesis ficticia `h9`, el informe es el padre de su reporte, su hipótesis, su diseño y su bitácora:

   ```yaml
     - scope:
         path: experimentos/h9/informe/informe.md
       values: {title: "H9", parent: "Experimentos", nav_order: 6, has_children: true}
     - scope:
         path: experimentos/h9/informe/reporte.html
       values: {title: "Reporte", parent: "H9", grand_parent: "Experimentos", nav_order: 1}
     - scope:
         path: experimentos/h9/docs/hipotesis.md
       values: {title: "Hipótesis", parent: "H9", grand_parent: "Experimentos", nav_order: 2}
     - scope:
         path: experimentos/h9/docs/diseno.md
       values: {title: "Diseño", parent: "H9", grand_parent: "Experimentos", nav_order: 3}
     - scope:
         path: experimentos/h9/docs/bitacora.md
       values: {title: "Bitácora de h9", parent: "Proceso", nav_order: 8}
   ```

   Después `scripts/sitio.sh` (construye y verifica enlaces; con `serve` lo deja en `localhost:4000`). Si se olvida
   este paso, las páginas igual aparecen, pero en el primer nivel de la barra lateral.

### 3. Usar un estudio de otra hipótesis

Una variante puede entrenar con los hiperparámetros de un estudio que corrió otra hipótesis. El caso de la casa es H3
(`H3-0.25`): su variante es de `h3`, pero su estudio es `U0.25`, de `h1`. En el registro,
`Variante("H3-0.25", "h3", "opt-muestra", 0.25, "U0.25")` con `"U0.25": "h1"` en `ESTUDIOS`; `comun.correr` lee
`experimentos/h1/ledger/hp/U0.25.json` y escribe la fila en `experimentos/h3/ledger/`. Consecuencia: `h3` declara
`h1` en `## Dependencias` (`--verificar` lo exige) y no se corre `h3` sin los hp de `h1`.

### 4. Ejemplo: H4

H4 prueba muestreos que no son uniformes: `informado` (conserva las filas que más aportan) y `pesado` (conserva todas
y pesa las de la clase positiva). Los pasos: `h4/` desde la plantilla; los dos métodos en `comun/metodos.py` y su regla
de nombre en `variantes.nombre()`; variantes `I0.25` e `P0.25`, con estudios propios `I0.25` e `P0.25` de `h4` (o, si se
compara contra el mismo estudio que `U0.25`, con estudio `U0.25` de `h1` y `h4` declara `h1`); `## Dependencias` con
`control`; `--verificar`, correr, consolidar y reportar. Ni `control` ni `h1`–`h3` se modifican.
