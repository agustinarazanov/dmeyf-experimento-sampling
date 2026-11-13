# Control y reglas

El control `C` es el baseline sin cambios, y acá están las reglas con las que se juzga a todas las hipótesis: G, N\*,
Δ, δ, el veredicto, T y A. Las hipótesis enlazan esta página en lugar de repetirlas.

## Baseline

El baseline del curso (Zulip 208135), con train completo (r = 1):

- **Datos**: 2019; train 201903–201906 completo; positivo BAJA+1 ∪ BAJA+2; lags y deltas de orden 2 (201901 y 201902
  solo como historia); validación 201908; test 201910, que no se usa para elegir nada. 201911 y 201912 no se usan.
- **Modelo**: LightGBM con defaults, salvo lo que optimiza Optuna, con `num_iterations = 100` sin early stopping y
  `num_threads = 8`.
- **Optuna**: 40 trials, TPE con semilla de optimización 0, maximiza el AUC en validación (201908). El espacio de
  búsqueda lo fija cada grupo (208135). El nuestro:

  | hiperparámetro | rango | escala |
  |---|---|---|
  | `num_leaves` | 8 – 1024 (entero) | log |
  | `learning_rate` | 0,01 – 0,3 | log |
  | `min_data_in_leaf` | 10 – 5000 (entero) | log |
  | `feature_fraction` | 0,1 – 1,0 | lineal |
  | `bagging_fraction` | 0,1 – 1,0, con `bagging_freq = 1` | lineal |

  Los 40 trials y la semilla única de Optuna son una elección nuestra, porque 208135 no los fija.
- **Final**: el modelo final entrena con 201903–201908 (ronda vigente, ver § Rondas) con los hiperparámetros que eligió
  Optuna, y se evalúa en test (201910).
- **Semillas finales**: 20 semillas fijas, las mismas en todas las variantes (§ Diseño). Cada una fija el `seed` de
  LightGBM, de donde salen el bagging y el `feature_fraction`. En las variantes con muestreo previo, la semilla final
  también vuelve a sortear la muestra, así que el IC incluye la variabilidad de la muestra.

### Meses

```mermaid
flowchart TB
  H["201901–201902<br/>solo historia<br/>(lags y deltas)"] --> T["201903–201906<br/>train de Optuna"]
  T --> J["201907<br/>solo en el final"]
  J --> V["201908<br/>validación: AUC de Optuna y N*<br/>(también en el final)"]
  V --> S["201909<br/>no se usa"]
  S --> X["201910<br/>test: G y veredicto"]
  style X fill:#fdebd0,stroke:#b8860b
  style S fill:#eeeeee,stroke:#999999
```

Optuna entrena con 201903–201906 y elige por AUC en 201908. El final entrena con 201903–201908 y predice 201910. 201909
solo aporta la clase de 201907.

### Parámetros fijos de LightGBM

En todas las variantes, además de los defaults:

- `objective = binary`, `num_iterations = 100`, `num_threads = 8`, `verbosity = -1`, `seed` = la semilla final en las
  corridas finales y 0 en los trials de Optuna.
- `deterministic = true` y `force_col_wise = true`. No cambian el modelo salvo por redondeo: hacen que la misma
  configuración repita el resultado y que LightGBM no cambie de estrategia de histogramas según r, lo que ensuciaría
  los tiempos. Por `force_col_wise`, T(C) no es exactamente el tiempo del baseline con la elección automática de
  LightGBM.
- `feature_pre_filter = false` en el `Dataset`, porque Optuna cambia `min_data_in_leaf` entre trials. El `Dataset` se
  construye una vez por estudio y una vez por corrida final, y ese tiempo entra en T.

Los tres son una adaptación declarada en la etapa de diseño (1-nov).

## Reglas

Escritas antes de cualquier corrida real: fijadas el 2026-11-01 en `sampling_1/docs/hipotesis.md` (commit `2f05cae`) y
pasadas a `control/docs/hipotesis.md` el 2026-11-03 (commit `dc6d9ce`). La ronda 201903–201908 se fijó el 2026-11-12
(commit `159ee0d`), antes del tag `corridas-v4` y de cualquier final de esa ronda. Un cambio posterior se anota en la
[bitácora del control](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/control/docs/bitacora.md)
con su motivo, y las corridas previas quedan marcadas como de la versión anterior.

- **N\***: la cantidad de clientes contactados que maximiza la ganancia media del control en validación (201908). Ese mismo N\* se
  aplica en test (201910) a todas las variantes. En la ronda vigente es N\* = 3.300, fijo (§ Rondas).
