# Hipótesis — Sampling_1

Escrito antes de cualquier corrida real. Si algo de este documento cambia después de abrir la etapa de corridas, el
cambio se anota en `docs/bitacora.md` con su motivo y las corridas previas quedan marcadas como de la versión anterior.

Desde el 2-nov cada hipótesis tiene su carpeta. Acá quedan la pregunta, H4 (pendiente), la respuesta al tutor y las
limitaciones comunes. El resto está en:

- [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md): el control (C) y las métricas y reglas comunes (G,
  Δ, δ, T, A, N\* y veredictos).
- [`h1/docs/hipotesis.md`](../../h1/docs/hipotesis.md): H1, submuestreo uniforme del train.
- [`h2/docs/hipotesis.md`](../../h2/docs/hipotesis.md): H2, muestrear dentro de LightGBM.
- [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md): H3, optimizar sobre una muestra y entrenar con todo.

## Pregunta

Pregunta del tutor (Zulip 208986, 1-nov): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?**

Para el baseline de Bolaños (28-oct, Zulip 208135), ¿cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 si se
usan menos filas para entrenar u optimizar? En H1, H2 y H3 la proporción de BAJA+1 ∪ BAJA+2 queda igual, en
esperanza, en todos los brazos; H4 la cambia a propósito y la lleva un integrante por separado.

## H4 — Submuestreo informado de CONTINUA y pesos por fila (a cargo de un integrante, fuera de la grilla nuestra)

Pendiente: no tiene carpeta hasta que la tome el integrante que la propuso.

Propuesta de un integrante del grupo a partir de lo que le funcionó en la primera competencia. No la implementa este
repo en las fases 1 a 3; la corre él con el mismo control, el mismo corredor y el mismo ledger, como método adicional
(`informado` y `pesado`) o en su propia carpeta `experimentos/sampling-informado/`.

- **Variables**: (a) quedarse con el 100% de las bajas y el 20% de los CONTINUA, elegidos por un algoritmo (no al azar);
  (b) quedarse con el 10% de los CONTINUA al azar y darle a cada fila un peso que compense la proporción.
- **Métrica que decide**: el veredicto de cada variante contra el control, con las reglas comunes.
- **Predicción**: *no pierde* en ninguna de las dos y A ≥ 4, porque el 80–90% de las filas que se descartan son
  CONTINUA que el modelo ya separa bien.
- **Se confirma** si (a) *no pierde*. **Se refuta** si (a) *pierde*. **Ninguna de las dos** si sale *indeterminado*.
- **Qué la distingue de H1**: cambia la proporción de clases y la probabilidad queda descalibrada; el ranking no. Hay
  que corregir la probabilidad con la tasa (o el peso) antes de usarla en un corte por umbral.
- **Pendiente de definir por quien la lleva**: cuál es el algoritmo de selección de (a), y si los pesos de (b) van en
  `weight` de LightGBM o en `scale_pos_weight`.

## Respuesta a la pregunta del tutor

La pregunta no es velocidad contra ganancia sino qué se hace con el tiempo ahorrado. Si no se reinvierte, no vale la pena
perder ni un 1%. Por eso, además de la comparación a datos iguales, hay una **comparación a tiempo igual**: el control
completo contra la variante rápida con el tiempo sobrante gastado en más semillas (ensamble de K modelos de la variante,
con K tal que el tiempo total iguale al del control). Sale del mismo ledger, sin corridas nuevas, porque las 10 semillas
de cada brazo ya están. Predicción: a tiempo igual la variante rápida gana, y H3 es la que más rinde.
*Nota del 2-nov (después de las fases 1 a 3, antes de ver ningún ensamble):* el ledger guardaba curvas y no predicciones,
así que el ensamble no salía "sin corridas nuevas". Se agrega una fase 4 que repite solo los finales guardando
predicciones (`diseno.md` § Fases, D12). La predicción no cambia.

Un brazo **vale la pena** si *no pierde* contra el control y además A ≥ 2, con la definición común de T. La respuesta
del video es la lista de brazos que valen la pena, con su A y su Δ, más la curva tiempo-ganancia de todos los brazos.
Predicción: valen la pena H3 con ambas tasas y H1 con r = 0,25. Para un pipeline acotado en tiempo, como el de 15
minutos de la segunda entrega, lo que más sirve es H3 con r_opt = 0,1, porque la optimización domina el tiempo total.

## Limitaciones previstas

Las comunes a todas las hipótesis. Las propias de una hipótesis están en su `hipotesis.md` (GOSS en `h2`, el estudio
compartido entre H1 y H3 en `h3`).

- Con 10 semillas no se separan diferencias menores que δ; esos casos salen como *indeterminado* y se informan.
- Aparear por semilla ayuda poco entre brazos con datos e hiperparámetros distintos, porque la misma semilla no produce
  modelos correlacionados. El IC apareado es honesto, pero no es mucho más angosto que uno no apareado.
- Optuna corre con una sola semilla por brazo, así que Δ incluye la suerte de la optimización, que el IC no mide.
- El corte N* sale de 201908, así que si la tasa de bajas de 201910 es distinta, todos los brazos pagan igual.
- Hay un solo mes de test (201910) y un solo año (2019), así que la conclusión vale para este baseline.
- Los tiempos se miden en `n2-highmem-8`. Si el pipeline de la segunda entrega corre en otra máquina, por ejemplo con
  la predicción en la laptop, las aceleraciones relativas se pueden trasladar, pero los segundos absolutos no.
