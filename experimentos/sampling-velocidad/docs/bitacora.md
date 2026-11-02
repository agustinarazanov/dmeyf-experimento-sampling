# Bitácora — Sampling_1

Una entrada por sesión de Claude Code y una por cada cierre de etapa, de la más vieja a la más nueva. La etapa que se
declara acá es la que usa `comun/tokens.py` para clasificar la sesión.

## Formato de cierre de etapa

```
### AAAA-MM-DD — cierre <etapa>
- Sesión: <id de sesión de Claude Code> · modelo: <Opus | Sonnet>
- Revisor: <sesión limpia / subagente general-purpose / integrante>
- Lista: docs/revision.md § <n>; ítems ✓ <k>/<total>
- Hallazgos: <qué encontró la revisión>
- Corregido: <qué se cambió por la revisión>
- Tokens: <turnos> turnos · contexto promedio <n> por turno · ≈ US$ <x> (objetivo < 100.000 por turno)
- Tutor: <id de Zulip y resumen, si hubo devolución>
```

## Entradas

### 2026-11-01 — planificación (sesión previa)
- Sesión: `08a28c05-6f60-44ea-af46-c4d51105c4b7`, que corrió en el proyecto `dmeyf2026` y no en este repo. Se cuenta
  como etapa `planificacion`.
- Produjo `openspec/changes/experimento-sampling-velocidad/` (proposal, specs, design, tasks) y `CLAUDE.md`.

### 2026-11-01 — apertura: etapa hipótesis
- Sesión: `d2e5b603-2b55-42d4-9898-ef129dce5e4b` · modelo: Opus · etapa: **hipotesis**.
- Tareas 1.1 a 1.5 de `tasks.md`: `docs/hipotesis.md`, `docs/revision.md`, esta bitácora y el borrador del post a
  Zulip (`docs/zulip/01_hipotesis.md`).
- Pregunta del tutor tomada de Zulip 208986 (Joaquín Aramendía, 1-nov, `Experimentos - Lunes > sampling_1`).

### 2026-11-01 — cierre hipótesis
- Sesión: `d2e5b603-2b55-42d4-9898-ef129dce5e4b` · modelo: Opus
- Revisor: dos subagentes `general-purpose`, sin contexto, en pasadas sucesivas.
- Lista: docs/revision.md § 1. Primera pasada ✓ 3/10. Segunda pasada ✓ 10/10.
- Hallazgos de la primera pasada:
  - faltaban en el control los rangos de Optuna, las 100 iteraciones y el uso de las semillas;
  - H2 no aislaba una sola variable;
  - H2 y H3 se decidían con dos métricas;
  - había zonas grises entre confirma y refuta;
  - la regla de "un σ_C" era casi trivial con 10 semillas;
  - **el corte de envíos se elegía en 201910**;
  - T se definía distinto según la hipótesis;
  - la condición de tiempo de H2 caía fuera de la grilla.
- Corregido, con decisiones del equipo:
  - no inferioridad con δ = 2% de Ḡ_C (cota inferior del IC ≥ −δ) y un veredicto *indeterminado* con nombre;
  - corte N* elegido en 201908;
  - H2 decidida contra el control, la comparación con `uniforme` como descriptiva y `goss` como brazo descriptivo;
  - T como pipeline completo en todos los brazos;
  - rangos de Optuna propios;
  - D1 y D2 de `design.md` actualizados para coincidir.
  
  Las observaciones menores de la segunda pasada (frontera monótona, muestra de Optuna en H1, origen de δ, arranque de
  GOSS) se aplicaron. Informes: `revision_hipotesis.md` y `revision_hipotesis_2.md` en el scratchpad de la sesión, no
  versionados.
- Tokens: 26 turnos hasta la segunda revisión · contexto promedio 87.648 por turno (máximo 108.724) · 28.831 de salida.
  El objetivo de < 100.000 se cumple. El costo en US$ queda para `comun/tokens.py` (tarea 4.7).
- Tutor: el post `docs/zulip/01_hipotesis.md` está listo y sin enviar, con la consulta sobre la adaptación de H2.
- Pendientes que llegaron del grupo al cierre:
  - Una propuesta de quedarse con el 20% de CONTINUA y el 100% de las BAJA con selección de instancias, y otra con el
    10% de CONTINUA y pesos. Es territorio de Sampling_2. La variante con peso de 10× conserva la proporción efectiva
    en la pérdida y podría ser H4. Hay que decidir si se coordina con Sampling_2 o si se reabre la compuerta.
  - ¿El pipeline de 15 minutos corre todo en GCP, o entrena en GCP y predice en la laptop? Es una decisión de la
    segunda entrega; quedó como limitación en `hipotesis.md`.

