# Bitácora — h4

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

### 2026-11-09 — apertura (`incorporar-aportes` 1.1)

- Quién: Agustina, sesión headless `f0b04f89-178e-4a6c-80fb-07a78749b44f` · modelo: Opus · etapa `hipotesis`.
- `h4/` creado desde `plantilla/`. `docs/hipotesis.md`: H4 (muestras informadas por clase) con las reglas de D4 del
  cambio (búsqueda informada, difícil contra uniforme, fast-retrain), la declaración de que las variantes salen de
  estrategias que Luis eligió mirando 201910, los contrastes principales (`H3-0.1`, `H4H-0.1`, `H4F-0.05`) y la nota de
  comparaciones múltiples. `docs/diseno.md`: variantes y estudios de D3, sonda y muestras, grilla (32 celdas, 16
  estudios), `## Dependencias` con `control`, `h1` y `h3`.
- Las variantes no están todavía en `comun/variantes.py` (grupo 2), así que `--verificar` no mira `h4`.
- Pendiente: revisión en sesión limpia de hipótesis y diseño (1.3). Ninguna corrida real antes de ese cierre.

### 2026-11-09 — cierre revisión de hipótesis y diseño (`incorporar-aportes` 1.3)

- Sesión limpia `bf7f462e-3502-49bc-af4a-8fc438d913dc` · modelo: Opus · etapa `revision`. Lista de `docs/revision.md`
  § 1 y § 2 sin ✗ abiertos; detalle en `sampling_1/docs/bitacora.md`. Correcciones en `docs/hipotesis.md`: no hay un
  veredicto único de H4 (se informan las reglas 1 y 3 por variante) y H4 declara que toca la proporción de clases
  (terreno de Sampling_2) como excepción; en `docs/diseno.md`, ~5,9 h para la tanda de variantes. Ninguna regla ni
  umbral cambia.

### 2026-11-09 — 4.3 consolidación de las corridas (`incorporar-aportes`)

- `python -m comun.consolidar` y `--sanity` sin ✗. Las 8 variantes nuevas (`H3R-0.25`, `H3L-0.25`, `H3L-0.1`, `H3K-0.1`,
  `H4F-0.05`, `H4F-0.25`, `H4H-0.1`, `H4U-0.1`) tienen 8 réplicas × 10 semillas = 80 finales cada una (640 en total);
  todo en `n2-highmem-8` y con `codigo_sucio = False` (h3: 669 corridas válidas, h4: 336, sin reemplazadas en h4).
- Tiempos reales contra D6 (preparación + optimización + entrenamiento, suma de las filas del ledger): ~5,25 h de cómputo
  en total contra ~5,9 h de D6; por réplica (una VM) entre 33 y 44 min contra ~45 min. Optimización: `NH0.1` 83–132 s
  (media ~104 s), `K0.1` 76–227 s, `NU0.1` 84–395 s (la más variable). D6 se cumplió, un poco por debajo.

### 2026-11-09 — cierre revisión de las corridas (`incorporar-aportes` 4.5)

- Sesión limpia `fb76540c-c00a-47cb-9fad-dcc9d4850cf7` · modelo: Opus · etapa `revision`. § 4 de `docs/revision.md`
  sin ✗ abiertos; detalle en `sampling_1/docs/bitacora.md`. El ledger de `h4` estaba bien.
- Gasto de la fase 6 (no estaba anotado, **estimado**): el ledger registra ~5,25 h de cómputo en las 8 VMs de
  variantes y ~2,9 h en las 10 de Luis; con Martín (~2,1 h según D6, más el reintento de 08), D7 dos veces, `luis_1` y
  `luis_1_panel` y ~10 min de arranque por VM (≈ 24 VMs), son ≈ 13–18 h de `n2-highmem-8` spot; a ≈ US$ 0,19/h,
  **≈ US$ 2,5–3,5**. La cifra real sale de la facturación del proyecto (la mira Agustina).

### 2026-11-10 — análisis e informe (`incorporar-aportes` 6.1)

- Sesión headless del grupo 6 · modelo: Opus · etapa `informe`. Reglas de `docs/hipotesis.md` aplicadas tal como
  quedaron escritas: regla 1 refutada (`H4H-0.1` y `H4U-0.1` *pierden* con réplicas); regla 2 *no cambia*; regla 3
  confirmada en `H4F-0.05` (no pierde, A mayor que la de `H3-0.05`, gana a tiempo igual) e indeterminada en `H4F-0.25`
  (la cota inferior a tiempo igual queda debajo de 0). Informe en `informe/informe.md`.
- `comun/`: `replicas.csv` suma las diferencias de D4 que faltaban (`PARES_WELCH` en `comun/variantes.py`: `H4H-0.1` −
  `H4U-0.1` y `H3K-0.1` − `H3-0.1` con IC de Welch; pares apareados de las reglas 5 y 6 de `h3`); el reporte las muestra
  en "Diferencias entre variantes" con el tipo de IC. Reconsolidado y `python -m comun.reporte --todos`.
- Verificación: `python -m scripts.verificar_informe_h3 --informe experimentos/h4/informe/informe.md` (el verificador de
  `h3` ahora acepta `--informe` y mira también los ledgers de `h4`): 0 números sin fuente.

### 2026-11-10 — revisión del informe (`incorporar-aportes` 6.3)

- Revisión en sesión limpia de la etapa informe (lista `docs/revision.md` § 5), sin ✗ abiertos ni correcciones en
  `informe/informe.md`; detalle en `sampling_1/docs/bitacora.md`. Reglas 1 a 3 aplicadas tal como quedaron escritas;
  D_HU recalculado aparte (−3,07 M$ [−7,61; 1,47]). `verificar_informe_h3 --informe`: 0 sin fuente.
