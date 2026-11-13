# Bitácora — h3

Una entrada por sesión de Claude Code y una por cada cierre de etapa, de la más vieja a la más nueva. La etapa que se
declara acá es la que usa `comun/tokens.py` para clasificar la sesión.

## Entradas

### 2026-11-03 — apertura por la separación de Sampling_1
- Historia anterior al 2-nov: [`sampling_1/docs/bitacora.md`](../../sampling_1/docs/bitacora.md). Este experimento
  sale de la separación de Sampling_1 en `control`, `h1`, `h2`, `h3` y `sampling_1` (cambio `separar-hipotesis`).
- Etapa hipótesis: **revisada** el 1-nov-2026 en Sampling_1 (cierre de hipótesis de su bitácora). Los textos de
  `docs/hipotesis.md` y `docs/diseno.md` se movieron tal cual desde `sampling_1/docs/`; solo se ajustaron las
  referencias cruzadas.
- Commits de la separación: ledger en fd53165 (3.1–3.2); documentos en dc6d9ce (4.1), 7c34254 (4.2) y ffc2e26 (4.3).
- Etapas de diseño, código, corridas y análisis: cerradas en Sampling_1 antes de la separación; sus filas están en
  `ledger/` (`H3-0.25`, `H3-0.1`). No tiene estudios propios: lee `U0.25` y `U0.1` del ledger de `h1`.

### 2026-11-08 — renombre de «brazo» a «variante» (`renombrar-brazos`)

- Qué cambió: la columna y la clave `brazo` de los ledgers pasaron a `variante`, `comun/brazos.py` a `comun/variantes.py`
  y el texto del repo dice «variante» donde decía «brazo». Los números no cambian: `apareado.csv` y las tablas de cada
  `reporte.html` coinciden con la foto previa (diferencia 0).
- Commits: ledgers y bucket `b9f6b43` (2.1) y `7b0545c` (2.5, bucket subido con `gsutil rsync`); código y tests `6ea0074`
  (2.2); paquete de Martín `f4566a3` (2.3); texto `4a456c8` (3.1); reportes regenerados `611bb2f` (3.2).
- Lo que sigue diciendo «brazo»: la historia de git (los commits anteriores) y el tag `corridas-v1`.
- Un clon anterior al renombre no consolida: `comun/ledger.py` rechaza una cabecera `brazo` nombrando el archivo. Hay que
  actualizar el clon y volver a bajar el ledger del bucket renombrado.

### 2026-11-08 — hipótesis y diseño de las réplicas (`h3-semillas-optuna` 1.1)

- Sesión headless de aplicación del grupo 1, etapa `hipotesis`.
- `docs/hipotesis.md` suma § H3 con réplicas de optimización: δ = 5,52 M$ y N\* = 3.300 fijos, R = 8 cerrado, y las
  reglas de D4 (H3 con réplicas, A contra B, `H3-0.05`, `H3R-0.1`), cada una con umbral numérico y métrica. La hipótesis
  de la réplica 0 y su veredicto no cambian.
- `docs/diseno.md` suma las variantes `H3-0.05` y `H3R-0.1`, § Réplicas de optimización (nombres `@k` y regla de
  dueños: `U{r}` es de `h1`, `U{r}@k` de `h3`), § Grilla con réplicas (D3) y `## Dependencias` actualizada (`U0.05`
  de `h1`). `python -m comun.variantes --verificar` sin problemas.
- Pendiente: revisión en sesión limpia (1.3). Ninguna corrida con réplicas antes de ese cierre.

### 2026-11-08 — cierre revisión de hipótesis y diseño de las réplicas (`h3-semillas-optuna` 1.3)

- Revisión en sesión limpia (`e16c0e12-db59-4e10-a044-7b41ea926a16`, Opus) con `docs/revision.md` § 1 y § 2: ningún ✗
  abierto. Detalle en [`sampling_1/docs/bitacora.md`](../../sampling_1/docs/bitacora.md) (cierre del grupo 1 de
  `h3-semillas-optuna`).
- Corregido: la regla de `H3-0.05` aclara A = T(`C`) / T(`H3-0.05`) con cada T como mediana entre sus 8 réplicas; la
  fase 5 de `sampling_1/docs/diseno.md` suma el costo (≈ US$ 6 en el peor caso).
