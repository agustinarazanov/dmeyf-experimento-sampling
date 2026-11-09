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
  - H2 decidida contra el control, la comparación con `uniforme` como descriptiva y `goss` como variante descriptiva;
  - T como pipeline completo en todas las variantes;
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
- Tarea 2.1: `docs/diseno.md` con 11 variantes, 9 estudios de Optuna (H3 comparte los suyos con `U0.25` y `U0.1`), 110
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
  - la réplica pasa a ser una variante propia, `C-rep`;
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

- `consolidar.py --sanity`: todo OK. 30 finales de la fase 1 en una máquina y un commit; las 8 variantes de H1/H2 con 10
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
    Hay que tenerlo en cuenta al comparar tiempos de variantes que vienen de VMs distintas.
  - ✓ `bagging_fraction` fijo en las 44 filas de H2 (`--sanity`).
  - ✓ 10 semillas en las 12 variantes (incluye C-rep), las mismas 10 que el control.
  - ✓ `apareado.csv`: 10 variantes con media, sd, IC 95% de Δganancia y ΔAUC, semillas ganadas y veredicto.
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
  (`scripts/ledger_parcial.py`), que muestra las variantes que faltan como pendientes. Dos corridas seguidas dan el mismo
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

### 2026-11-02 — fase 4 (tarea 6.6, finales con predicciones)

- VM `sampling-f4` (n2-highmem-8 spot, northamerica-northeast2-b, commit `4a42bc6`), creada 17:02 y **borrada**
  ≈ 18:02 según `ledger/sesiones/vm_f4.log` (`== borrando sampling-f4` / `Deleted`). Tiempo de la fase ≈ 1 h de VM; los
  120 finales corrieron entre 17:05 y 17:49 (≈ 44 min, 0,68 h de entrenamiento sumado). ≈ US$ 0,2.
- `consolidar.py --sanity`: todas las verificaciones OK. 120 finales en `resultados.csv` (12 variantes × 10 semillas),
  un commit (`4a42bc6`), una máquina (`n2-highmem-8`, mismo CPU); 120 parquet en `ledger/predicciones/`, uno por fila.
- Las 120 finales anteriores están en `reemplazadas.csv` (110 de `2bd8a63`, 30 de `79039c9`; algunas semillas tienen
  dos filas viejas por el relanzamiento de C-rep). **Determinismo**: `ganancia_max_201910` y `auc_test` idénticos a
  los reemplazados en los 140 pares variante-semilla; ninguna diferencia que anotar.

### 2026-11-02 — tarea 6.7 (comparación a tiempo igual) y cierre de 6.0

- `src/reporte.py` arma, para cada variante con K ≥ 2, el ensamble de las primeras K semillas (orden de
  `SEMILLAS_FINALES`, K acotado a 10), promediando `prob` fila a fila desde `ledger/predicciones/`. Mide la ganancia al
  corte N* con `comun/ganancia.py` y la compara con Ḡ_C y con el ensamble de las 10 semillas de C. Agrega la figura
  `tiempo_igual.png`. Regenerados `informe/reporte.html`, `informe/figuras/`, `informe/decisiones.md` (A con los
  tiempos de la fase 4: ningún veredicto ni decisión cambia), `informe.md` y `guion.md`.
- Verificado: con una copia del ledger sin un parquet de H3-0.1, esa fila sale "pendiente: faltan predicciones" y el
  HTML fuera de la sección es idéntico. Con el ledger completo no queda ninguna celda pendiente. Dos corridas dan el
  mismo HTML salvo el pie, sin recursos externos. `python -m pytest`: 11 passed.
- Resultado: ensamble de 10 de C = 275,55 M$ contra Ḡ_C = 276,10. Arriba de Ḡ_C quedan U0.5 (+6,05), H3-0.1
  (+3,85), H3-0.25 (+2,75), U0.25 y B0.25 (+0,55). Abajo, U0.1 y B0.1 (−4,95) y U0.05 (−23,65). B0.5 y GOSS tienen
  K = 0. La predicción se cumple en parte: H3 no es la que más rinde.

### 2026-11-02 — cierre informe
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (tarea 6.3).
- Revisor: sesión limpia (Opus, sin contexto de las sesiones del grupo 6).
- Lista: docs/revision.md § 5; ítems ✓ 7/7 después de las correcciones (dos ✗ al empezar).
  - ✓ Cada hipótesis se decide con su regla de `hipotesis.md`: H1 ninguna de las dos (U0.5 indeterminado, U0.05
    pierde), H2 refutada (B0.1 pierde), H3 confirmada (H3-0.25 no pierde). Los números de `informe.md` y `guion.md`
    coinciden con `apareado.csv` y con `decisiones.md` (Δ, IC, A y la tabla a tiempo igual; 275,55 = 276,10 − 0,55).
  - ✗→✓ Afirmaciones sin cita: "la optimización domina T" no citaba nada (ahora: 748 s de Optuna contra 35 s de un
    final en C, `estudios.csv` y `reporte.html`). "Tres fases, 119 corridas válidas" estaba desactualizado: son 129
    filas válidas (9 optimizaciones y 120 finales) y hay una fase 4.
  - ✓ Refutaciones y empates con el mismo peso (tabla completa, H2 refutada y H1 sin decisión en el texto y el guion).
  - ✗→✓ Limitaciones: estaban las semillas y el mes único, pero faltaba la adaptación de H2 (`bagging_fraction` fuera
    de Optuna). Agregada en `informe.md` y en el bloque de limitaciones de `guion.md`.
  - ✓ Guion en 10:00 con hipótesis, diseño, limitaciones, resultados y conclusiones; no explica el baseline.
  - ✓ Bibliografía lista para Zulip.
- Hallazgo menor: la frase a tiempo igual de `informe.md` usaba δ como si fuera el criterio de la predicción, y
  `hipotesis.md` no le pone umbral. Se reescribió como en `decisiones.md` (cinco de ocho arriba de Ḡ_C, δ solo como
  referencia). No cambia ninguna conclusión.
- Corregido: `informe/informe.md` (Diseño, Resultados a tiempo igual, Limitaciones, Conclusiones) y `informe/guion.md`
  (limitaciones). Sin cambios en código, ledger ni `decisiones.md`.
- Tokens: ~20 turnos · ≈ US$ 0,8 (presupuesto US$ 2). `comun/tokens.py` no se corrió en esta sesión.
- Tutor: sin devolución nueva.

### 2026-11-02 — cierre revisión del grupo 2 de `separar-hipotesis` (registro de variantes y código en `comun/`)
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (grupo 2, tareas 2.1–2.5).
- Revisor: sesión limpia (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código); 7 ✓, 2 n/a, ningún ✗.
  - ✓ Smoke `--filas 20000` en la Mac, los cuatro métodos, una fila cada uno y en el ledger del dueño: U0.25 →
    `h1/ledger/exploracion`, B0.25 y GOSS → `h2/ledger/exploracion`, final de H3-0.25 → `h3/ledger/exploracion`
    leyendo `h1/ledger/exploracion/hp/U0.25.json`.
  - ✓ Determinismo: dos finales de H3-0.25 semilla 0 dan el mismo `hash_muestra` (b063898d8598c66e), AUC 201910
    0,82477 y ganancia máx 3.025.000; dos optimizaciones de U0.25, mismo hash (6f080ebbfe0677d9) y AUC 201908.
  - ✓ `optimizar` no lee 201910: el log de `MESES_LEIDOS` muestra 201903–201906 y 201908; 201910 solo en `final`.
  - ✓ Columna obligatoria faltante falla nombrándola (`comun/ledger.py`, `test_falta_una_columna_y_se_nombra`).
  - ✓ `codigo_sucio`: False con el árbol limpio y True con `costos.csv` modificado (filas de esta sesión).
  - ✓ Filas de train: U0.25 registra 2.463 = 0,25 × 9.852 (exacto).
  - ✓ `consolidar` aparea solo semillas en común (`test_apareado_usa_solo_semillas_en_comun`) y el caso con dos
    ledgers pasa (`test_consolidar_con_dos_ledgers`).
  - n/a `vm.sh` borra la VM: los scripts de VM se tocan en la tarea 3.4.
  - ✓ Sin datos en el repo: ningún parquet, csv.gz, sqlite ni `predicciones/` versionado; `exploracion/` ignorado.
  - n/a sin cambios en `informe/`.
- Además: `python -m pytest` 46 passed. `python -m comun.variantes --verificar` sale con código 1 porque faltan
  `control/`, `h2/` y la sección `## Dependencias` de los `diseno.md`: es lo esperado hasta el grupo 4 (4.1, 4.2), y
  muestra que el verificador detecta carpetas y declaraciones faltantes y lista qué se rompe.