### 2026-11-01 — apertura: etapa diseño
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus · etapa: **diseno**.
- Tarea 2.1: `docs/diseno.md` con 11 brazos, 9 estudios de Optuna (H3 comparte los suyos con `U0.25` y `U0.1`), 110
  finales más 10 de réplica del control, ≈ 6 h de VM (≈ 15 h en el peor caso, ≈ US$ 9) y el reparto por persona.
  D7 de `design.md` se actualizó para que coincida.
- Revisión preliminar con la lista § 2, a cargo de un subagente `general-purpose` sin contexto: ✓ 7/8, con el ítem de
  la devolución del tutor en n/a. No encontró errores aritméticos.
- Corregido por la revisión:
  - **parámetros de ejecución** (`deterministic`, `force_col_wise`, `feature_pre_filter`): declarados como adaptación
    en `hipotesis.md` § Control;
  - **T**: suma de las duraciones de los trials más un `Dataset`, para que no dependa de cortes de la VM spot. Se
    llevó también a `hipotesis.md`;
  - **plataforma de CPU**: fija con `--min-cpu-platform`, y el modelo de CPU queda en el ledger;
  - **reparto**: los finales de `U0.25` y `U0.1` pasan a la VM que corre sus estudios;
  - **g.l.**: n − 1 cuando faltan semillas;
  - **limitaciones nuevas**: estudios compartidos entre H1 y H3, y GOSS cuando `learning_rate` es chico;
  - **paralelo**: Martín no espera la calibración.
- Pendiente para cerrar la etapa: 2.2 (consola GCP: trial, cuota, template, zona, plataforma de CPU, precio spot) y
  2.3 (repo en GitHub). `README.md` y `.gitignore` ya están escritos, sin publicar.

### 2026-11-01 — reorganización del repo (layout D0)
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus · etapa: **diseno**.
- Pedido de la sesión de planificación (`dmeyf2026`), confirmado por Agustina. El repo tiene ahora una carpeta por
  experimento: `comun/`, `experimentos/sampling-velocidad/`, `plantilla/` y `docs/` en la raíz. La decisión es D0 de
  `design.md`.
- Se movieron `hipotesis.md`, `diseno.md`, esta bitácora y `zulip/` a `experimentos/sampling-velocidad/docs/`.
  `docs/revision.md` queda en la raíz, compartido, y se creó `docs/metodo.md`.
- `tasks.md`: las rutas quedaron alineadas con D0 y se agregó la tarea 2.0. Las tareas 1.x y 2.1 conservan su contenido;
  solo cambió dónde viven. `scripts/tokens.py` pasa a ser `comun/tokens.py`.

### 2026-11-01 — tareas 2.2 y 2.3
- **2.2, GCP**: no hay un template `n2-highmem-8`. La VM se crea desde `to-064ram-08vcpu`, sobrescribiendo la máquina
  con `n2-highmem-8` y fijando `--min-cpu-platform="Intel Ice Lake"`, en `northamerica-northeast2-b`.
  - Prueba: `prueba-sampling-n2` se creó con Ice Lake y spot, y se borró junto con su disco (19:19 a 19:21).
  - Cuotas: `CPUS_ALL_REGIONS` 32 y `N2_CPUS` 100 en la región.
  - Trial: alta el 11-oct, confirmada por Agustina; vence el 9-ene-2027.
  - Detalle en `docs/diseno.md` § Máquina.
- **2.3, repo**: es privado, en `agustinarazanov/dmeyf-experimento-sampling`. El prefijo `dmeyf` lo pidió Agustina para
  los repos de la materia; el nombre no admite `/`. Por decisión de Agustina, no se mandaron invitaciones a Martín y
  Luis. El README no menciona el dataset y `.gitignore` excluye los datos.

### 2026-11-01 — cierre diseño
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus
- Revisor: subagente `general-purpose` sin contexto. Pasó dos veces: la preliminar (ver la apertura) y esta final.
- Lista: docs/revision.md § 2. Pasada final ✓ 7/7 aplicables; el ítem del tutor es n/a. Al recalcular, coincidieron
  todos los números.
