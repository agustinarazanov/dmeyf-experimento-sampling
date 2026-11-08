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

## Fuera de la grilla

- **Respuesta del tutor sobre H2**: si pide mantener `bagging_fraction` optimizado, salen `B0.5`, `B0.25` y `B0.1`, y
  la fase 3 queda solo con `GOSS`. H1 y H3 no cambian.

## Dependencias

- `control`: finales de `C`, N\* y δ.
