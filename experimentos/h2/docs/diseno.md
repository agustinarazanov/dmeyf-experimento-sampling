# Diseño — h2

Traduce `docs/hipotesis.md` a corridas concretas. Máquina, parámetros fijos de LightGBM, semillas finales y métricas
que se calculan son los de [`control/docs/diseno.md`](../../control/docs/diseno.md); el reparto en fases y la
estimación, los de [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md). Si este documento cambia después de
abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas quedan marcadas como de la versión
anterior.

## Variantes

| variante | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `B0.5`, `B0.25`, `B0.1` | H2 | r = 1 | 4 hp (sin `bagging_fraction`) | r = 1 | `bagging_fraction = f`, `bagging_freq = 1` |
| `GOSS` | H2, descriptivo | r = 1 | 4 hp (sin `bagging_fraction`) | r = 1 | `data_sample_strategy = goss`, `top_rate = 0,2`, `other_rate = 0,1` |

"4 hp" son los rangos del espacio del control (`control/docs/hipotesis.md` § Control) sin `bagging_fraction`. En
`GOSS` sale porque LightGBM no admite bagging con GOSS; es la misma adaptación que H2 y se declara igual.

## Grilla

- **Optimización**: 4 estudios (`B0.5`, `B0.25`, `B0.1`, `GOSS`) × 40 trials.
- **Finales**: 4 variantes × 10 semillas = 40 corridas.

### Ronda 201903–201908 (cambio `final-con-julio-agosto`, 12-nov-2026)

Sin estudios nuevos: `B0.5`, `B0.25`, `B0.1` y `GOSS` se reusan. Los finales se repiten con train 201903–201908 y las 20
semillas de [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908: 4 variantes × 20 =
80 corridas, en la lista `fase7_r0` de la fase 7 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
§ Reparto y fases). La ronda anterior se conserva. Los apartamientos (208135, 211210) están justificados en el diseño
del control.

### Réplicas y `B0.05` (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Predicción y regla: [`docs/hipotesis.md`](hipotesis.md) § Réplicas de H2 y `B0.05`. H2 forma la fila "dentro de
LightGBM" de la grilla común ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Grilla común), al lado de
las otras y sin pares directos.

| variante | método | tasa | estudio (k = 0 / k ≥ 1) | final: params fijos |
|---|---|---|---|---|
| `B0.05` | `bagging` | 0,05 | `B0.05` / `B0.05@k` | `bagging_fraction = 0,05`, `bagging_freq = 1` |

- **Réplicas**: `B0.5`, `B0.25`, `B0.1`, `B0.05` y `GOSS` con 8 réplicas (k = 0…7). Réplica k: TPE con semilla k; no
  hay muestra previa que sortear.
- **Estudios nuevos**: `B0.05` en k = 0 y `B{f}@k` y `GOSS@k` en k = 1…7: 1 + 5 × 7 = **36 estudios**, todos sobre el
  train completo con el espacio de 4 hp.
- **Finales nuevos**, con las 20 semillas de la ronda 201903–201908: `B0.05` en k = 0 y las cinco variantes en
  k = 1…7: 20 + 5 × 7 × 20 = **720 finales**.
- **T y A**: T como mediana entre réplicas y A con una sola referencia
  ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición de tiempos).
- Van en las listas `fase8_r0_b` … `fase8_r7_b` de la fase 8 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
  § Reparto y fases). Ninguna lista `_a` lee nada de una `_b`.
- § Fuera de la grilla: las réplicas de `B*` y `GOSS`, que `h3` dejaba fuera, entran ahora.

## Fuera de la grilla

- **Respuesta del tutor sobre H2**: si pide mantener `bagging_fraction` optimizado, salen `B0.5`, `B0.25` y `B0.1`, y
  la fase 3 queda solo con `GOSS`. H1 y H3 no cambian.

## Dependencias

- `control`: finales de `C`, N\* y δ.
