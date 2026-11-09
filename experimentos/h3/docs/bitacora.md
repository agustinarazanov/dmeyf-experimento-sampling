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