- **G** (métrica que decide): ganancia en 201910 al corte fijo N\*, calculada contra BAJA+2 con los valores de la
  cátedra. La ganancia máxima de la curva se reporta pero no decide.
- **Δ**: G(variante) − G(control), apareada por la semilla final. Se reportan la media, el desvío, el IC 95% (t de
  Student con n − 1 g.l.: 19 con 20 semillas) y en cuántas semillas gana la variante.
- **δ**: δ = 0,02 · Ḡ_C, donde Ḡ_C es la ganancia media del control en 201910 al corte N\*. Lo que se fija antes de correr
  es la regla; el valor de δ sale del control y cambia con la ronda.
- **Veredicto**: cuatro casos que cubren todo.
  - *gana*: la cota inferior del IC de Δ es mayor que 0;
  - *no pierde*: la cota inferior del IC de Δ es mayor o igual que −δ (incluye *gana*);
  - *pierde*: la media de Δ es menor que −δ;
  - *indeterminado*: el resto, cuando la cota inferior es menor que −δ y la media es mayor o igual que −δ. Faltan
    semillas para decidir y se informa así.
- **T** (tiempo): tiempo de pared del pipeline de la variante, medido solo en `n2-highmem-8` con CPU Ice Lake. Es la
  optimización (suma de la duración de los 40 trials, incluida la predicción en 201908, más un armado del
  `lgb.Dataset`) más la media del modelo final entre semillas (`Dataset`, entrenamiento y predicción en 201910). Sumar
  trials, y no medir el proceso entero, hace que T no dependa de si la VM se cayó y el estudio se retomó. No incluye
  leer los datos ni generar los lags, que son iguales en todas las variantes. El tiempo de `lgb.train` del modelo final
  se reporta aparte.
- **A** (aceleración): A = T(control) / T(variante), con la misma definición de T en todas las variantes.
- **Vale la pena** una variante que no pierde y tiene A ≥ 2.

```mermaid
flowchart TD
  A["Δ por semilla: media e IC 95%"] --> B{"cota inferior del IC > 0"}
  B -- sí --> G["gana<br/>(cuenta como no pierde)"]
  B -- no --> C{"cota inferior ≥ −δ"}
  C -- sí --> N["no pierde"]
  C -- no --> D{"media < −δ"}
  D -- sí --> P["pierde"]
  D -- no --> I["indeterminado<br/>(faltan semillas)"]
  style G fill:#d5f0e0,stroke:#2e8b57
  style N fill:#d5f0e0,stroke:#2e8b57
  style P fill:#f6d5d1,stroke:#c0392b
  style I fill:#f7ebc8,stroke:#b8860b
```

## Diseño

### Variantes

| variante | Optuna: datos | Optuna: espacio | final: datos |
|---|---|---|---|
| `C` | r = 1 | 5 hp (§ Baseline) | r = 1 |

`C-rep` es una réplica del control para la compuerta de resultados, no una variante que entre en Δ.

### Grilla

- **Optimización**: el estudio `C`, 40 trials, 100 iteraciones cada uno, sin early stopping. Además, siete réplicas de
  optimización `C@1…7` (cambio `h3-semillas-optuna`, 8-nov): un estudio más por réplica k, con la semilla del sampler
  TPE = k. Los estudios `C@k` son de `control`, sus hiperparámetros van a `ledger/hp/C@k.json` y sus filas llevan
  `replica_opt = k` y el `id` con `@k`. El estudio `C`, sus finales y `C-rep` son la réplica 0, y N\* y δ salen de ella.
  Para qué sirven las réplicas: [H3](../h3/README.md).
- **Finales**: `C` y `C@1…7` × 20 semillas = 160 corridas, y `C-rep` × 20 = 20 corridas, en otra VM. `C-rep` usa el JSON
  de `C` y las mismas semillas, con su propio nombre de variante para que el id de la corrida no choque con el de `C`.
  Sirve para comprobar que el control se repite y para medir cuánto varía el tiempo entre VMs del mismo tipo.
- **Semillas finales**, en este orden: las 10 oficiales (100003, 200003, 300007, 400009, 500009, 600011, 700001, 800011,
  900001, 999983) y 10 más de la fórmula 110017 + i · 19937 con i = 0…9 (110017, 129954, 149891, 169828, 189765, 209702,
  229639, 249576, 269513, 289450). Ninguna choca con las oficiales ni con la semilla 0, que queda reservada para Optuna
  y para las muestras de optimización. Las primeras 10 son las de la ronda anterior, así que la ronda vigente se puede
  reconsolidar con 10 y separar el efecto de la ventana del de las semillas.
