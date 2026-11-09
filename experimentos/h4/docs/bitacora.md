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