- Las corridas con réplicas quedan habilitadas después del grupo 2 y del tag `corridas-v2`.

### 2026-11-09 — corridas con réplicas y consolidación (`h3-semillas-optuna` 3.1 y 3.2)

- Las 8 listas `fase5_r0…r7` corrieron en VMs paralelas desde `dcd06d6` (logs `sampling_1/ledger/sesiones/vm_f5_r*.log`:
  todas `DONE`, ledgers traídos y VMs borradas por `vm.sh`). 65 corridas: 28 estudios nuevos y 37 celdas finales.
- `python -m comun.consolidar`: `C`, `H3-0.05`, `H3-0.1`, `H3-0.25` y `H3R-0.1` tienen 8 réplicas × 10 semillas (40
  celdas variante × réplica, 400 finales); todas las filas son `n2-highmem-8`, `codigo_sucio = False` y
  `valida = True` (ninguna `False`). `control/ledger/replicas.csv` y `h3/ledger/replicas.csv` generados.
- Tiempos reales contra D3 (media por estudio, réplicas 1…7): Optuna `C` 938 s (D3: 748 s; rango 644–1194 s entre
  réplicas), `U0.25` 213 s (153 s), `U0.1` 110 s (77 s), `U0.05` 61 s (67 s); finales ≈ 33 s `C`, ≈ 20 s `H3-0.05` y
  ≈ 24 s las demás `H3-*` (D3: ~35 s). Optuna salió ~25–45 % más lento que lo estimado, los finales más rápidos; no
  cambia el diseño. (Corregido en la revisión 3.3: decía 915 s, que es la media con la réplica 0 incluida, y
  «50 celdas».)
- Los logs `vm_f5_r3`, `r4` y `r5` muestran errores de `gsutil` al traer `C@5_…_600011` (corridas) y `C@5_…_999983`
  (predicciones) mientras r5 los subía; los archivos locales finales están completos (CSV legible, todos los parquet
  abren) y la fila está en el ledger.
- Gasto estimado (revisión 3.3): ≈ 5,7 h de corrida sumando las 8 VMs según el ledger, ≈ 7 h con arranque y
  sincronización; a ≈ US$ 0,19/h (spot + disco) son **≈ US$ 1,3**, dentro del peor caso de D3 (≈ US$ 6). La cifra
  exacta está en Billing.

### 2026-11-09 — informe con réplicas (`h3-semillas-optuna` 5.1)

- Sesión headless de aplicación del grupo 5, etapa `informe`.
- `informe/informe.md` aplica las reglas de D4 tal como están en `docs/hipotesis.md`: H3 con réplicas *confirmada*
  (`H3-0.1` y `H3-0.25` no pierden), A contra B *apoya (B)* (el IC de Δ de `H3-0.1` contiene a 0 y Ḡ_{C,0} = 276,10 M$
  queda debajo de la mediana de `C`, 276,49 M$), `H3-0.05` *confirmada* (no pierde, A = 11,82) y `H3R-0.1` *no cambia*
  (−0,54 [−1,88; 0,81] M$). Copia las filas de H3 de `sampling_1/informe/tabla_resultados.md` y responde «¿alcanzan
  50 semillas finales?» con la descomposición de varianza.
- `python -m scripts.verificar_informe_h3`: 10 filas copiadas idénticas a la tabla y 102 números del texto con fuente
  (tabla, `replicas.csv`, `apareado.csv`, medianas de `feature_fraction`, constantes del diseño); una fila alterada lo
  hace salir con 1. Límite conocido: un entero chico puede coincidir por casualidad con otra fuente.
- Pendiente: 5.2 (informe conjunto, guion y README) y la revisión en sesión limpia (5.3).

### 2026-11-09 — cierre revisión del informe (`h3-semillas-optuna` 5.3)

- Sesión limpia headless `8240957c-794f-41de-9371-672f20033d70`, etapa `revision`, lista de `docs/revision.md` § 5;
  detalle ítem por ítem en la bitácora de `sampling_1`. Ningún ✗ abierto.