- Hallazgos de la pasada final:
  - **bloqueante**: la réplica del control chocaba con la regla de saltear las corridas que ya tienen fila;
  - **bloqueante**: el template borra la VM spot con su disco, y el SQLite de Optuna no funciona sobre gcsfuse;
  - **menores**: el proyecto del template y de las cuotas no estaba nombrado; faltaba la verificación de Ice Lake en
    las zonas `-a` y `-c`; quedaban pendientes de Martín y Luis sin listar; la bitácora decía US$ 8 y el diseño US$ 9.
- Corregido:
  - la réplica pasa a ser un brazo propio, `C-rep`;
  - el SQLite es local y se copia al bucket después de cada trial; el panel y las filas del ledger también se suben,
    y una VM nueva los baja;
  - quedaron nombrados el proyecto y las zonas, con la lista de pendientes de Martín y Luis antes de la fase 1;
  - US$ 9 en los dos documentos.
  - La carga más baja de Luis queda como margen para reintentos.
- Tokens: 61 turnos · contexto promedio 125.991 por turno (máximo 165.868) · 59.180 de salida. **No se cumple el
  objetivo** de < 100.000. Pesaron la reorganización del repo a mitad de etapa, que reabrió `tasks.md` con
  `/opsx:update`, y la configuración de `gcloud` y `gh` en la misma sesión. El costo en US$ queda para
  `comun/tokens.py` (tarea 4.7).
- Tutor: sin devolución. El post `zulip/01_hipotesis.md` sigue sin enviar.

### 2026-11-01 — apertura: etapa código
- Sesión: `457cc09a-a528-48c5-849e-322b3261b914` · modelo: Sonnet · etapa: **codigo**.
- Tareas 3.1 a 4.7 de `tasks.md`: `comun/` (datos, baseline, ganancia, ledger, tokens), `src/` (muestreo, métodos,
  correr, consolidar), `scripts/` (vm.sh, graficar.py) y `docs/operacion.md`.

### 2026-11-01 — 4.9 verificada a mano (sesión de planificación, Fable)
- `scripts/etapa.sh` corrió el grupo 4 tres veces: dos con un bug de comillas (sesiones de 1 turno, US$ 0,004–0,01) y
  una buena (7 turnos, US$ 0,40) que hizo la 4.6 en una VM real y bloqueó 4.8 y 4.9. En las tres, `costos.csv` recibió
  su fila con modelo y costo, y el `BLOQUEADO` cortó `etapas.sh` con código 2 (antes del parche de `exit $?`, con 0:
  hallazgo 1 de la revisión del script).
- Revisión del script en sesión limpia (Opus, sin contexto): 7 hallazgos confirmados y 4 posibles, todos aplicados o
  anotados en comentarios de `scripts/etapa.sh`.
- Regla nueva: las tareas "Revisar" las hace y marca la sesión de revisión; el aplicador no las toca. Si en un grupo
  solo queda la revisión, `etapa.sh` saltea la sesión de aplicar.

### 2026-11-01 — cierre codigo
- Sesión: `4ad957d6-9aae-41a0-8cdc-48b10bd3252d` · modelo: Opus · etapa: **revision** (tarea 4.8).
- Revisor: sesión limpia (Opus, sin contexto de la implementación).
- Lista: docs/revision.md § 3; ítems ✓ 9/9 (uno tras corregir).
  - ✓ Smoke `--filas 20000 --trials 3` en la Mac: `uniforme 0.5`, `bagging 0.5`, `goss 1` y `opt-muestra 0.5`,
    `optimizar` + `final` semilla 7, todos rc 0 y una fila cada uno en `ledger/exploracion/corridas/` (commit `909f4ae`).
    Logs en `ledger/exploracion/_rev_logs/`.
  - ✓ Determinismo: `uniforme 0.5` semilla 7 dos veces → hash `339fc6ce1e905e1e`, AUC 201908 0,879142, AUC 201910
    0,858614 y ganancia 2.750.000 idénticos.
  - ✓ `optimizar` lee solo `201903–201906, 201908` (línea `MESES_LEIDOS` del log) en los cuatro métodos; `final` agrega
    201910. El corredor además falla si `optimizar` toca 201910.
  - ✓ Columnas obligatorias: `test_falta_una_columna_y_se_nombra` pasa; las filas `final` no tienen nulos.
  - ✓ `codigo_sucio`: True con el árbol sucio en la Mac. ✗ en la VM (ver hallazgo), corregido.
  - ✓ `filas_train` U0.5 = 4.926 = 0,5 × 9.852 (exacto).
  - ✓ Apareado solo en semillas comunes: `test_apareado_usa_solo_semillas_en_comun` y `test_consolidar_de_punta_a_punta`
    pasan (pytest 9/9).
  - ✓ `vm.sh` borra la VM: `trap borrar EXIT` con `--delete-disks=all`; tras el smoke de la 4.6
    (`ledger/exploracion/smoke_vm.txt`) no queda ninguna `sampling-*` en `gcloud compute instances list`.
  - ✓ Sin datos en el repo: `git ls-files` no tiene parquet, gz, db ni el crudo (solo `ledger/tokens.csv`).