- Hallazgos menores (sin corrección, no bloquean): con `--trials 2` el estudio exploratorio de U0.25 retoma un
  SQLite previo con 40 trials ("40 de 2 trials hechos") y el tiempo informado (57,2 s) es el del estudio acumulado; lo
  mismo GOSS (5 trials). Solo afecta corridas exploratorias. El smoke creó `experimentos/h2/ledger/exploracion/`
  (ignorado por git).
- Correcciones: ninguna en código. `tasks.md` no tenía tarea de revisión del grupo 2; se agregó la 2.6 y se marcó.
- Tokens: ~30 turnos · ≈ US$ 0,7 (presupuesto US$ 2). `comun/tokens.py` no se corrió en esta sesión.

### 2026-11-03 — cierre revisión del grupo 3 de `separar-hipotesis` (separación del ledger)
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (grupo 3, tareas 3.1–3.4).
- Revisor: sesión limpia (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código) y § 4 (resultados, solo lo que toca la separación); ningún ✗.
  - n/a smoke, determinismo, `optimizar` sin 201910, columnas obligatorias, `codigo_sucio`, filas de train: el grupo
    3 no toca `comun/` (diff de los cinco commits: solo `scripts/`, `tests/test_separar_ledger.py`, ledgers y
    `tasks.md`); revisados en el grupo 2.
  - ✓ `consolidar` aparea solo semillas en común: `pytest` 49 passed (incluye `test_separar_ledger.py`).
  - ✓ `vm.sh` borra la VM: `trap borrar EXIT` se instala después de la salida de `--en-seco` y antes de
    `instances create`, con `--delete-disks=all`; verificado leyendo el script. No pude ejecutar `bash -n` ni
    `--en-seco` (la sesión headless no tiene permiso para correr scripts de shell); queda la verificación a mano de
    4d55ac4. `lanzar_fase.sh` en la raíz y el atajo de `sampling_1/scripts/` revisados leyendo: rutas y `pgrep` coinciden.
  - ✓ Sin datos en el repo: ningún parquet, csv.gz, SQLite ni `predicciones/` versionado; `predicciones/` y
    `exploracion/` de `control`, `h1`–`h3` y `sampling_1` aparecen como ignorados.
  - ✓ Conservación: `python -m scripts.separar_ledger --origen experimentos/sampling_1/ledger --verificar` → OK.
    La unión de los `resultados.csv` de `control`, `h1`, `h2`, `h3` tiene 129 `id` únicos, iguales a los del
    manifiesto; cada dueño tiene solo sus variantes (control: C, C-rep; h1: U*; h2: B*, GOSS; h3: H3-*).
  - ✓ 3.3 repetida: `python -m comun.consolidar` no cambia ningún archivo versionado; la unión de los `apareado.csv`
    de `h1`–`h3` contra `apareado_previo.csv`: 10 variantes en ambos, diferencia máxima 0 en todas las columnas
    numéricas (Δ, IC, A, n, tiempos) y mismos veredicto, nota y semillas.
  - ✓ Sin `codigo_sucio` (129 False) ni `etapa = exploracion` (120 final, 9 optimizar) en los ledgers repartidos.
  - n/a máquina y commit por fase, réplica del control, H2 con `bagging_fraction` fijo, 10 semillas, VMs borradas y
    gasto: la separación no agrega corridas ni cambia filas.
- Hallazgos menores (sin corrección, no bloquean): `python scripts/separar_ledger.py` falla con
  `ModuleNotFoundError: comun`; hay que usar `python -m scripts.separar_ledger`, como dice su docstring. El final de
  `vm.sh` extrae los ledgers de la VM encima de los locales después del rsync del bucket (comportamiento anterior a
  este cambio).
- Correcciones: ninguna en código. `tasks.md` no tenía tarea de revisión del grupo 3; se agregó la 3.5 y se marcó.
- Tokens: ~15 turnos · ≈ US$ 0,7 (presupuesto US$ 2). `comun/tokens.py` no se corrió en esta sesión.

### 2026-11-03 — grupo 4 de `separar-hipotesis` (documentos por experimento)
- Sesión: `eccad74f-e7e0-4f11-b5b6-110f0c62bcf1` (headless) · modelo: Opus · etapa: **diseno**.
- Separación de los documentos según D5, moviendo los textos tal cual y ajustando solo referencias cruzadas:
  - `control/docs/`: § Control y § Métricas y reglas comunes (`hipotesis.md`); variante `C`, `C-rep`, semillas,
    parámetros fijos, métricas que se calculan, máquina y `## Dependencias` vacía (`diseno.md`). En § Métricas que se
    calculan, los pasos 3 y 6 remiten a `hipotesis.md` en vez de repetir las fórmulas de δ y A (dc6d9ce).
  - `h1/`, `h2/`, `h3/docs/`: la sección de su H, sus variantes y su grilla, y `## Dependencias` (`control`; `h3` además
    `h1`). Estudios compartidos completos en `h1` y con remisión en `h3`. Las limitaciones propias pasaron a su
    `hipotesis.md` (GOSS a `h2`, estudio compartido a `h3`), y lo que quedaba fuera de la grilla de cada H a su
    `diseno.md` (7c34254).
  - `sampling_1/docs/`: pregunta, H4 pendiente, respuesta al tutor, limitaciones comunes, estimación, reparto y fases,
    devolución del tutor, enlaces y `## Dependencias` (`control`, `h1`, `h2`, `h3`) (ffc2e26).
  - Bitácoras de `control`, `h1`, `h2` y `h3` abiertas con puntero a esta, hipótesis revisada el 1-nov y los commits
    de la separación.
- Verificado: `python -m comun.variantes --verificar` sin problemas; `grep` de G, Δ, δ, T, A, N* y veredictos: solo en
  `control/docs/hipotesis.md`; 17 pasajes de D5, cada uno en un solo documento de `docs/`. `informe/informe.md` y
  `informe/reporte.html` de `sampling_1` todavía repiten textos (el reporte se genera de `hipotesis.md`): grupo 5.
- Revisión del grupo 4: pendiente, en sesión limpia.