- **Consolidado**, en este orden: N\* (fijo en la ronda vigente), G por corrida final, Ḡ_C y δ, Δ por variante apareada
  por semilla contra `C` y solo sobre las semillas que tienen los dos, veredicto y T con su A. Todo sale del
  `ledger/apareado.csv` de cada experimento; nada se calcula a mano. N\* y δ salen siempre del ledger de `control`.
- **Por corrida final**, el ledger guarda AUC 201908 (vacío en la ronda vigente), AUC 201910, las curvas de ganancia
  acumulada (`ledger/curvas/`), la ganancia máxima en 201910, las filas de train, el hash de la muestra, los tiempos por
  fase, la memoria máxima y el modelo de CPU. Por estudio: AUC del mejor trial, hiperparámetros
  (`ledger/hp/<estudio>.json`, versionado) y tiempo total.
- Las corridas en la Mac (`--filas 20000`) son pruebas con `etapa = exploracion` y no entran en `resultados.csv`. La
  ejecución en VMs está en [Corridas](../sampling_1/corridas.md).

### Rondas

- **Ronda 201903–201906** (anterior): final con train 201903–201906, 10 semillas, N\* calculado en validación (201908)
  con esos finales. Se conserva y se sigue pudiendo consolidar.
- **Ronda 201903–201908** (vigente, cambio `final-con-julio-agosto`, 12-nov): cambia solo lo siguiente; Optuna, el
  espacio, G, Δ, la regla de δ, los veredictos, T y A quedan iguales.
  - **Ventana del final 201903–201908.** La consigna pide reentrenar incluyendo 201907 y 201908 para predecir 201910
    (Zulip 211210). Optuna no cambia: sigue entrenando con 201903–201906 y eligiendo por AUC en 201908, y los estudios
    ya guardados (réplicas `@k` incluidas) se reusan.
  - **N\* = 3.300, fijo.** Es el valor de la ronda anterior, calculado en validación con finales que no habían visto
    201908. En la ronda vigente la predicción de 201908 sería dentro de la muestra, así que los finales no la hacen y
    N\* no se recalcula. Recalcularlo en test violaría «201910 solo para comparar».
  - **δ** sigue la regla de siempre con los `C` de la ronda vigente, así que su valor cambia. La tabla de rondas de
    [Resultados](../sampling_1/README.md) muestra los dos δ.
  - **20 semillas** y t de Student con 19 g.l.
  - Cada fila final lleva `meses_final = 201903-201908` y el id la ventana. El consolidado no mezcla rondas.

### Apartamientos del baseline

Cada uno con su id y su motivo. Los tres están justificados. Va a Limitaciones solo el tercero.

- **El veredicto sale de la ganancia G y no del AUC**, aunque el baseline dice «métrica auc» (Zulip 208135). La regla
  de veredicto se escribió en pesos antes de la primera corrida y δ está definido en pesos. Un umbral de AUC sería una
  regla nueva escrita después de haber visto los AUC de la ronda anterior. Optuna sí elige por AUC en validación, como
  pide 208135, y el AUC en 201910 se reporta al lado (ΔAUC con su IC por semilla y con réplicas).
- **Ventana del final 201903–201908** (seis meses; Zulip 211210). La respuesta dice que se reentrena incluyendo 201907 y
  201908, no que se saquen 201903 y 201904. Los seis meses quedaron confirmados el 13-nov-2026.
- **Los hiperparámetros elegidos con cuatro meses se usan sin cambios en un final de seis**, incluido
  `min_data_in_leaf`, que es absoluto (Zulip 211210). Es lo que pide la consigna (reentrenar con los hiperparámetros ya
  elegidos), no una variante. Reescalar sería una variante nueva, y la idea ya está en `H3R` y `H3L`
  ([H3](../h3/README.md)).

## Predicción

### Predicción del experimento (1-nov)

!!! info "Predicción"
    Fijada el 2026-11-01 en `sampling_1/docs/hipotesis.md` (commit `2f05cae`), antes de cualquier corrida real. Las
    predicciones de cada hipótesis están en su página.

- **Qué vale la pena**: H3 con ambas tasas y H1 con r = 0,25. Para un pipeline acotado en tiempo, como el de la segunda
  entrega, lo que más sirve es H3 con r_opt = 0,1, porque la optimización domina el tiempo total.