- Hallazgos: `vm.sh` manda `git archive HEAD` sin `.git`, así que en la VM `commit_y_sucio()` devolvía `sin-git` y
  `codigo_sucio=False` (se ve en las filas U0.25 del smoke de VM). Las filas reales iban a quedar sin commit
  trazable. El aviso de árbol sucio de `vm.sh` además decía lo contrario de lo que pasa (a la VM va HEAD limpio).
- Corregido: `src/correr.py` usa `COMMIT_REPO` cuando no hay git (el archive de HEAD está limpio por construcción);
  `scripts/vm.sh` exporta `COMMIT_REPO=$COMMIT` y el aviso dice que los cambios sin commitear no viajan. Probado sin
  git, con y sin la variable; falta verlo en una VM real en la primera tanda de la fase 1 (columna `commit` ≠
  `sin-git`).
- Tokens (`comun/tokens.py`): etapa código `457cc09a` 37 turnos · contexto promedio 121.193 · ≈ US$ 1,71 (**supera el
  objetivo**); `65a5d7fd` 7 · 39.337 · US$ 0,18; `b5e73664` 25 · 53.308 · US$ 0,40; sesiones de 1 turno de
  `etapa.sh` (bug de comillas) ≈ US$ 0,23 en total. Esta revisión: ~25 turnos · ~47.000 por turno · ≈ US$ 1
  (presupuesto US$ 2). Sin clasificar: `02a8a58c`, `3e0ced8f`, `34a0d6ac`.
- Tutor: sin devolución.

## 2026-11-02 · incidente en la fase 3 (VM `sampling-f3`)

- Qué pasó: las fases 1 y 2 terminaron solas (ledger traído, VMs borradas). En la fase 3, a las 00:38:55 UTC
  `unattended-upgrades` actualizó paquetes y reinició `google-guest-agent`; en ese momento murió el proceso de la
  corrida completo (el `nohup bash remoto.sh` y su python) sin traza en `corrida.log` ni `remoto.log`. GOSS quedó con
  1 trial de 40 y `~/estado` nunca se escribió, así que `vm.sh` siguió esperando ~14 h con la VM ociosa (≈ US$ 2,7 de
  spot). Las corridas de bagging 0,5/0,25/0,1 ya estaban en el ledger y no se perdieron.
- Qué se hizo: en la misma VM se apagaron los timers de apt y se relanzó solo `goss` (optimizar + 10 semillas) como
  unidad transitoria de systemd (`systemd-run`), fuera de la sesión de usuario; Optuna retomó desde el trial 1. El
  supervisor `vm.sh` local siguió vivo y cierra la fase cuando aparezca DONE.
- Cambio: `vm.sh` ahora lanza la corrida remota con `systemd-run` y desactiva `apt-daily*` y `unattended-upgrades`
  al arrancar la VM. Pendiente: que `vm.sh` detecte un `~/estado` vacío con la VM sin procesos de python por más de N
  minutos y lo declare FALLO en vez de esperar para siempre.
- Tiempos de GOSS: como el reinicio corta la optimización, el `tiempo_optimizacion_s` de GOSS sale de la corrida
  retomada (39 trials + 1 previo); se anota para la sección de tiempos.
- Segundo tropiezo, propio: edité `vm.sh` mientras el supervisor de la fase 3 seguía corriendo; bash lee el script a
  medida que avanza, así que al llegar a "trayendo el ledger" leyó el archivo nuevo desplazado y falló con un error de
  sintaxis; el trap borró la VM. GOSS ya había terminado (40 trials y 10 semillas) y `remoto.sh` sube el ledger al
  bucket tras cada configuración, así que no se perdió nada: se trajo con `gcloud storage rsync`. Regla: no editar
  un script de bash mientras corre; si hace falta, reemplazarlo con un archivo nuevo (`mv`), nunca reescribirlo.