### 2026-11-03 — cierre revisión del grupo 4 de `separar-hipotesis` (documentos por experimento)
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (grupo 4, tareas 4.1–4.4).
- Revisor: sesión limpia (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 1 (hipótesis) y § 2 (diseño), aplicadas a los documentos de `control`, `h1`–`h3` y
  `sampling_1`; ningún ✗. Base de comparación: `hipotesis.md` y `diseno.md` de `sampling_1` en `dc6d9ce~1`.
  - ✓ Texto conservado: cada sección de la versión previa está, palabra por palabra, en un solo documento nuevo; lo
    que cambia son las referencias cruzadas, los pasos 3 y 6 de § Métricas que se calculan (remiten a `hipotesis.md`
    en vez de repetir δ y T) y los totales de `sampling_1/docs/diseno.md` (once variantes + `C-rep`, 9 estudios, 9 filas
    `optimizar` y 120 `final`), que suman igual que las grillas de `control` (1 + 10 + 10), `h1` (4 + 40), `h2`
    (4 + 40) y `h3` (0 + 20).
  - ✓ Definiciones una sola vez: `grep` de G, Δ, δ, veredictos, T, A y N* en `experimentos/`, `docs/`, `plantilla/`,
    `comun/`, `openspec/specs/`, `README.md` y `CLAUDE.md`: solo `control/docs/hipotesis.md` (y
    `sampling_1/informe/reporte.html`, grupo 5).
  - ✓ § 1: pregunta del tutor con Zulip 208986 y baseline 208135 en `sampling_1`; control completo en `control`; cada
    H con una variable, una métrica, umbral, confirma/refuta/ninguna; adaptaciones declaradas (parámetros de ejecución
    en `control`, `bagging_fraction` en `h2`); H1–H3 no tocan la proporción de clases; regla de "vale la pena" en
    `sampling_1`; 201910 no elige nada.
  - ✓ § 2: cada variante de una `hipotesis.md` está en la tabla de variantes de su `diseno.md` y viceversa; semillas,
    parámetros fijos, máquina (`n2-highmem-8`) en `control`; estimación, reparto y fases, y devolución del tutor (sin
    devolución) en `sampling_1`.
  - ✓ `python -m comun.variantes --verificar`: sin problemas; lista lo que se rompe si falta cada carpeta (`control` →
    todos; `h1` → `h3`, `sampling_1`).
  - ✓ Bitácoras de `control`, `h1`, `h2`, `h3`: puntero a `sampling_1`, hipótesis **revisada** el 1-nov (existe el
    cierre de hipótesis del 1-nov en esta bitácora) y commits de la separación (fd53165, dc6d9ce, 7c34254, ffc2e26
    existen y corresponden).
- Hallazgos: `sampling_1/docs/diseno.md` § Fase 4 nombraba `src/correr.py`, que desde el grupo 2 es
  `comun/correr.py`. La sesión del grupo 4 costó US$ 2,06 (`costos.csv`), por encima del presupuesto de US$ 2.
- Correcciones: ruta anotada como "`src/correr.py` (hoy `comun/correr.py`)". `tasks.md` no tenía tarea de revisión
  del grupo 4; se agregó la 4.5 y se marcó.
- Tokens: ~25 turnos · ≈ US$ 1,1 (presupuesto US$ 2). `comun/tokens.py` no se corrió en esta sesión.

### 2026-11-03 — cierre revisión del grupo 5 de `separar-hipotesis` (reportes e informes)
- Sesión: revisión headless en sesión limpia · modelo: Opus · etapa: **revision** (grupo 5, tareas 5.1–5.3).
- Revisor: sesión limpia (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código, aplicada a `comun/reporte.py`) y § 5 (informe, aplicada a `informe/` de `h1`–`h3`
  y `sampling_1`); ningún ✗.
  - ✓ `pytest` completo: 57 pasan (8 de `tests/test_reporte.py`: idempotencia, hipótesis nueva, ledger vacío).
  - ✓ Determinismo del reporte: `python -m comun.reporte --todos` regenera los cinco `reporte.html`; el `diff` por
    palabra contra HEAD solo cambia el pie (fecha y commit). Se descartó la regeneración.
  - ✓ `python -m comun.variantes --verificar` sin problemas.
  - ✓ No hay datos del dataset en el repo (`git ls-files`). Smoke test, `optimizar` sin 201910, columnas del ledger,
    `codigo_sucio`, filas de train, `consolidar.py` y `vm.sh`: n/a (el grupo no toca el corredor).
  - ✓ Cada veredicto de `h1`–`h3/informe/informe.md` sigue la regla de su `docs/hipotesis.md` (H1 ninguna de las dos
    por U0.25 pierde; H2 refutada por B0.1 pierde; H3 confirmada por H3-0.25 no pierde); Δ e IC de cada fila coinciden
    con `ledger/apareado.csv` de su experimento; A coincide con `reporte.html`.
  - ✓ Refutación (H2) y "ninguna" (H1) con el mismo peso que la confirmación (H3), en los informes propios y en el
    conjunto.
  - ✓ Limitaciones: semilla de Optuna única, un mes de test y un año en los cuatro; adaptación de H2 y GOSS descriptivo
    en `h2`; estudios de `h1` en `h3` y en `h1`; el conjunto remite a ellos.
  - ✓ Enlaces y rutas citadas en `informe.md` de `h1`–`h3` y `sampling_1`, `decisiones.md` y `guion.md` existen.
  - n/a Duración del guion, guion sin baseline y bibliografía: no cambiaron en el grupo 5.
- Hallazgos: `sampling_1/informe/informe.md` § Diseño decía "cada uno con su propio Optuna", falso para H3 (reusa los
  estudios de `h1`; el mismo párrafo cuenta 9 optimizaciones); y un corte de línea suelto en "Detalle / en".
- Correcciones: § Diseño aclara "H3 reusa los estudios de U0.25 y U0.1"; corte de línea unido. `tasks.md` no tenía
  tarea de revisión del grupo 5; se agregó la 5.4 y se marcó.
- Tokens: ~30 turnos · ≈ US$ 0,9 (presupuesto US$ 2). La sesión del grupo 5 costó US$ 1,04 (`costos.csv`).
  `comun/tokens.py` no se corrió en esta sesión.

### 2026-11-03 — grupo 6 de `separar-hipotesis`: verificación de 6.3 y 6.5 (sesión interactiva)
- Sesión: interactiva (la del cambio) · modelo: Opus · etapa: **revision**. El loop headless se bloqueó en 6.3 y 6.5
  porque `git worktree add` y `git clone` fuera de la raíz no están en su lista de permitidos; se hicieron desde acá.
- 6.5, clon limpio en una carpeta temporal con `DATOS_DIR` en `~/datos/experimentos-dmeyf` (panel de 20000 filas):
  `python -m pytest` 61 pasan; `comun.variantes --verificar` sin `PROBLEMA`; `comun.reporte --todos` regenera los cinco;
  smoke `--filas 20000 --trials 2` de `C`, `U0.25`, `B0.5` (optimizar) y `H3-0.25` (final, hp de `h1`), los cuatro rc 0
  y cada fila en `exploracion/` de su dueño. En el repo, los cinco `reporte.html` regenerados solo cambiaban el pie: se
  descartaron.
- 6.3, revisor: subagente `general-purpose` sin contexto en un `git worktree` temporal, siguiendo solo
  `docs/metodo.md` § Agregar una hipótesis: creó `h9` con la variante `U0.02`; `--verificar` pasa, el reporte de
  `sampling_1` (con `--salida`) lista `h9`, y `git diff --stat` no toca `control` ni `h1`–`h3`. Worktree descartado.
- Pasos donde la guía no alcanzó, corregidos en `docs/metodo.md`:
  1. `--verificar` exige `h9` en `## Dependencias` de `sampling_1/docs/diseno.md`, pero la guía decía que `sampling_1`
     no se toca: ahora es la excepción explícita (reglas y paso 3).
  2. "Tiene que decir que no hay problemas": `--verificar` no imprime eso; ahora dice código 0 y ninguna línea `PROBLEMA`.
  3. "Abrir `docs/bitacora.md`" sin formato de primera entrada: ahora dice `### fecha — apertura` bajo `## Entradas`.
  4. `--salida` fuera de `informe/` rompe los enlaces relativos: anotado.
  5. `scripts/etapa.sh` vs `scripts/etapas.sh` ambiguo: ahora dice qué hace cada uno.
- Tokens: subagente ~56.000 tokens, 20 herramientas. Sesiones headless del grupo 6 en `costos.csv`.

### 2026-11-03 — cierre revisión del grupo 6 de `separar-hipotesis` (tokens, documentación e integración)
- Sesión: `069aa733-ba79-4b18-8633-133355d4836b` · modelo: Opus · etapa: **revision** (grupo 6, tareas 6.1–6.5).
- Revisor: sesión limpia (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código, aplicada a `comun/tokens.py` y a la integración) y § 5 (informe); ningún ✗.
  - ✓ `pytest` completo: 61 pasan, incluidos los cuatro de `tests/test_tokens.py` (cada experimento registra lo que
    declara, sin dueño va a `sampling_1`, doble declaración falla, etapa headless por cambio y grupo).
  - ✓ `python -m comun.variantes --verificar`: código 0, ninguna línea `PROBLEMA`.
  - ✓ `python -m comun.tokens` sin `--experimento` regenera los cinco; en `sampling_1/ledger/tokens.csv` solo cambian
    filas del 3-nov (sesiones posteriores a la separación); las anteriores quedan idénticas.
  - ✓ `git grep sampling-velocidad` fuera de lo histórico (archivo de openspec, bitácora, `ledger/sesiones/`, este
    cambio) solo aparece en `CLAUDE.md` y `README.md` (notas del cambio archivado y del renombre), y en `comun/tokens.py`
    y su test (clave del cambio archivado en `ETAPA_DE_GRUPO_POR_CAMBIO`): todo legítimo.
  - ✓ Guía § Agregar una hipótesis enlazada desde `README.md` y `CLAUDE.md`; la plantilla trae `## Dependencias` y la
    referencia a las reglas de `control` en `hipotesis.md`. La prueba con `h9` en worktree y el clon limpio con el smoke
    de una variante por experimento (6.3 y 6.5) están en la entrada anterior; no se repitieron.
  - ✓ Ningún archivo del dataset en `git ls-files`.
  - n/a resto de § 3 (smoke de los cuatro métodos, determinismo, meses leídos, columnas, `codigo_sucio`, filas de train,
    `consolidar.py`, `vm.sh`): el grupo 6 no toca ese código; lo cubren los tests y la revisión del grupo 2.
  - n/a § 5: el grupo 6 no toca `informe/` (el único código que cambia es `comun/tokens.py`); los informes se revisaron
    en el grupo 5.
- Hallazgos: ninguno bloqueante. Observación: varias sesiones del 2 y 3-nov (entre ellas `cf0dc9c0…`, la interactiva
  del cambio) siguen `sin-etapa` en `tokens.csv`; clasificarlas no es del grupo 6.
- Correcciones: ninguna.
- Tokens: ~20 turnos · ≈ US$ 0,6 (presupuesto US$ 2). `comun/tokens.py` corrido en esta sesión.

### 2026-11-08 — cierre revisión del grupo 1 de `renombrar-brazos` (foto previa)
- Sesión: `ec6b3064-be95-4958-8c6c-abbc3cfb580f` · modelo: Opus · etapa: **revision** (grupo 1, tareas 1.1–1.2).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código, aplicada a `scripts/foto_renombre.py` y `scripts/verificar_tokens_renombre.py`)
  y la verificación escrita en cada tarea; el grupo no tiene lista propia ni tarea de revisión en `tasks.md` (se agregó
  la 1.3). Ningún ✗ abierto.
  - ✓ 1.1 foto: en `DATOS_DIR/renombre/antes/` hay un `reporte.html` y sus tablas en CSV por cada uno de los cinco
    experimentos, y un `apareado.csv` por cada experimento que lo tiene en el repo (h1, h2, h3; control y sampling_1 no
    tienen). Los tres `apareado.csv` son idénticos byte a byte a los del repo (`cmp`); cada `reporte.html` difiere del
    del repo solo en el pie (fecha y commit de generación), una línea por archivo.
  - ✓ 1.1 bucket: `DATOS_DIR/renombre/bucket/` tiene `ledger/` y `optuna/`, 969 archivos como dice el commit `c61483c`;
    293 archivos de `ledger/` todavía dicen "brazo", o sea que es la copia previa al renombre que necesita la 2.1. No se
    recontó contra el bucket remoto (el nombre no está en el entorno de esta sesión); lo cubre la 2.5.
  - ✓ 1.1 `git status`: solo `costos.csv` y el JSON de la última sesión headless del grupo 1 (lo que deja
    `scripts/etapa.sh`); los `reporte.html` del repo siguen con la fecha del 3-nov.
  - ✓ 1.2: `comun/tokens.py` solo lee bitácoras, `costos.csv` y transcripts, y no busca "brazo" en ninguno. Se volvió a
    correr `scripts/verificar_tokens_renombre.py`: código 0, los cinco `tokens.csv` idénticos (sampling_1: 47 filas).
  - ✓ `pytest` completo: 61 pasan. Ningún archivo del dataset en el repo (la foto y la copia están en `DATOS_DIR`).
  - n/a resto de § 3 (smoke, determinismo, meses leídos, columnas, `codigo_sucio`, filas de train, `consolidar.py`,
    `vm.sh`): el grupo 1 no toca ese código.