- Los veredictos de D4 se mantienen. Corrección: «apoya (B)» se presenta como el nombre de la regla y se agrega que
  Ḡ_{C,0} (276,10 M$) queda arriba de la media de `C` con réplicas (275,92 M$): Δ se achica porque la réplica 0 de
  `H3-0.1` quedó arriba de su media (278,22 M$), no porque el control haya salido bajo. `verificar_informe_h3` pasa
  (107 números, 0 sin fuente).

### 2026-11-09 — extensiones del aporte de Luis (`incorporar-aportes` 1.2)

- Sesión headless `f0b04f89-178e-4a6c-80fb-07a78749b44f` · modelo: Opus · etapa `hipotesis`.
- `docs/hipotesis.md` § Extensiones del aporte de Luis: variantes `H3R-0.25`, `H3L-0.25`, `H3L-0.1` y `H3K-0.1`
  (estudio propio `K0.1`), declaradas como salidas de un análisis que miró 201910, con las reglas 5 a 8 de D4 (raíz
  contra lineal, raíz contra nada en r = 0,25, por cliente con Welch, veredicto con réplicas contra `C`) y la nota de
  comparaciones múltiples con los contrastes principales de `h4`. `docs/diseno.md`: variantes, reescalados, muestra
  por cliente (reconstrucción), grilla de la fase 6 (32 celdas, 8 estudios, ~3,3 h). Dependencias sin cambio.
- Pendiente: revisión en sesión limpia de hipótesis y diseño (1.3). Ninguna corrida real antes de ese cierre.

### 2026-11-09 — cierre revisión de hipótesis y diseño (`incorporar-aportes` 1.3)

- Sesión limpia `bf7f462e-3502-49bc-af4a-8fc438d913dc` · modelo: Opus · etapa `revision`. Lista de `docs/revision.md`
  § 1 y § 2 sin ✗ abiertos; detalle en `sampling_1/docs/bitacora.md`. Reglas 5 a 8 sin cambios. Corrección: la tanda
  de variantes suma ~5,9 h de VM (no ~5,8) en `docs/diseno.md` § Grilla de las extensiones.

### 2026-11-09 — cierre revisión de las corridas (`incorporar-aportes` 4.5)

- Sesión limpia `fb76540c-c00a-47cb-9fad-dcc9d4850cf7` · modelo: Opus · etapa `revision`. El `resultados.csv` de `HEAD`
  tenía 20 filas (lo pisó la copia vieja del bucket al volver una VM, `b736a7a`); reconsolidado desde `corridas/`:
  669 filas, idéntico a `69bd98f`, con `apareado.csv` (8 variantes) y `replicas.csv` (9 filas). `vm.sh` ya no sincroniza
  los CSV consolidados. Detalle en `sampling_1/docs/bitacora.md`.

### 2026-11-10 — análisis e informe de las extensiones (`incorporar-aportes` 6.1)

- Sesión headless del grupo 6 · modelo: Opus · etapa `informe`. Reglas 5 a 8 aplicadas tal como quedaron escritas: raíz
  contra lineal gana la raíz en r = 0,1 y no cambia en r = 0,25; raíz contra nada en r = 0,25 no cambia; por cliente no
  cambia; las cuatro variantes nuevas *no pierden* contra `C`. Sección "Extensiones del aporte de Luis" en
  `informe/informe.md`, más test ya mirado y comparaciones múltiples en Limitaciones.
- `replicas.csv` reconsolidado con las filas `H3R-0.25 - H3L-0.25`, `H3R-0.1 - H3L-0.1`, `H3R-0.25 - H3-0.25`
  (apareadas) y `H3K-0.1 - H3-0.1` (Welch); el cambio en `comun/` está en la bitácora de `h4`.
- Verificación: `python -m scripts.verificar_informe_h3`: 0 números sin fuente.

### 2026-11-10 — revisión del informe (`incorporar-aportes` 6.3)

- Revisión en sesión limpia de la etapa informe (lista `docs/revision.md` § 5), sin ✗ abiertos; detalle en
  `sampling_1/docs/bitacora.md`. Reglas 5 a 8 bien aplicadas. Corregido: la conclusión decía que el reescalado "no
  cambia nada"; ahora dice que √(1/r) no cambia contra no reescalar (la regla 5 da *gana la raíz* contra la lineal en
  r = 0,1). `verificar_informe_h3`: 0 sin fuente.