- Grupo 5, dos sesiones headless (US$ 0,48 y 0,14). La primera consolidó, escribió `consolidar.py --sanity`, vio que
  faltaba la réplica del control y relanzó la fase 2 con `C-rep`; como la VM arranca sin ledger, volvió a correr
  también U0.5 y U0.05 (los estudios de Optuna se retoman, así que solo repitió las 10 semillas de cada uno). Eso dejó
  la misma semilla dos veces, con dos commits, y la clave del ledger incluía el commit: el apareado rompió. La segunda
  sesión además se trabó porque antepuso `PYENV_VERSION=... python`, forma que la lista de permisos no cubre.
- Decisión: la clave del ledger ya no incluye el commit (spec `ledger-resultados` y `comun/ledger.py`); una repetición
  con código más nuevo reemplaza a la anterior. Resultado: 22 filas de U0.5/U0.05 en `reemplazadas.csv`, `--sanity`
  pasa completo y `C-rep` reproduce al control exacto (ΔAUC = 0, Δganancia = 0: LightGBM es determinista con la misma
  semilla, hilos y máquina). El prompt de `etapa.sh` ahora pide `python` a secas.

## 2026-11-02 · cierre del grupo 5 (sanity de resultados, tarea 5.4)

- `consolidar.py --sanity`: todo OK. 30 finales de la fase 1 en una máquina y un commit; los 8 brazos de H1/H2 con 10
  finales; filas de train dentro de ±0,1% de la tasa; sin `codigo_sucio`; `bagging_fraction` fijo en las 44 filas de H2;
  ninguna corrida exploratoria en `resultados.csv`; un solo tipo de máquina (`n2-highmem-8`); `C-rep` reproduce al
  control exacto (ΔAUC = 0, Δganancia = 0).
- VMs borradas (según `ledger/sesiones/vm_f{1,2,3}.log`, "Deleted"): `sampling-f1`, `sampling-f2`, `sampling-f3`.
- Gasto del trial: no se puede leer desde la sesión (la consola de facturación no es accesible). Solo hay una
  estimación sin medir: el incidente de la fase 3 costó ≈ US$ 2,7 de VM ociosa. Agustina debe confirmar el saldo en
  Billing antes del análisis.

### 2026-11-02 — cierre corridas
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (tarea 5.5).
- Revisor: sesión limpia (Opus, sin contexto de las sesiones del grupo 5).
- Lista: docs/revision.md § 4; ítems ✓ 6/8 (dos con desvío anotado, ninguno invalida filas).
  - ✓ (con desvío) Una máquina (`n2-highmem-8`) en las 120 finales; fase 1 y fase 3 con un solo commit (`2bd8a63`).
    La fase 2 mezcla commits: U0.1 y U0.25 en `2bd8a63`, U0.5, U0.05 y C-rep en `79039c9`. `git diff --stat
    2bd8a63 79039c9` solo toca `consolidar.py`, `vm.sh`, `fase2.txt`, `etapa.sh` y documentos; `correr.py`,
    `metodos.py`, `muestreo.py` y `comun/` no cambian, así que el código que entrena es el mismo.
  - ✓ Sin `codigo_sucio`, sin `etapa = exploracion`, sin commit `sin-git`; 129 filas, todas `valida`.
  - ✓ Filas de train = tasa × 506.871 en U (253.436, 126.718, 50.687, 25.344); B, GOSS y H3 final con r = 1 usan las
    506.871 completas, como corresponde.
  - ✗ El control "entre dos personas": `C-rep` corrió en otra VM (fase 2), pero `persona = agustina` en C y C-rep.
    Reproduce exacto (ΔAUC = 0, Δganancia = 0), lo que prueba el determinismo entre VMs, no entre personas.
    Tiempo de entrenamiento: C 33,7 s (sd 1,4) y C-rep 31,6 s (sd 0,3), un 6% de diferencia entre VMs del mismo tipo.
    Hay que tenerlo en cuenta al comparar tiempos de brazos que vienen de VMs distintas.
  - ✓ `bagging_fraction` fijo en las 44 filas de H2 (`--sanity`).
  - ✓ 10 semillas en los 12 brazos (incluye C-rep), las mismas 10 que el control.
  - ✓ `apareado.csv`: 10 brazos con media, sd, IC 95% de Δganancia y ΔAUC, semillas ganadas y veredicto.
  - ✗ VMs borradas: sí (`vm_f{1,2,3}.log`). Gasto: **no anotado**, falta leerlo en Billing.