- Hallazgos:
  1. `ETAPA_DE_GRUPO_POR_CAMBIO` en `comun/tokens.py` no tenía `renombrar-brazos`, así que las sesiones headless de
     este cambio (`c4ff6b18…`, `571ade1e…`) salían `sin-etapa` en `tokens.csv`. La 1.2 pasaba igual porque comparaba
     `sin-etapa` con `sin-etapa`.
  2. Al agregar la clave, la verificación de 1.2 falla: su reemplazo ciego convertía la columna `cambio` de
     `costos.csv` en `renombrar-variantes`, cosa que el renombre real no hace (D8 deja el nombre del cambio).
- Correcciones (cambio en `comun/`):
  1. `comun/tokens.py`: `"renombrar-brazos": {"1": "codigo", "2": "codigo", "3": "informe", "4": "informe"}`; ahora
     las dos sesiones del grupo 1 salen `codigo`.
  2. `scripts/verificar_tokens_renombre.py`: el reemplazo saltea `renombrar-brazos` (`(?<!renombrar-)brazo`), igual
     que D8; vuelve a dar código 0 con tokens idénticos. Ojo para la 3.1: el reemplazo de D3 tiene que respetar
     `renombrar-brazos` en `costos.csv`, o esas filas vuelven a `sin-etapa`.
- Tokens: ~35 turnos · ≈ US$ 1,1 (presupuesto US$ 4). `comun/tokens.py` lo corre la verificación de 1.2 sobre una copia;
  el `tokens.csv` del repo se regenera al cierre del cambio.

### 2026-11-08 — cierre revisión del grupo 2 de `renombrar-brazos` (ledgers y código)
- Sesión: `c13ad09a-de57-413c-a76c-29813c1344c4` · modelo: Opus · etapa: **revision** (grupo 2, tareas 2.1–2.5).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código) y la verificación escrita en cada tarea. Ningún ✗ abierto.
  - ✓ 2.1 repo: no quedó respaldo del repo en `DATOS_DIR` (solo `renombre/original/bucket/`), así que se reconstruyó
    desde `b9f6b43^` en `DATOS_DIR/renombre/rev_g2/original_repo/`; `renombrar_columna.py --verificar experimentos`
    contra eso: 296 archivos, 0 errores. `git diff --numstat` del commit: 296 archivos de ledger (287 CSV, 9 `hp/*.json`),
    todos `1 1`. Ningún CSV ni `hp/*.json` de ledger conserva `brazo`.
  - ✓ 2.1/2.5 bucket: `--verificar` sobre `renombre/bucket/` y sobre la copia vuelta a bajar `renombre/bucket_verif/`
    contra `original/bucket/`: 288 archivos, 0 errores en las dos; 959 archivos en cada `ledger/`. Lo único con "brazo"
    en la copia bajada son 5 archivos de `ledger/sesiones/` (texto, fuera de D2; los toca la 3.1).
  - ✓ 2.2: `pytest` completo 75 pasan; `python -m comun.variantes --verificar` sin problemas. `git grep -i brazo` en todo
    lo que no es `.md`, `.html`, `openspec/` ni `ledger/sesiones/` solo da el rechazo de `comun/ledger.py` y su test, la
    clave del cambio en `comun/tokens.py` y los scripts de la migración. `consolidar.py` y `reporte.py` leen los ledgers
    con `lg.leer_csv` (el que rechaza la cabecera vieja). `vm.sh --en-seco` con `sampling_1/scripts/fase4.txt` emite
    `--variante C-rep`.
  - ✓ 2.3: los 13 tests de `h3/sensibilidad_muestra` pasan; `busqueda.cargar_grilla()` regenera las 20 configuraciones
    con el sha256 de `grilla_06.json` (`7ecaa079…`). En `grilla_06.json` "brazo" solo estaba en texto, no como clave.
    Las huellas de `resumen.json` (`comun/ganancia.py`, `datos.py`, `baseline.py`, `tests/test_ganancia.py`) coinciden
    con `shasum` de hoy; `sha256_scripts_originales` de `procedencia.json` son de los scripts originales de Martín.
  - ✓ Smoke `--filas 20000 --trials 3` en la Mac, los cuatro métodos, una fila cada uno en el ledger del dueño con
    columna `variante` y todas las columnas: U0.25 → h1, B0.5 y GOSS → h2, final H3-0.25 (semilla 100003) → h3.
  - ✓ Determinismo: el final de H3-0.25 corrido dos veces da hash `b063898d…`, AUC 201910 0,832417 y ganancia
    3.850.000 iguales.
  - ✓ Meses leídos: `optimizar` lee 201903–201906 y 201908; solo el final lee 201910.
  - ✓ Filas de train: U0.25 2463 = 0,25 × 9852.
  - ✓ `codigo_sucio`: `commit_y_sucio()` sin cambios en el grupo (ignora `/ledger/`, por eso las filas salen `False` con
    `costos.csv` modificado); `consolidar` (`test_apareado_usa_solo_semillas_en_comun`) y la columna faltante
    (`test_falta_una_columna_y_se_nombra`) siguen cubiertos por tests.
  - ✓ `vm.sh`: el grupo solo renombra la quinta columna de la lista y comentarios; el borrado de la VM no cambia.
  - ✓ Ningún archivo del dataset en `git ls-files`.
- Hallazgos:
  1. `README.md:43`: el comando de smoke pasaba `--semilla 100003` a `--etapa optimizar`, que el corredor rechaza
     (la semilla de Optuna es 0). Anterior al cambio.
  2. D8 nombra solo `scripts/renombrar_columna.py`, pero `reemplazar_d1.py`, `foto_renombre.py` y
     `verificar_tokens_renombre.py` también nombran "brazo"; la verificación final de la 3.1 los habría marcado.
  3. El mensaje de `b9f6b43` dice 339 archivos; el commit tiene 296 de ledger (más el script). Los números del bucket
     (288) coinciden.
  4. Los smoke de esta revisión dejaron filas y `hp/*.json` en `exploracion/` (ignorado por git), como los de la 2.4.
- Correcciones:
  1. `README.md:43`: se saca `--semilla 100003` (la 4.1 reescribe el README igual).
  2. `design.md` D8: suma los demás scripts de la migración a las excepciones.
- Tokens: ~40 turnos · ≈ US$ 1,6 (presupuesto US$ 4). `comun/tokens.py` no se corrió: el `tokens.csv` se regenera al
  cierre del cambio (4.2).

### 2026-11-08 — renombre de «brazo» a «variante» (`renombrar-brazos`)

- Qué cambió: la columna y la clave `brazo` de los ledgers pasaron a `variante`, `comun/brazos.py` a `comun/variantes.py`
  y el texto del repo dice «variante» donde decía «brazo». Los números no cambian: `apareado.csv` y las tablas de cada
  `reporte.html` coinciden con la foto previa (diferencia 0).