### 2026-11-13 — `docs/hipotesis.md`, `docs/diseno.md` e `informe/` fundidos en `README.md` (sitio-legible 3.5)

- Sesión: aplicar del grupo 3 de `sitio-legible`, headless, Opus. Etapa: informe.
- Destino de cada sección vieja:
  - `hipotesis.md` encabezado → callouts de § Predicción (tres momentos, con fecha y commit: `2f05cae` 1-nov y
    `7c34254` 3-nov; 8-nov `h3-semillas-optuna`; 9-nov `incorporar-aportes`).
  - `hipotesis.md` § H3 → § Idea (mecanismo y riesgo de `min_data_in_leaf`) y § Predicción › H3 (réplica 0), reglas sin
    cambios. «pre-registrada» → «fijada de antemano».
  - `hipotesis.md` § H3 con réplicas (qué queda fijo, qué es una réplica, reglas 1–4) → § Predicción › H3 con réplicas.
    En las reglas 1, 3 y 8 el umbral «−5,52 M$» se escribe «−δ», con δ = 5,52 M$ en «Qué queda fijo» y la nota de que en
    la ronda vigente se aplica el δ de la ronda (como ya hacía el informe).
  - `hipotesis.md` § Limitaciones previstas de las réplicas: «desvío mayor que el previsto → indeterminado» descartada
    (no pasó: las reglas decidieron); «tiempos de VMs distintas» → § Limitaciones › Ocho réplicas.
  - `hipotesis.md` § Extensiones del aporte de Luis → § Predicción › Extensiones del exploratorio
    `validacion_50_semillas` (D8: sin nombres; «lo que reporta Luis» → «lo que reporta el exploratorio»). Tabla de
    variantes nuevas → § Diseño › Variantes.
  - `hipotesis.md` § Limitaciones previstas → § Limitaciones (dependencia de `h1`, estudios compartidos, test ya mirado).
  - `diseno.md` § Variantes y › Extensiones → § Diseño › Variantes (una sola tabla de las ocho). § Estudios compartidos y
    § Réplicas de optimización → § Diseño › Estudios y réplicas.
  - `diseno.md` § Grilla con réplicas, › Grilla de las extensiones, § Grilla de la réplica 0 → § Diseño › Grilla, con los
    totales de horas (las tablas de horas por bloque se descartan: el detalle de ejecución está en
    `sampling_1/corridas.md`). «Por qué R = 8» → § Diseño › Grilla («exploratorio de Martín» → `sensibilidad_muestra`).
  - `diseno.md` › Ronda 201903–201908 y «por qué H3 no reoptimiza (211718)» → § Diseño › Rondas («el tutor pidió…,
    Tschopp» → «la consigna pide…»).
  - `diseno.md` § Fuera de la grilla → § Diseño › Grilla (réplicas de `U*`, `B*`, `GOSS`); «H4 y fast-retrain» descartado
    (lo dice H4); «reescalado como trabajo futuro» ya está en la regla 4.
  - `diseno.md` § Dependencias → § Dependencias.
  - `informe.md` encabezado, § Hipótesis y › Ronda 201903–201908 → descartados (dónde estaba cada cosa) o § Diseño ›
    Rondas. Los tres apartamientos están en `control/README.md` y en § Diseño › Rondas.
  - `informe.md` tablas copiadas de `tabla_resultados.md` (réplica 0, con réplicas, varianza, diferencias) → bloque
    `resultado` (tabla de variantes, mapa y curva) y, para réplicas, varianza y diferencias, los bloques de Resultados
    (una línea enlaza ahí). Veredictos de las reglas 1–8, AUC y ganancia, «¿alcanzan 50 semillas?» y § Conclusión →
    § Veredicto, con los mismos números.
  - `informe.md` § Limitaciones → § Limitaciones, salvo hiperparámetros de cuatro meses (la parte común va a Resultados;
    la propia, «no se probó el reescalado para el salto de cuatro a seis meses», queda) y un solo año/mes/máquina con el
    bootstrap de clientes → Limitaciones comunes de Resultados.
- Nuevo: diagrama del pipeline que marca que H3 achica solo la optimización.
