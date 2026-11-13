# Bitácora — h2

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
  `ledger/` (`B0.5`, `B0.25`, `B0.1`, `GOSS`).

### 2026-11-08 — renombre de «brazo» a «variante» (`renombrar-brazos`)

- Qué cambió: la columna y la clave `brazo` de los ledgers pasaron a `variante`, `comun/brazos.py` a `comun/variantes.py`
  y el texto del repo dice «variante» donde decía «brazo». Los números no cambian: `apareado.csv` y las tablas de cada
  `reporte.html` coinciden con la foto previa (diferencia 0).
- Commits: ledgers y bucket `b9f6b43` (2.1) y `7b0545c` (2.5, bucket subido con `gsutil rsync`); código y tests `6ea0074`
  (2.2); paquete de Martín `f4566a3` (2.3); texto `4a456c8` (3.1); reportes regenerados `611bb2f` (3.2).
- Lo que sigue diciendo «brazo»: la historia de git (los commits anteriores) y el tag `corridas-v1`.
- Un clon anterior al renombre no consolida: `comun/ledger.py` rechaza una cabecera `brazo` nombrando el archivo. Hay que
  actualizar el clon y volver a bajar el ledger del bucket renombrado.

### 2026-11-13 — `docs/hipotesis.md`, `docs/diseno.md` e `informe/` fundidos en `README.md` (sitio-legible 3.4)

- Sesión: aplicar del grupo 3 de `sitio-legible`, headless, Opus. Etapa: informe.
- Destino de cada sección vieja:
  - `hipotesis.md` encabezado → callout de § Predicción con fecha y commit (`2f05cae` 1-nov; `7c34254` 3-nov).
  - `hipotesis.md` § H2 → línea de apertura, § Idea (mecanismo de `bagging_fraction`, adaptación del espacio, GOSS) y
    § Predicción (todas las viñetas, sin cambios en las reglas; «curva tiempo-ganancia» → «mapa del tradeoff», que es la
    figura nueva).
  - `hipotesis.md` § Limitaciones previstas (GOSS y `learning_rate`) → § Limitaciones, primer callout.
  - `diseno.md` encabezado → una línea en § Diseño que remite al control. § Variantes → § Diseño › Variantes (tabla con
    menos columnas; r = 1 en el párrafo). § Grilla y › Ronda 201903–201908 → § Diseño › Grilla y › Rondas.
  - `diseno.md` § Fuera de la grilla («respuesta del tutor sobre H2») → § Diseño › Grilla, «si la devolución del curso
    pide…» (D8).
  - `diseno.md` § Dependencias → igual.
  - `informe.md` encabezado y § Hipótesis → descartado / línea de apertura. Párrafo de la ronda → § Diseño › Rondas y
    el bloque generado. § Resultados (tabla) → bloque `resultado`; viñetas → § Veredicto. § Conclusión → último párrafo
    del veredicto.
  - `informe.md` § Limitaciones: GOSS descriptivo, adaptación de `B*` y una semilla de Optuna → § Limitaciones;
    hiperparámetros de cuatro meses y un solo año/mes/máquina → Limitaciones comunes de Resultados.
  - `informe/reporte.html` y `bandas_H2.png` → bloque `resultado` y `figuras/` (curva de diferencia).
- Nuevo: diagrama del pipeline que marca dónde muestrea (dentro de cada árbol, con train y `Dataset` completos).