- Commits: ledgers y bucket `b9f6b43` (2.1) y `7b0545c` (2.5, bucket subido con `gsutil rsync`); código y tests `6ea0074`
  (2.2); paquete de Martín `f4566a3` (2.3); texto `4a456c8` (3.1); reportes regenerados `611bb2f` (3.2).
- Lo que sigue diciendo «brazo»: la historia de git (los commits anteriores) y el tag `corridas-v1`.
- Un clon anterior al renombre no consolida: `comun/ledger.py` rechaza una cabecera `brazo` nombrando el archivo. Hay que
  actualizar el clon y volver a bajar el ledger del bucket renombrado.

### 2026-11-08 — cierre revisión del grupo 3 de `renombrar-brazos` (texto y specs)
- Sesión: `9a0db73f-cd1c-442b-bd24-a418b22396f2` · modelo: Opus · etapa: **revision** (grupo 3, tareas 3.1–3.3).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 5 (informe) en lo que el grupo toca, más la verificación escrita en cada tarea. La lectura
  del README como alguien que no conoce el repo queda para la 4.2, con el README nuevo. Ningún ✗ abierto.
  - ✓ 3.1 excepciones: `git grep -n -i brazo | grep -v renombrar-brazos` solo da archivos de D8: el rechazo en
    `comun/ledger.py` y `tests/test_ledger.py`, los seis scripts de la migración, el escenario «Ledger con la columna
    vieja» (también en el delta de `h3-semillas-optuna`), las entradas del renombre y de las revisiones del renombre en
    las bitácoras, y `openspec/specs/` (cambia al archivar). `comun/tokens.py` y los JSON/`costos.csv` de
    `ledger/sesiones/` solo nombran `renombrar-brazos`.
  - ✗→✓ 3.1 concordancia: el grep de artículos de D3 no da nada, pero la búsqueda de adjetivos masculinos cerca de
    «variante» encontró seis: «variantes apareados» (`comun/consolidar.py`, mensaje de consola), «una variante
    ficticio» (`docs/metodo.md` y `openspec/changes/archive/2026-11-03-separar-hipotesis/tasks.md` 6.3), «variante
    propio» (`control/docs/diseno.md`, `sampling_1/docs/bitacora.md`), «una variante desconocido falla nombrándolo»
    (`separar-hipotesis/tasks.md` 2.1). Corregidos. Quedan en transcripts JSON de `ledger/sesiones/` (registro crudo,
    no se tocan).
  - ✓ 3.2: `python -m comun.consolidar` (control 21/20/0, h1 44/62/4, h2 44/40/4, h3 20/20/2) y `comun.reporte --todos`
    regenerados; `foto_renombre.py despues` contra `antes`: los 16 CSV (4 `apareado.csv`, 12 tablas) con mismas
    columnas tras cambiar brazo→variante y diferencia máxima 0. Los `apareado.csv` del repo no cambian en git; el
    `--word-diff` de los cinco `reporte.html` solo cambia hora y commit, y ningún PNG cambia.
    `git diff --word-diff 4a456c8^ HEAD` de los `informe.md` no toca números.
  - ✓ 3.3: las cinco bitácoras tienen la entrada del renombre con fecha, commits (`b9f6b43`, `7b0545c`, `6ea0074`,
    `f4566a3`, `4a456c8`, `611bb2f`, todos existen), historia de git y `corridas-v1` (el tag existe), y que un clon viejo
    no consolida (cubierto por `test_cabecera_brazo_se_rechaza_nombrando_el_archivo`).
  - ✓ `pytest` 75 pasan; `python -m comun.variantes --verificar` sin problemas.
  - n/a reglas de decisión, citas, refutaciones, limitaciones, guion y bibliografía: el grupo no cambia contenido del
    informe (verificado con el `--word-diff` de 3.2).
- Hallazgos:
  1. Seis concordancias masculinas que el grep de artículos de D3 no cubre (adjetivo después del sustantivo).
  2. D8 no nombraba `scripts/reemplazar_d3.py`, `scripts/concordar_d3.py` ni `openspec/specs/` (hasta archivar), que
     el grep final sí devuelve.
  3. `tasks.md` no tenía tarea de revisión propia del grupo 3 (la 4.2 revisa los grupos 3 y 4).
- Correcciones:
  1. Las seis concordancias, a mano.
  2. `design.md` D8 suma esos dos scripts y `openspec/specs/` hasta el archivo.
  3. `tasks.md`: se agrega la 3.4 (esta revisión, hecha); la 4.2 sigue abierta para el grupo 4 y el README.
- Tokens: ~35 turnos · ≈ US$ 1,3 (presupuesto US$ 4). `comun/tokens.py` no se corrió: se regenera en la 4.2.

### 2026-11-08 — cierre revisión del grupo 4 de `renombrar-brazos` (README)
- Sesión: `2c594c00-7d10-45a2-9010-963efd4f5495` · modelo: Opus · etapa: **revision** (grupo 4, tarea 4.1, y repaso del
  grupo 3 en lo que cambia la 4.1).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 5 (informe) aplicada al README, más la verificación escrita en la 4.1 y la lectura del README
  como alguien que no conoce el repo. Ningún ✗ abierto.
  - ✓ 4.1 secciones de D7 en orden (pregunta y respuesta corta, resultados, experimentos, aportes, qué sigue, estructura
    y cómo correr). `python scripts/verificar_readme.py` sale con 0 antes y después de las correcciones: 10 filas
    idénticas a `sampling_1/informe/informe.md` § Resultados, 11 números del texto presentes, 21 enlaces que existen.
  - ✗→✓ Cada hipótesis se decide con la regla escrita: la respuesta corta decía que H3-0.1 tiene «la misma» ganancia que
    el control «dentro de δ = 2%», una equivalencia que no es la regla (*no pierde*: cota inferior ≥ −δ) y que no se
    cumple (cota superior 8,41 > δ = 5,52). Reescrita como «no pierde ganancia contra el control (la cota inferior del
    IC queda arriba de −δ)».
  - ✓ Cada afirmación cita su fuente: resultados y tiempo igual citan `informe.md` § Resultados; aportes, contra
    `h3/sensibilidad_muestra/README.md` (7 de 10 muestras eligen la configuración del control; las otras tres, ±10 M$
    de ruido de semilla) y `Experimentos h3 y h4/resumen_completo_de_experimentos.md` (50 semillas, todas las bajas);
    qué sigue, contra las propuestas de `h3-semillas-optuna` (8 réplicas, `H3-0.05`, `H3R-0.1`) e `incorporar-aportes`
    (H4, `exploratorios/`, 07 y 08 de Martín).
  - ✓ Refutaciones y empates con el mismo peso: la tabla tiene las diez variantes; el mapa da H2 refutada y H1 ni una ni
    otra; la respuesta corta dice qué pierde.
  - ✓ Limitaciones: la grande (una sola optimización de Optuna) está en la respuesta corta; el resto se remite al
    informe con enlace.
  - n/a guion, baseline en el guion y bibliografía: el README no es el guion.
  - ✓ Lectura de alguien que no conoce el repo: se entiende; Ḡ_C aparecía sin definir y ahora dice «la ganancia media
    del control». Los comandos de «Cómo correr» usan flags que existen (`comun.datos --filas`, `comun.correr --metodo
    --tasa --etapa --filas`, `consolidar`/`reporte --experimento`, `variantes --verificar`) y los scripts nombrados
    están en `scripts/`.
  - ✗→✓ Repaso del grupo 3: el README nuevo decía «brazo» (§ Estructura), fuera de D8. Ahora nombra el cambio
    `renombrar-brazos`. `git grep -n -i brazo | grep -v renombrar-brazos` da los archivos de D8 y además
    `ledger/sesiones/g3_aplicar_20261108T182343.json`, que copia los comandos del renombre.
  - ✓ `pytest` 75 pasan; `python -m comun.variantes --verificar` sin problemas; `comun/tokens.py --experimento
    sampling_1` regenerado.
- Hallazgos:
  1. Respuesta corta con una equivalencia («la misma ganancia, dentro de δ») que no es la regla y que el IC no cumple.
  2. «brazo» en § Estructura del README, fuera de las excepciones de D8.
  3. D8 no nombraba los registros de sesión que copian comandos del renombre.
  4. Ḡ_C sin definir en el README; una línea de más de 120 caracteres.
- Correcciones:
  1. y 4. README reescrito en esas frases; `verificar_readme.py` sigue en 0.
  2. README nombra el cambio en lugar de la palabra.
  3. `design.md` D8 suma los registros de `ledger/sesiones/` posteriores al reemplazo de D3 (no se reescriben).
