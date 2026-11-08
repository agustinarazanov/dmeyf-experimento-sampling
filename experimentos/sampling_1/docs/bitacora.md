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
  - la réplica pasa a ser una variante propio, `C-rep`;
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