- **A tiempo igual**: la pregunta no es velocidad contra ganancia sino qué se hace con el tiempo ahorrado. Si no se
  reinvierte, no vale la pena perder ni un 1 %. Por eso, además de la comparación a datos iguales, hay una comparación a
  tiempo igual: el control completo contra la variante rápida con el tiempo sobrante gastado en más semillas (ensamble
  de K modelos de la variante, con K tal que el tiempo total iguale al del control). Predicción: a tiempo igual la
  variante rápida gana, y H3 es la que más rinde. (Nota del 2-nov, después de las fases 1 a 3 y antes de ver ningún
  ensamble: el ledger guardaba curvas y no predicciones, así que se agregó una fase que repite los finales guardando
  predicciones. La predicción no cambió.)
- **Contrastes principales** (9-nov, cambio `incorporar-aportes`, antes de correr H4 y las extensiones de H3): con cuatro
  hipótesis hay más de diez contrastes sin corrección por comparaciones múltiples, así que la respuesta se apoya en
  `H3-0.1`, `H4H-0.1` y `H4F-0.05` contra `C`, con réplicas (y `H4F-0.05` también a tiempo igual), fijados en
  [H4](../h4/README.md). El resto se informa como secundario.
- **Ronda 201903–201908** (12-nov): ningún veredicto cambia de lado, el IC por semilla se angosta del orden de √2 y el de
  réplicas menos. Las reglas están abajo.

Cómo salió está en [Resultados](../sampling_1/README.md#conclusiones).

### Predicción de la ronda 201903–201908

!!! info "Predicción de la ronda 201903–201908"
    Fijada el 2026-11-12, commit `159ee0d`, antes del tag `corridas-v4` y de cualquier final de la ronda.

- **Veredictos estables.** Para cada variante, con Δ por semilla (sin réplicas) y con Δ con réplicas donde existen, se
  compara el veredicto de la ronda anterior con el de la vigente. Un *cambio de lado* es pasar de *gana* o *no pierde* a
  *pierde*, o al revés; los pasos desde o hacia *indeterminado* no cuentan.
  - **Predicción**: 0 cambios de lado.
  - **Se confirma** si hay 0 cambios de lado; **se refuta** si hay 1 o más.
- **IC más angosto.** Para cada variante, la razón ancho del IC 95% de Δ por semilla en la ronda anterior / ancho en la
  vigente. Con el mismo desvío sería 1,53 (2,262/√10 contra 2,093/√20), del orden de √2.
  - **Predicción**: la mediana de la razón entre variantes está entre 1,2 y 1,9.
  - **Se confirma** si está en [1,2; 1,9]; **se refuta** si es menor que 1,2 o mayor que 1,9.
- **Con réplicas el ancho baja menos**, porque entre el 33 y el 40 % de la varianza de `H3` es entre réplicas y las
  réplicas siguen siendo 8.
  - **Predicción**: la mediana de la razón de anchos del IC de Welch de Δ con réplicas es menor que la mediana de la
    razón por semilla, y menor que 1,3.
  - **Se confirma** si se cumplen las dos desigualdades; **se refuta** si no se cumple alguna.
- `H4O-0.5`, que solo existe en la ronda vigente, tiene su predicción y su regla en [H4](../h4/README.md).

Un veredicto que cambie no se descarta ni se reemplaza: la tabla de rondas del
[Anexo de resultados](../sampling_1/anexo.md#rondas) muestra, por variante, Δ y veredicto en las dos rondas, con los dos δ.

## Dependencias

Ninguna: el control no lee de otro experimento.

## Estado

<!-- generado:estado -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

- Final entrenado con 201903-201908, 20 semillas; N* = 3,300 clientes contactados (fijo, de la ronda anterior); δ = 5.65 M$.
- Ḡ_C (réplica 0) = 282.48 M$; T_C = 797 s.
- Finales del control: 20 de 20 semillas.

<!-- /generado:estado -->

## Limitaciones

- **Hiperparámetros de cuatro meses en un final de seis.** Los hiperparámetros que eligió Optuna con train 201903–201906 se usan sin cambios en un final de seis meses
    (§ Apartamientos del baseline). Cambia el régimen del final para todas las variantes por igual.

- **`C-rep` en la misma cuenta.** `C-rep` corre en otra VM de la misma cuenta: prueba el determinismo entre máquinas, no la reproducción entre
    integrantes.