- Tokens: ~25 turnos · ≈ US$ 1,0 (presupuesto US$ 4). `comun/tokens.py` corrido.

### 2026-11-08 — cierre revisión del grupo 1 de `h3-semillas-optuna` (hipótesis y diseño)
- Sesión: `e16c0e12-db59-4e10-a044-7b41ea926a16` · modelo: Opus · etapa: **revision** (grupo 1, tareas 1.1 y 1.2).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 1 (sobre `h3/docs/hipotesis.md` § H3 con réplicas) y § 2 (sobre `h3/docs/diseno.md`,
  `control/docs/diseno.md` § Grilla y `sampling_1/docs/diseno.md` § Reparto y fases, fase 5); ítems ✓ 18/18 después de
  las correcciones, ningún ✗ abierto.
  - ✓ Pregunta del tutor y control: no cambian; la sección nueva remite a `control/docs/hipotesis.md`.
  - ✓ Una variable por hipótesis (r_opt en `H3-0.05`, el reescalado en `H3R-0.1`, la réplica como fuente de varianza).
  - ✓ Métrica y umbral numérico en cada regla: H3 con réplicas (cota inferior del IC de Welch ≥ −5,52 M$), A contra B
    (cota > 0 M$ y mediana de `feature_fraction`; IC que contiene 0 y Ḡ_{C,0} contra la mediana de Ḡ_{C,k}),
    `H3-0.05` (no pierde y A ≥ 8; la regla compuesta es la de D4) y `H3R-0.1` (IC t de D con 7 g.l. contra 0).
  - ✓ Sin zona gris sin nombre: la regla 1 cubre *gana*/*no pierde* contra *pierde*/*indeterminado*; A y B son
    excluyentes y el resto es «mecanismo sin resolver»; `H3-0.05` y `H3R-0.1` tienen la tercera salida nombrada.
  - ✓ Adaptaciones declaradas (réplicas con semilla TPE = semilla de muestra = k; 8 VMs de una persona en lugar de una
    por persona); ninguna toca la proporción de clases; δ, N\* y R = 8 fijos antes de correr, sin usar 201910 para
    elegir nada; el texto coincide con D1–D5 de `design.md`.
  - ✓ Grilla: 8 × 10 × 5 = 40 celdas, 3 hechas, 37 nuevas, 28 estudios; tiempos 87 + 35 + 216 min ≈ 5,6 h; ~47 min por
    VM de réplica (1045 s de Optuna + 50 × 35 s); semiamplitud de Welch con s = 4, 8 contra 8: ±4,29 (5 contra 5: ±5,83).
  - ✓ Cada variante de la hipótesis está en la grilla y en la tabla de variantes; control apareado por las mismas 10
    semillas finales; 40 trials y espacio iguales en cada réplica; máquina `n2-highmem-8`.
  - ✓ Reparto: `fase5_r1…r7` (5 celdas cada una) + `fase5_r0` (2) = 37 celdas, sin huecos ni solapes; todo Agustina.
  - ✗→✓ Horas y costo: la fase 5 tenía horas pero no costo en US$ ni la preparación de cada VM.
  - ✓ Tutor: sin devolución nueva sobre este cambio.
  - ✓ Enlaces relativos de los seis documentos tocados (script ad hoc, 0 rotos) y secciones citadas (§ Grilla, § Reparto
    y fases, § Corridas perdidas, § Estudios de Optuna compartidos); `python -m comun.variantes --verificar` sin
    problemas; `h1/ledger/hp/U0.05.json` existe (dependencia de k = 0).
- Hallazgos:
  1. La fase 5 de `sampling_1/docs/diseno.md` no estimaba el costo en US$ ni sumaba la preparación de las 8 VMs.
  2. En `H3-0.05`, «A ≥ 8 con T como mediana entre réplicas» no decía que la T de `C` también es la mediana de sus 8.
- Correcciones:
  1. La fase 5 suma **Costo**: ≤ 10 h de VM con la preparación (≤ 0,5 h × 8), ≈ US$ 6 en el peor caso, dentro del trial.
  2. `h3/docs/hipotesis.md` regla 3: A = T(`C`) / T(`H3-0.05`), cada T como mediana entre sus 8 réplicas.
- Tokens: ~25 turnos · contexto promedio ~58.000 por turno · ≈ US$ 1,0 (presupuesto US$ 4). `comun/tokens.py` corrido.
- Tutor: —

### 2026-11-08 — grupo 2 de `h3-semillas-optuna` implementado (código, sesión headless)
- Sesión: `73253550-be37-45c3-88cf-df31d827f7ec` · modelo: Sonnet · etapa: **codigo** (tareas 2.1–2.5, commits
  `fc523d7`, `49d8df1`, `df04f6b`). No dejó entrada propia; la clasifica la revisión del grupo. 72 turnos, contexto
  promedio ~124.000 por turno (supera el objetivo de 100.000): cinco tareas de código en una sola sesión, con smoke,
  tests y consolidación del ledger real dentro de la conversación.

### 2026-11-08 — cierre revisión del grupo 2 de `h3-semillas-optuna` (código)
- Sesión: `a5f2b686-74a5-48f3-a6a1-f3e427f640d1` · modelo: Opus · etapa: **revision** (grupo 2, tareas 2.1–2.5).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código) y la verificación escrita en cada tarea. Ningún ✗ abierto.
  - ✓ Smoke `--filas 20000 --trials 3` en la Mac, los cuatro métodos, una fila (o `hp/*.json`) cada uno en el ledger
    del dueño: U0.25 → h1, B0.5 y GOSS → h2, `opt-muestra 0.1 --replica 3` (estudio `U0.1@3`) → `h3/ledger/exploracion/`
    con `replica_opt = 3`, y los finales de H3-0.1 y H3R-0.1 en la réplica 3 → h3. `h1/` sin tocar (`git status`).
  - ✓ Réplica no habilitada: `bagging 0.5 --replica 2` falla nombrando B0.5 y las variantes que admiten réplicas.
  - ✓ Reescalado: H3R-0.1 usa `min_data_in_leaf` 111 = round(35 × √10) sobre el `hp` de `U0.1@3`.
  - ✓ Determinismo: el final de H3-0.1 réplica 3, semilla 100003, corrido dos veces da hash `b063898d…`, AUC 201910
    0,862507 y ganancia 3.575.000 iguales.
  - ✓ Meses leídos: `optimizar` (también con `--replica`) lee 201903–201906 y 201908; solo el final lee 201910.
  - ✓ Filas de train: `U0.1@3` 985 = 0,1 × 9852 (± 0,1%).
  - ✓ Columnas: `replica_opt` es obligatoria en `COLUMNAS` y en la clave; `test_falta_una_columna_y_se_nombra` pasa.
    Los 12 CSV consolidados de `control`, `h1`, `h2` y `h3` que tocó `fc523d7` solo suman `replica_opt = 0`: el resto de
    cada tabla es idéntico al de `3d8cf0c` (comparado con pandas, mismas filas).
  - ✓ `codigo_sucio`: `commit_y_sucio()` no cambió en el grupo; las filas del smoke salen `False` (solo `ledger/` sucio).
  - ✓ `consolidar.py`: `python -m comun.consolidar` sobre el ledger real no cambia ningún archivo; `apareado.csv` de
    las hipótesis no cambió desde `3d8cf0c` y no hay `replicas.csv` (ninguna variante con dos réplicas todavía). El
    apareo por semillas en común, la descomposición exacta, las réplicas incompletas y el apareado H3R − H3 están
    cubiertos por `tests/test_replicas_ledger.py`. Welch entre medias por réplica y IC t de D con k − 1 g.l. coinciden
    con D5.
  - ✓ `vm.sh`: la sexta columna (`replica`) y el `-` de variante se pasan bien en la VM y en `--en-seco`; el borrado
    de la VM no cambia. Cada corrida escribe archivos propios (`corridas/`, `hp/<estudio>@k.json`, curvas,
    predicciones), así que 8 VMs sincronizando el mismo ledger del bucket no se pisan.
  - ✗→✓ `lanzar_fase.sh --en-seco` con las 8 listas: 65 corridas (7 × 9 + 2) = 37 celdas y 28 estudios, sin repetir
    (`tests/test_fase5.py`, 6 pasan). La verificación de cuota miraba solo `N2_CPUS` de la región.
  - ✓ `python -m pytest` 128 pasan; `python -m comun.variantes --verificar` sin problemas.
  - ✓ Ningún archivo del dataset ni base de Optuna en `git ls-files`.