- Hallazgos: los dos ✗ y el desvío de commits de arriba. `consolidar.py --sanity` da OK en todo; su chequeo de
  "un commit" solo mira la fase 1.
- Corregido: nada en código ni en ledger. Se agregó la tarea 5.5 en `tasks.md`, que no existía. Pendientes humanos en
  `ledger/sesiones/bloqueo.txt`: el gasto del trial y aceptar C-rep como réplica entre VMs o pedir a Martín o Luis
  que corran las 10 finales de C en su cuenta.
- Tokens: ~20 turnos · ≈ US$ 0,8 (presupuesto US$ 2). `comun/tokens.py` no se corrió en esta sesión.
- Tutor: sin devolución.
- Decisión (2-nov, sesión principal, por la regla del 1-nov de que todas las fases corren en la cuenta de Agustina):
  **se acepta `C-rep` como réplica entre VMs** y se declara como limitación en el informe; no se pide una corrida a
  otro integrante. `diseno.md` § Grilla y `docs/revision.md` § 4 quedan redactados así.
- Gasto del trial, **estimado** desde los tiempos de vida de las VMs (n2-highmem-8 spot ≈ US$ 0,19/h más el disco de
  256 GB): fase 1 ≈ 0,7 h, fase 2 ≈ 0,75 h, relanzamiento de la fase 2 (C-rep) ≈ 0,4 h, fase 3 ≈ 15,3 h de las cuales
  ≈ 14 h fueron la VM ociosa del incidente. Total ≈ 17 h ≈ **US$ 3,5 a 4**, de los cuales ≈ 2,7 son el incidente. La
  cifra exacta hay que leerla en Google Cloud Billing (cuenta `Mi cuenta de facturación`); el trial de US$ 300 queda
  prácticamente intacto. El smoke de la etapa 4 y el bucket suman centavos.

### 2026-11-02 — grupo 6 (reporte, decisiones, informe, tokens)

- Etapa: análisis e informe, sesión headless (Opus). Revisor: pendiente (6.3, sesión limpia).
- 6.0: `src/reporte.py` escribe `informe/reporte.html`. Probado con el ledger completo y con uno parcial de la fase 1
  (`scripts/ledger_parcial.py`), que muestra los brazos que faltan como pendientes. Dos corridas seguidas dan el mismo
  archivo y no tiene recursos externos. **Queda sin marcar** porque la comparación a tiempo igual calcula K pero no el
  ensamble: el ledger guarda curvas de ganancia y no predicciones. Ver `ledger/sesiones/bloqueo.txt`.
- 6.1: figuras en `informe/figuras/`, decisiones en `informe/decisiones.md`: H1 ninguna de las dos, H2 refutada, H3
  confirmada. Valen la pena H3-0.1 y H3-0.25.
- 6.2: `informe/informe.md` y `informe/guion.md`.
- 6.4, tokens contra octubre (`comun/tokens.py`, 28 sesiones en `ledger/tokens.csv`; a esta sesión le falta el costo
  porque todavía no cerró):

  | | contexto promedio por turno | turnos | US$ equivalentes | US$ por turno |
  |---|---|---|---|---|
  | octubre (`dmeyf2026`) | 400.000 | 2.509 | 694 | 0,28 |
  | este experimento, todas las sesiones | 131.275 | 530 | 31,37 | 0,059 |
  | este experimento, sin la planificación | 74.589 | 359 | 14,87 | 0,041 |

  El promedio está ponderado por turnos. Conclusión sobre el método: el contexto por turno bajó un 67% en total y un
  81% sin la planificación. Las sesiones por etapa quedan debajo del objetivo de 100.000. Lo superaron la planificación
  (250.283, Fable), el diseño (127.918) y la primera sesión de código (121.193). El costo por turno bajó unas 5 veces.
  Lo que más ayudó fue cortar por etapa con `/clear`, mandar las salidas largas a archivo y que las corridas las hagan
  las VMs y no la conversación. Lo que infla el contexto son las sesiones largas e interactivas de diseño. Siete
  sesiones quedaron `sin-etapa`; hay que clasificarlas a mano.
