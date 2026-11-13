# Bitácora — h1

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
  `ledger/` (`U0.5`, `U0.25`, `U0.1`, `U0.05`). Los estudios `U0.25` y `U0.1` los lee también `h3`.

### 2026-11-08 — renombre de «brazo» a «variante» (`renombrar-brazos`)

- Qué cambió: la columna y la clave `brazo` de los ledgers pasaron a `variante`, `comun/brazos.py` a `comun/variantes.py`
  y el texto del repo dice «variante» donde decía «brazo». Los números no cambian: `apareado.csv` y las tablas de cada
  `reporte.html` coinciden con la foto previa (diferencia 0).
- Commits: ledgers y bucket `b9f6b43` (2.1) y `7b0545c` (2.5, bucket subido con `gsutil rsync`); código y tests `6ea0074`
  (2.2); paquete de Martín `f4566a3` (2.3); texto `4a456c8` (3.1); reportes regenerados `611bb2f` (3.2).
- Lo que sigue diciendo «brazo»: la historia de git (los commits anteriores) y el tag `corridas-v1`.
- Un clon anterior al renombre no consolida: `comun/ledger.py` rechaza una cabecera `brazo` nombrando el archivo. Hay que
  actualizar el clon y volver a bajar el ledger del bucket renombrado.

### 2026-11-13 — `docs/hipotesis.md`, `docs/diseno.md` e `informe/` fundidos en `README.md` (sitio-legible 3.3)

- Sesión: aplicar del grupo 3 de `sitio-legible`, headless, Opus. Etapa: informe.
- Destino de cada sección vieja:
  - `hipotesis.md` encabezado (enlaces a sampling_1 y control, escrito antes de correr) → callout de § Predicción, con
    fecha y commit (`2f05cae` 1-nov, en `sampling_1/docs/hipotesis.md`; `7c34254` 3-nov, `h1/docs/hipotesis.md`).
  - `hipotesis.md` § H1 → título y línea de apertura (qué se prueba), § Idea (el mecanismo de la variable: Optuna de
    nuevo por tasa, final con muestra resorteada) y § Predicción (variable, métrica, predicción, reglas), sin cambios de
    texto en las reglas.
  - `diseno.md` encabezado → una línea en § Diseño que remite al control; el resto (dónde estaba cada cosa) descartado.
  - `diseno.md` § Variantes → § Diseño › Variantes. § Estudios de Optuna compartidos → § Diseño › Variantes (párrafo).
    § Grilla y › Ronda 201903–201908 → § Diseño › Grilla (ronda vigente) y › Rondas (anterior). § Dependencias → igual.
  - `informe.md` encabezado → descartado (decía dónde estaban otras páginas). § Hipótesis → línea de apertura. Párrafo
    de la ronda → § Diseño › Rondas y el bloque generado (`linea_ronda`).
  - `informe.md` § Resultados (tabla copiada) → bloque `resultado` generado (tabla, mapa del tradeoff y curva de
    diferencia, que reemplaza a `bandas_H1.png`). Viñetas de veredicto y AUC → § Veredicto.
  - `informe.md` § Limitaciones: una semilla de Optuna y estudios compartidos con H3 → § Limitaciones; hiperparámetros
    de cuatro meses en un final de seis y un solo año/mes/máquina → Limitaciones comunes de Resultados (son de todas).
  - `informe.md` § Conclusión → última frase del callout de § Veredicto; la remisión al informe conjunto se descarta.
  - `informe/reporte.html` → bloque `resultado` y `figuras/`.
- Nuevo: diagrama del pipeline que marca las dos muestras (Optuna y final).