- Hallazgos:
  1. `scripts/lanzar_fase.sh` verificaba la cuota regional `N2_CPUS` pero no la global `CPUS_ALL_REGIONS`, que en una
     cuenta de trial suele ser la que limita: con 8 VMs × 8 vCPU podía pasar la verificación y crear solo algunas.
  2. `pytest` a secas (el ejecutable del PATH) falla al importar `comun` con 15 errores de colección; `python -m pytest`
     pasa. No es del grupo; conviene usar siempre `python -m pytest`.
  3. La sesión de implementación (`73253550…`) no dejó entrada en la bitácora y superó el objetivo de contexto.
- Correcciones:
  1. `lanzar_fase.sh` verifica también `CPUS_ALL_REGIONS` (de `gcloud compute project-info describe`) y no lanza
     ninguna VM si alguna de las dos cuotas no alcanza.
  2. Entrada de etapa **codigo** para la sesión de implementación (arriba).
- Tag `corridas-v2` creado sobre el commit de esta revisión (lo pushea Agustina).
- Tokens: ~45 turnos · contexto promedio ~60.000 por turno · ≈ US$ 1,6 (presupuesto US$ 4). `comun/tokens.py` corrido.
- Tutor: —

### 2026-11-09 — grupo 3 de `h3-semillas-optuna` (corridas)

- Fase 5 completa: 8 listas en VMs paralelas, 65 corridas, ledgers consolidados (8 réplicas × 10 semillas en las 5
  variantes, todo `n2-highmem-8`, sin código sucio ni filas inválidas). Detalle y tiempos contra D3 en
  [`h3/docs/bitacora.md`](../../h3/docs/bitacora.md). Pendiente: revisión de resultados (3.3).
- Sesión de la consolidación: `3421053b-9538-41ab-85e2-6322b4379378` (Sonnet, headless) · etapa: **corridas**
  (clasificada en la revisión 3.3).

### 2026-11-09 — cierre revisión del grupo 3 de `h3-semillas-optuna` (corridas)
- Sesión: `111f125f-b1eb-409a-9712-50f47987aa6c` · modelo: Opus · etapa: **revision** (grupo 3, tareas 3.1–3.2).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que corrió y consolidó el grupo).
- Lista: docs/revision.md § 4 (resultados) sobre los ledgers de `control` y `h3`, y la verificación de 3.1 y 3.2.
  Ningún ✗ abierto.
  - ✓ Máquina y commit: las 341 filas de `h3` y las 98 de `control` son `n2-highmem-8`; todo lo de la fase 5 es
    `dcd06d6` (los k = 0 previos de `C`, `H3-0.1` y `H3-0.25` conservan `2bd8a63`/`4a42bc6` de su fase).
  - ✓ Sin `codigo_sucio`, sin `etapa = exploracion` en los `resultados.csv`; todas las filas `valida = True`.
  - ✓ Filas de train: estudios `U0.05@k` 25.344, `U0.1@k` 50.687 y `U0.25@k` 126.718 (= r × 506.871); `C@k` y todos
    los finales de `H3-*` usan las 506.871 completas.
  - ✓ Control repetido: `C-rep` (fase 2, otra VM) reproduce exacto, limitación ya declarada el 2-nov; además `C` tiene
    ahora 8 réplicas de optimización.
  - n/a `bagging_fraction` de H2: el grupo no tocó `h2/ledger` ni `h1/ledger` (`git diff dcd06d6 adb62a2` vacío).
  - ✓ Semillas: las 40 celdas variante × réplica (`C`, `H3-0.05`, `H3-0.1`, `H3-0.25`, `H3R-0.1` × k = 0…7) tienen
    las 10 semillas; 7 estudios `@k` por tasa en `h3` y 8 en `control`.
  - ✓ `apareado.csv` de `h3` con media, sd, IC 95%, semillas ganadas y veredicto para las 4 variantes; `replicas.csv`
    de `h3` (4 variantes contra `C` y `H3R-0.1 − H3-0.1`, 8 réplicas × 80 semillas, sin notas de incompletas) y de
    `control`. `python -m comun.consolidar` vuelto a correr no cambia ningún archivo.
  - ✗→✓ VMs borradas: los 8 `vm_f5_r*.log` terminan en `DONE` y `Deleted`; `gcloud compute instances list` no
    muestra ninguna `sampling-*` (solo `desktop-jr`, `TERMINATED`, que no es del experimento). Gasto: no estaba
    anotado; estimado ahora en la bitácora de `h3`.
- Hallazgos:
  1. Gasto de la fase 5 sin anotar.
  2. La bitácora de `h3` daba Optuna `C` 915 s como media de las réplicas 1…7 (es la media con k = 0; la de 1…7 es
     938 s) y «50 celdas finales» (son 40); los finales de `H3-0.05` promedian ≈ 20 s, no ≈ 23.
  3. Los logs r3–r5 tienen errores de `gsutil`/`tar` al traer archivos de `C@5` que r5 estaba subiendo (carrera entre
     VMs que sincronizan el mismo bucket). Los archivos locales están completos: el CSV se lee y los parquet de
     predicciones de los cuatro experimentos abren todos. No estaba anotado.
  4. Optuna de `C@k` va de 644 a 1194 s entre réplicas con la misma máquina; parte es la VM y parte los `hp` que
     elige cada TPE. A tener en cuenta en la comparación a tiempo igual (4.2).
  5. `comun/tokens.py` dejaba sin etapa la sesión de consolidación `3421053b…`.
- Correcciones: entradas de `h3/docs/bitacora.md` (cifras, errores de sincronización y gasto ≈ US$ 1,3 estimado desde
  el ledger a US$ 0,19/h); clasificación de `3421053b…` como **corridas** (arriba). Nada en código ni en ledger.
- Tokens: ~30 turnos · contexto ~55.000 por turno · ≈ US$ 1,1 (presupuesto US$ 4). `comun/tokens.py` corrido.
- Tutor: —

### 2026-11-09 — grupo 4 de `h3-semillas-optuna` implementado (código, sesión headless)
- Sesión: `fb2dbf0b-78c4-43e0-8f9d-1c4b52bbd2f0` · modelo: Sonnet · etapa: **codigo** (tareas 4.1–4.2, commits
  `343d8f7`, `296865c`). No dejó entrada propia; la clasifica la revisión del grupo. 37 turnos, contexto promedio
  ~82.000 por turno, US$ 1,13 (`costos.csv`).

### 2026-11-09 — cierre revisión del grupo 4 de `h3-semillas-optuna` (comparación limpia)
- Sesión: `e042cbd2-25f3-48a3-9fd1-1e9c74d5919f` · modelo: Opus · etapa: **revision** (grupo 4, tareas 4.1–4.2).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 3 (código) sobre `comun/reporte.py`, `comun/variantes.py`, sus tests y el manifiesto
  `h3/sensibilidad_muestra/exploratorio.json`, más las verificaciones de 4.1 y 4.2. Ningún ✗ abierto.
  - n/a Smoke de los cuatro métodos, `optimizar` sin 201910, columnas obligatorias del ledger, `codigo_sucio`, filas
    de train, apareo de `consolidar.py` y `vm.sh`: el grupo no tocó el corredor, el ledger, `consolidar` ni los
    scripts (`git diff dcd06d6 HEAD` en `comun/`, `scripts/` y `tests/` solo cambia `reporte.py`, `variantes.py` y
    sus tests). Esos ítems se cerraron en la revisión del grupo 2.
  - ✓ Determinismo: `python -m comun.reporte --todos` corrido tres veces; `tabla_resultados.md` idéntica y en los
    HTML solo cambia la hora del pie. El bootstrap con `default_rng(20261108)` tiene su test de dos corridas
    idénticas.
  - ✓ No hay datos del dataset en el repo (`git ls-files` sin parquet ni gz); los CSV de Martín son tablas agregadas
    de 4 a 10 filas.
  - ✓ 4.1: los `sha256` (LF) de los tres CSV de `h3/sensibilidad_muestra/resultados/` coinciden con `sha256_lf` de
    `procedencia.json`; las columnas que declara el manifiesto existen en sus CSV; `--verificar` pasa y el test de
    manifiesto sin advertencia falla nombrando carpeta y campo.
  - ✓ 4.2: `pytest` 134 verdes (133 + 1 de esta revisión); los tres tests pedidos (exploratorio sin CSV, variante de
    una réplica, bootstrap idéntico) están y pasan. Revisados a mano `tiempo_igual_replicas` (K_k contra el
    presupuesto del control de la misma réplica, IC t entre réplicas) y `bootstrap_tiempo_igual` (corte N\*·n_b/n,
    mismo remuestreo para todas las variantes, Ḡ_C como media de las 10 semillas): coinciden con D6.
  - ✗→✓ Bloque A coherente: en las filas de H3, Ḡ es la media entre réplicas (`reporte.py`, `fila_bloque_a`) y T y A
    medianas entre réplicas, pero la cabecera solo daba Ḡ_C de la réplica 0 y nada lo decía: 277,79 − 276,10 no da
    ni el Δ de réplica 0 (3,74) ni el de réplicas (1,87), y en la figura las H3 se comparaban con el control de la
    réplica 0.
