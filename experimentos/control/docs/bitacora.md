# Bitácora — control

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
  `ledger/` (`C`, `C-rep`).

### 2026-11-08 — renombre de «brazo» a «variante» (`renombrar-brazos`)

- Qué cambió: la columna y la clave `brazo` de los ledgers pasaron a `variante`, `comun/brazos.py` a `comun/variantes.py`
  y el texto del repo dice «variante» donde decía «brazo». Los números no cambian: `apareado.csv` y las tablas de cada
  `reporte.html` coinciden con la foto previa (diferencia 0).
- Commits: ledgers y bucket `b9f6b43` (2.1) y `7b0545c` (2.5, bucket subido con `gsutil rsync`); código y tests `6ea0074`
  (2.2); paquete de Martín `f4566a3` (2.3); texto `4a456c8` (3.1); reportes regenerados `611bb2f` (3.2).
- Lo que sigue diciendo «brazo»: la historia de git (los commits anteriores) y el tag `corridas-v1`.
- Un clon anterior al renombre no consolida: `comun/ledger.py` rechaza una cabecera `brazo` nombrando el archivo. Hay que
  actualizar el clon y volver a bajar el ledger del bucket renombrado.

### 2026-11-08 — réplicas `C@1…7` (`h3-semillas-optuna` 1.2)

- Sesión headless de aplicación del grupo 1, etapa `diseno`.
- `docs/diseno.md` § Grilla suma las réplicas de optimización `C@1…7`: siete estudios más de `C` (semilla TPE = k) con
  sus 10 finales, de este experimento, para el Δ con réplicas de H3.
- Qué cambia de lo ya corrido: **nada**. El estudio `C`, sus finales y `C-rep` son la réplica 0, con los mismos `id`;
  N\* = 3.300 y δ = 5,52 M$ siguen saliendo de ella.
- Las corridas esperan la revisión en sesión limpia de la etapa (1.3) y el tag `corridas-v2`.

### 2026-11-09 — cierre revisión de las corridas (`incorporar-aportes` 4.5)

- Sesión limpia `fb76540c-c00a-47cb-9fad-dcc9d4850cf7` · modelo: Opus · etapa `revision`. El `resultados.csv` de `HEAD`
  tenía 21 filas (lo pisó la copia vieja del bucket, `b736a7a`); reconsolidado desde `corridas/`: 98 filas (8 réplicas
  de `C` y `C-rep`), idéntico a `69bd98f`. Detalle en `sampling_1/docs/bitacora.md`.

### 2026-11-12 — regla de D7 en la ronda 201903–201908 (`final-con-julio-agosto` 4.1)

- Sesión headless de aplicación del grupo 4, etapa `informe` · modelo: Opus. `python -m comun.reporte --todos` y
  `python scripts/comparar_rondas.py` → `sampling_1/informe/comparacion_rondas.md` (20 variantes de la ronda anterior,
  más `C` sin Δ; sin `H4O-0.5`). δ = 5,52 M$ (ronda anterior) y 5,65 M$ (ronda nueva).
- **Veredictos estables — se confirma.** 0 cambios de lado. Cambian 8 veredictos, todos desde o hacia *indeterminado*
  o entre *gana* y *no pierde*: `GOSS` *no pierde* → *indeterminado*; `H3-0.25` y `H4F-0.05` *no pierde* → *gana* (por
  semilla); `H3K-0.1` y `H3R-0.1` *gana* → *no pierde* (por semilla); `H4H-0.1` y `H4U-0.1` *indeterminado* →
  *pierde* (por semilla); `U0.5` *indeterminado* → *no pierde*. Con réplicas no cambia ninguno.
- **IC más angosto — se confirma.** Mediana de la razón de anchos del IC por semilla (anterior / nueva) = 1,44
  (20 variantes; mín. 0,87, máx. 2,12), dentro de [1,2; 1,9].
- **Con réplicas el ancho baja menos — se confirma.** Mediana de la razón de anchos del IC de Welch con réplicas = 0,96
  (12 variantes; mín. 0,81, máx. 1,23): menor que 1,44 y menor que 1,3. Con 8 réplicas el IC prácticamente no se angosta.
- `H4O-0.5` (regla en `h4/docs/hipotesis.md`): contra `C`, Δ con réplicas −1,33 [−4,27; 1,60] M$, cota ≥ −δ → *no
  pierde*, **se confirma**; contra `H4F-0.05`, D_OF = −2,74 [−5,69; 0,21] M$ → *no cambia*, **se confirma**.
  A(`H4O-0.5`) = 2,31 contra A(`H4F-0.05`) = 12,50 (T mediana 434 s contra 80 s).
