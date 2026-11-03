# Tasks

## 1. Renombre a `sampling_1` (sesión: Sonnet)

- [x] 1.1 `git mv experimentos/sampling-velocidad experimentos/sampling_1` y commit con solo ese renombre; verificar que `git log --follow experimentos/sampling_1/docs/bitacora.md` muestra la historia previa
- [x] 1.2 Actualizar las rutas que se rompen con el renombre (`tests/test_consolidar.py`, defaults de `comun/tokens.py`, `scripts/etapa.sh`, `scripts/etapas.sh`, `EXP=` de los scripts de VM), para que el repo siga andando antes de separar; verificar que `pytest` pasa y que `python -m comun.tokens --experimento sampling_1` deja `tokens.csv` igual

## 2. Registro de brazos y código en `comun/` (sesión: Sonnet)

- [x] 2.1 Crear `comun/brazos.py` con la tabla de D2 (brazo → dueño, método, tasa, estudio; estudio → dueño) y `comun/rutas.py` (`ledger(exp)`, `docs(exp)`, `informe(exp)`); verificar con un test que cada brazo de `apareado.csv` y cada estudio de `estudios.csv` tiene dueño, y que un brazo desconocido falla nombrándolo
- [x] 2.2 Mover `muestreo.py` y `metodos.py` a `comun/`. Hacer que `estudio()` y `brazo()` salgan del registro y que los imports sean `from comun import …`; verificar que los nombres de estudio y brazo de cada `(método, tasa)` de la grilla son los mismos que antes (test)
- [x] 2.3 Mover `correr.py` a `comun/`: la fila va al ledger del dueño del brazo y los hp se leen y escriben en el ledger del dueño del estudio (spec `corrida-reproducible`); verificar con el smoke test de la Mac (`--filas 20000`) una optimización de `U0.25` en `h1/ledger` y un final de `H3-0.25` en `h3/ledger` que lee `h1/ledger/hp/U0.25.json`
- [x] 2.4 Mover `consolidar.py` a `comun/` con `--experimento X` (filas de X, finales de `C` y N* desde `control`) y sin argumento para todos; mover `tests/test_consolidar.py` a la nueva ruta y agregar un caso con dos ledgers; verificar que `pytest` pasa
- [x] 2.5 Agregar `python -m comun.brazos --verificar`: compara la sección `## Dependencias` de cada `diseno.md` con lo que implica el registro, detecta ciclos y lista qué se rompe si falta una carpeta (spec `dependencias-entre-experimentos`); verificar con tests de un ciclo armado a mano y de una carpeta faltante
- [x] 2.6 Revisión en sesión limpia del grupo 2 con la lista de código de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`

## 3. Separación del ledger (sesión: Sonnet)

- [x] 3.1 Escribir `scripts/separar_ledger.py` (D4) con `--verificar`, que reparte por dueño `resultados.csv`, `estudios.csv`, `reemplazadas.csv`, `hp/`, `curvas/`, `corridas/` y `predicciones/`, y deja en `sampling_1` lo que no tiene brazo; verificar con un test sobre un ledger sintético de tres brazos que ningún `id` se pierde ni se duplica
- [x] 3.2 Guardar `sampling_1/ledger/apareado.csv` como `apareado_previo.csv`, correr la separación sobre el ledger real (con las predicciones locales) y `--verificar`; verificar que la unión de los `resultados.csv` de `control`, `h1`, `h2` y `h3` tiene los mismos `id` que el original
- [x] 3.3 Correr `python -m comun.consolidar` para todos y comparar la unión de los `apareado.csv` con `apareado_previo.csv`; verificar que coinciden fila por fila (diferencia 0 en Δ, IC, A y n). Si no coinciden, no se sigue
- [x] 3.4 Ajustar `scripts/vm.sh` y `scripts/lanzar_fase.sh` (movidos a la raíz) para correr `python -m comun.correr` desde la raíz y sincronizar `experimentos/*/ledger/` contra `$BUCKET/experimentos/<exp>/ledger/` (D7); dejar los `faseN.txt` en `sampling_1/scripts/`; agregar a `vm.sh` un flag `--en-seco` que imprime comandos y destinos y sale antes de cualquier `gcloud` o `gsutil`; verificar solo con `bash -n` y con `--en-seco`. **No ejecutar `vm.sh` ni `lanzar_fase.sh` sin `--en-seco`: este cambio no crea VMs**
- [x] 3.5 Revisión en sesión limpia del grupo 3 con las listas de código y resultados de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`

## 4. Documentos por experimento (sesión: Opus)

- [x] 4.1 Crear `control/docs/hipotesis.md` y `control/docs/diseno.md` con las secciones de D5 (control, reglas comunes, parámetros fijos, máquina, métricas) y `## Dependencias` vacía; verificar que G, Δ, δ, T, A, N* y los veredictos quedan definidos una sola vez en todo el repo (`grep`)
- [x] 4.2 Crear `h1/`, `h2/` y `h3/` con `docs/hipotesis.md` (la sección de su H, con referencia a `control` para las reglas) y `docs/diseno.md` (sus brazos, su grilla, estudios compartidos en `h1` y `h3`, `## Dependencias`); verificar que `python -m comun.brazos --verificar` pasa
- [x] 4.3 Dejar en `sampling_1/docs/hipotesis.md` y `sampling_1/docs/diseno.md` solo pregunta, H4 pendiente, respuesta al tutor, limitaciones comunes, reparto, fases, estimación y devolución del tutor, con enlaces a cada experimento; verificar que ningún texto de D5 quedó en dos lugares
- [ ] 4.4 Abrir `docs/bitacora.md` de `control`, `h1`, `h2` y `h3` con la entrada de D5 (puntero a `sampling_1`, hipótesis revisada el 1-nov, commit de la separación); anotar la separación en `sampling_1/docs/bitacora.md` con esta sesión como etapa `diseno`; verificar que cada bitácora declara la etapa hipótesis como revisada

## 5. Reportes e informes (sesión: Sonnet)

- [ ] 5.1 Mover `reporte.py` a `comun/` con `--experimento X` y `--todos` (D3): reporte por `hN` (intro, tabla de sus brazos, bandas) y reporte de `sampling_1` (todos los brazos, tiempo-ganancia, tiempo igual, enlaces); mantener el test de idempotencia; verificar que generar dos veces da el mismo archivo salvo la fecha
- [ ] 5.2 Generar los cinco `reporte.html` y comparar la tabla de `sampling_1` con la de `sampling_1/informe/informe.md` § Resultados; verificar que cada Δ, IC, A y veredicto coincide (spec `reporte-visual`, "Mismos números que antes de separar")
- [ ] 5.3 Escribir `h1/`, `h2/`, `h3/informe/informe.md` con su bullet y sus filas de § Resultados, sus limitaciones propias (H3: estudios de `h1`; H2: GOSS descriptivo) y un enlace al informe conjunto; dejar en `sampling_1/informe/informe.md` la comparación y lo común; verificar que `decisiones.md` y `guion.md` siguen citando rutas que existen

## 6. Tokens, documentación del repo e integración (sesión: Sonnet; revisión: Opus en sesión limpia)

- [ ] 6.1 Cambiar `comun/tokens.py` según D6 (declaraciones de todas las bitácoras y de todos los `costos.csv`; sin dueño va a `sampling_1`; si dos la declaran, falla; sin `--experimento`, regenera todos; la etapa de una sesión headless sale del cambio y del grupo, no solo del número de grupo, porque `ETAPA_DE_GRUPO` es la del cambio archivado); verificar con tests de los tres casos y que las filas de `sampling_1/ledger/tokens.csv` anteriores a la separación no cambian
- [ ] 6.2 Actualizar `README.md` (tabla de experimentos con `control`, `h1`–`h3`, `sampling_1`; cómo correr desde la raíz), `CLAUDE.md`, `sampling_1/docs/operacion.md`, `docs/metodo.md` (agregar un experimento: dependencias y registro de brazos) y `plantilla/docs/diseno.md` (sección `## Dependencias`); verificar que `grep -rn sampling-velocidad` solo encuentra lo histórico (archivo de openspec, bitácora, logs de sesiones, `informe` previo y la nota de correspondencia de rutas)
- [ ] 6.3 Escribir la guía para colaboradores en `docs/metodo.md` § Agregar una hipótesis, enlazada desde `README.md` y `CLAUDE.md`: (a) el árbol de `experimentos/` y `comun/` con qué va en cada carpeta (`control`, `hN`, `sampling_1`) y qué no se toca (carpetas y ledgers ajenos); (b) los pasos en orden: tomar el siguiente `hN` libre (identificador válido), copiar `plantilla/`, completar `docs/hipotesis.md` citando las reglas de `control`, declarar `## Dependencias` en `docs/diseno.md` (`control` como mínimo), registrar brazos y estudios en `comun/brazos.py` (y anunciarlo en el commit), `python -m comun.brazos --verificar`, correr con `comun.correr`, `comun.consolidar --experimento hN` y `comun.reporte --experimento hN`, y cómo aparece sola en el reporte de `sampling_1`; (c) cómo usar un estudio de otra hipótesis, con H3 como ejemplo, y H4 (`informado`, `pesado`) como caso concreto de hipótesis nueva; (d) la plantilla trae `## Dependencias` con `control` ya puesta y la referencia a las reglas de `control` en `hipotesis.md`. Verificar en sesión limpia (la revisión del grupo o un subagente sin contexto): siguiendo solo la guía, en un `git worktree` temporal, crear un `h9` de prueba con un brazo ficticio hasta que `comun.brazos --verificar` pase y el reporte de `sampling_1` lo liste sin tocar `h1`–`h3`; descartar el worktree y anotar en la bitácora los pasos donde la guía no alcanzó
- [ ] 6.4 Escribir en `sampling_1/README.md` la correspondencia de rutas viejas y nuevas (para tags y commits anteriores); verificar que cada carpeta de primer nivel del árbol viejo tiene su destino
- [ ] 6.5 Integración: `pytest` completo, `python -m comun.brazos --verificar`, `python -m comun.reporte --todos` y el smoke test de un brazo por experimento en la Mac; verificar que todo pasa en un clon limpio con `DATOS_DIR` apuntando al panel de 20000 filas
- [ ] 6.6 Revisión en sesión limpia con las listas de código e informe de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`; verificar que la entrada tiene fecha, revisor, hallazgos y tokens

## Workflow follow-up

- Subir las predicciones repartidas al bucket nuevo (`$BUCKET/experimentos/<exp>/ledger/predicciones/`) si se va a volver a correr en VM; lo decide Agustina.
- Archivar el cambio con `/opsx:archive` cuando pase la revisión 6.6.