- Hallazgos:
  1. Fuente mezclada en Ḡ, T y A del bloque A (arriba), en la tabla, el HTML y la figura de tiempo contra ganancia.
  2. Bloque B: las dos columnas `delta` del manifiesto no miden lo mismo (en `08_…` es ganancia en $, en `07_…` es
     AUC). La tabla nombra el CSV de cada una, pero el informe (5.1–5.2) tiene que decirlo al citarlas.
  3. El pie de cada HTML cita el commit `HEAD` al generar, que es el anterior al commit que lo guarda; es lo esperable
     y no se toca.
  4. La sesión de implementación `fb2dbf0b…` no tenía entrada ni etapa (arriba).
- Correcciones: `comun/reporte.py` marca con (R=n) la Ḡ de las variantes con réplicas, agrega Ḡ_C con réplicas
  (275,92 M$, R = 8) a la referencia del control, escribe sobre la tabla del bloque A de dónde salen Ḡ, T y A, y en la
  figura dibuja el control con réplicas (media, mediana de T y rango) junto al de la réplica 0. Test nuevo en
  `tests/test_reporte.py`; reportes y `tabla_resultados.md` regenerados (las cifras no cambian). Ninguna cifra del
  ledger cambió.
- Tokens: ~47 turnos · contexto ~69.000 por turno · ≈ US$ 1,8 (presupuesto US$ 4). `comun/tokens.py` corrido.
- Tutor: —

### 2026-11-09 — grupo 5 de `h3-semillas-optuna` (informe, sesión headless)
- Sesión headless de aplicación del grupo 5 (`5555c3ce-e19b-44b4-b52e-7ced72269b7d`, id agregado en la revisión) ·
  modelo: Opus · etapa: **informe** (tareas 5.1–5.2).
- 5.1: `h3/informe/informe.md` con los veredictos de D4 (detalle en la bitácora de `h3`); `scripts/verificar_informe_h3.py`.
- 5.2: `informe/informe.md` reescrito: § Diseño suma la fase 5; § Resultados copia los bloques A y B de
  `tabla_resultados.md` (27 líneas de tabla idénticas, comprobado por script) y los comenta (H3 confirmada con
  réplicas, mecanismo (B), `H3-0.05` confirmada, `H3R-0.1` no cambia, varianza de Optuna, tiempo igual con intervalo);
  § Limitaciones, § Conclusiones y § Qué sigue (H4 y `incorporar-aportes`) actualizadas. Atiende el hallazgo 2 de la
  revisión del grupo 4: al citar a Martín dice que la `delta` de `08_…` es ganancia y la de `07_…` es AUC.
  `guion.md` con los bloques de H3 con réplicas, varianza y exploratorios.
- README: § Resultados apunta a `tabla_resultados.md` y al informe (sin la tabla vieja de la réplica 0), respuesta corta
  con Δ con réplicas, `h3` confirmada también con réplicas, § Qué sigue solo con `incorporar-aportes`.
  `scripts/verificar_readme.py` pasa a comparar contra `tabla_resultados.md`: 25 números del texto en la tabla (salvo
  identificadores listados en `NO_RESULTADOS`), 22 enlaces existen; un número cambiado lo hace salir con 1. Los enlaces
  del informe conjunto (13) y del de `h3` (7) existen.
- Pendiente: revisión en sesión limpia de la etapa informe (5.3).

### 2026-11-09 — cierre revisión del grupo 5 de `h3-semillas-optuna` (informe)
- Sesión: `8240957c-794f-41de-9371-672f20033d70` · modelo: Opus · etapa: **revision** (grupo 5, tareas 5.1–5.2).
- Revisor: sesión limpia headless (Opus, sin contexto de la sesión que implementó el grupo).
- Lista: docs/revision.md § 5 (informe) sobre `informe/informe.md`, `informe/guion.md`, `h3/informe/informe.md` y la
  respuesta corta del README. Ningún ✗ abierto.
  - ✓ Reglas escritas: los cuatro veredictos de `h3/informe/informe.md` § Veredictos siguen las reglas 1–4 de
    `h3/docs/hipotesis.md` § Predicciones y reglas (cotas contra −5,52 M$; (A) exige *gana* y no se cumple; (B) se
    cumple con Ḡ_{C,0} = 276,10 < mediana 276,49 M$, comprobado en `control/ledger/replicas.csv`; `H3-0.05` con
    A ≥ 8; `H3R-0.1` con el IC t de D). Sin reglas nuevas.
  - ✗→✓ Cada afirmación con fuente: `verificar_informe_h3` (107 números, 0 sin fuente) y `verificar_readme` (25
    números, 22 enlaces) pasan; los 748 s de Optuna del control están en `control/ledger/estudios.csv`. Pero «el
    control tuvo mala suerte», usado como explicación de por qué se achica Δ (informe conjunto, informe de `h3`, guion
    y README), no lo sostienen las fuentes: Ḡ_{C,0} = 276,10 M$ está debajo de la mediana pero **arriba de la media**
    con réplicas (275,92 M$), y Δ baja porque la media con réplicas de `H3-0.1` (278,22 M$) queda debajo de su
    réplica 0 (276,10 + 4,07). Corregido abajo.
  - ✓ Refutaciones y empates con el mismo peso: H2 refutada, H1 ninguna de las dos, `H3R-0.1` *no cambia* con la
    predicción (*mejora*) dicha como no cumplida, `H3-0.05` «salía *gana*; con réplicas ya no».
  - ✓ Limitaciones: semillas y suerte de Optuna (réplicas solo en `C` y H3, R = 8 cerrado, 50 semillas no alcanzan),
    un solo mes de test (201910, con el bootstrap de clientes) y la adaptación de H2 (`bagging_fraction`, remitida al
    informe de `h2` y nombrada en el guion).
  - ✓ Guion: 0:00–10:00, pregunta → hipótesis → diseño → limitaciones → resultados → conclusión → qué sigue.
  - ✓ El guion no explica el baseline (lo nombra y lo sigue).
  - ✓ Bibliografía lista para Zulip (LightGBM, Friedman, Optuna, TPE, Bolaños 208135). No se posteó.
- Hallazgos:
  1. «El control tuvo mala suerte» leído como causa (arriba): el veredicto *apoya (B)* es correcto por la regla, pero
     su nombre sugiere que el control salió bajo en la réplica 0, y salió arriba de su media; la suerte estaba en las
     H3.
  2. La entrada del grupo 5 no tenía id de sesión, así que `comun/tokens.py` la dejaba `sin-etapa`.
- Correcciones: el veredicto *apoya (B)* queda; se aclara que es el nombre de la regla pre-registrada y que la suerte de
  la réplica 0 estaba más en las H3 que en el control, en `h3/informe/informe.md` (regla 2 y conclusión),
  `informe/informe.md` (Mecanismo y Conclusiones), `guion.md` (H3 con réplicas) y README (respuesta corta). Solo cifras
  que ya estaban en las fuentes; los dos verificadores pasan después del cambio. Id `5555c3ce…` agregado a la entrada
  del grupo 5.
- Tokens: la implementación (`5555c3ce`) tuvo 46 turnos y ~103.500 de contexto por turno, arriba del objetivo; lo más
  probable (estimación del revisor) es la lectura y reescritura de dos informes largos con tablas de 10 columnas.
  Esta revisión: ~20 turnos, ≈ US$ 1 (presupuesto US$ 4). `comun/tokens.py` corrido.
- Tutor: —

### 2026-11-09 — cuatro hipótesis (`incorporar-aportes` 1.1 y 1.2)

- Sesión headless `f0b04f89-178e-4a6c-80fb-07a78749b44f` · modelo: Opus · etapa `hipotesis`.
- `experimentos/h4/` nuevo (1.1). `docs/hipotesis.md` pasa a cuatro hipótesis: la H4 del 1-nov queda como registro
  («reemplazada el 9-nov») y apunta a `h4`; se suman los contrastes principales (`H3-0.1`, `H4H-0.1`, `H4F-0.05`) y dos
  limitaciones comunes (test ya mirado, comparaciones múltiples). `docs/diseno.md`: índice con `h4`, fase 6 según D6
  (listas `fase6_r<k>` y `fase6_luis_<estrategia>`, 18 VMs, `corridas-v3`) y la nota de que h4 entra a
  `## Dependencias` junto con su registro (grupo 2), para que `--verificar` siga pasando.
- Verificación: los 36 enlaces relativos de los seis documentos tocados existen; `python -m comun.variantes
  --verificar` sale con 0 y sin `PROBLEMA`.
- Pendiente: revisión en sesión limpia (1.3).
