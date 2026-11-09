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
