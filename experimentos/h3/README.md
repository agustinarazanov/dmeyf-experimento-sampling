# H3 · Optimizar sobre una muestra, entrenar con todo

H3 prueba si alcanza con correr Optuna sobre una muestra chica del train y entrenar el modelo final con todas las filas.

Responde a **dónde achicar**: solo la búsqueda de hiperparámetros, con filas al azar
([Resultados § ¿Dónde achicar?](../sampling_1/README.md#donde-achicar)).

## Idea

En el baseline, casi todo el tiempo se va en Optuna: 40 trials, cada uno un entrenamiento entero. El modelo final es un
solo entrenamiento. Si los hiperparámetros que elige Optuna sobre una muestra al azar sirven también para el train
completo, se puede achicar solo la búsqueda: se acelera casi tanto como con [H1](../h1/README.md) y el final no pierde
filas.

El riesgo conocido es `min_data_in_leaf`, que es absoluto: el valor que se elige sobre la muestra puede quedar chico
para el train completo. Por eso se suman variantes que lo reescalan (`H3R`, raíz; `H3L`, lineal). Como la suerte de
Optuna pesa en el resultado, cada variante se repite con 8 réplicas de la optimización.

```mermaid
flowchart TB
  D[train 201903–201906] --> M["muestra r_opt al azar<br/>(semilla de la réplica)"]
  M --> O["Optuna: 40 trials<br/>AUC en 201908"]
  O --> HP["hiperparámetros<br/>(H3R / H3L: min_data_in_leaf reescalado)"]
  F[final 201903–201908 completo] --> E[modelo final]
  HP --> E
  E --> T["G en 201910 al corte N*"]
  style M fill:#e0a8002e,stroke:#c48a00,stroke-width:2px
```

H3 achica solo la optimización: el final entrena con todas las filas.

## Predicción

Las reglas comunes (G, Δ, δ, T, A, N\*, veredictos) están en [Control y reglas](../control/README.md). H3 se fijó en tres
momentos, cada uno antes de las corridas que decide; lo anterior no se cambió al sumar lo nuevo.

### H3 (réplica 0)

!!! info "Predicción"
    Fijada el 1-nov en `sampling_1/docs/hipotesis.md` (commit `2f05cae`) y pasada a `h3/docs/hipotesis.md` el 3-nov
    (commit `7c34254`), antes de cualquier corrida real.

- **Variable**: tasa de la muestra uniforme sobre la que corre Optuna, r_opt ∈ {0,1, 0,25}. La muestra de optimización
  se sortea con la semilla 0. El modelo final se entrena con r = 1 y con los hiperparámetros tal como salen de la
  muestra, sin reescalar `min_data_in_leaf`.
- **Métrica que decide**: el veredicto de cada r_opt contra el control.
- **Predicción**: *no pierde* con ambas tasas. Como predicción secundaria, que no decide: A ≥ 2 con r_opt = 0,25 y
  A ≥ 4 con r_opt = 0,1.
- **Se confirma** si con r_opt = 0,25 *no pierde*.
- **Se refuta** si con r_opt = 0,25 *pierde*.
- **Ninguna de las dos** si con r_opt = 0,25 sale *indeterminado*.
- **Riesgo conocido**: el `min_data_in_leaf` que se elige sobre la muestra queda chico para el train completo. Si eso
  hace perder a r_opt = 0,1, el reescalado se propone como trabajo futuro y no como una variante nueva. (El 8-nov el
  reescalado entró como variante fijada de antemano, `H3R-0.1`, en § H3 con réplicas.)

### H3 con réplicas de optimización

!!! info "Predicción"
    Fijada el 8-nov (cambio `h3-semillas-optuna`, commit `ca60a45`), antes de cualquier corrida con réplicas, y revisada en sesión limpia
    antes de la primera. Lo de la réplica 0 no cambia. Esta parte suma réplicas de la optimización para medir la suerte
    de Optuna, que el IC por semilla no ve.

**Qué queda fijo.** δ = 5,52 M$ (δ = 0,02 · Ḡ_C con Ḡ_C = 276,10 M$, la media del control en la réplica 0 de la ronda
201903–201906) y N\* = 3.300 no se recalculan con las réplicas nuevas de `C`. R = 8 réplicas (k = 0…7) queda cerrado: no
se agregan réplicas después de mirar resultados, aunque el IC quede ancho (§ Diseño › Grilla). El espacio de Optuna, los
40 trials, las semillas finales y los veredictos son los del control. En la ronda vigente las reglas se aplican con el δ
de la ronda (§ Diseño › Rondas).

**Qué es una réplica y cómo se mide.**

- **Réplica k**: la semilla del sampler TPE y la del sorteo de la muestra de optimización valen k. La réplica 0 es la ya
  corrida. Las semillas finales son las mismas en todas las réplicas.
- **Ḡ_{v,k}**: media de G en las semillas finales de la variante v en la réplica k.
- **Δ con réplicas**: media_k Ḡ_{v,k} − media_k Ḡ_{C,k}, con IC 95% de Welch entre las réplicas de cada uno (sin aparear
  por k: la réplica k de `C` y la de H3 no comparten datos). El veredicto se toma de este Δ con las reglas comunes.
- **Descomposición de la varianza** de G de cada variante: var_entre(Ḡ_{v,k}) + media_k var_dentro, con la suma de
  cuadrados exacta. Se informa; no decide ningún veredicto.

**Reglas.**

1. **H3 con réplicas** (`H3-0.1` y `H3-0.25`).
   - **Predicción**: las dos *no pierden* con réplicas: cota inferior del IC de Welch de Δ con réplicas ≥ −δ.
   - **Se confirma** la respuesta del experimento (el tradeoff vale la pena) si las dos cumplen esa regla.
   - **Se corrige** la conclusión si alguna sale *pierde* (media de Δ con réplicas < −δ) o *indeterminado* (cota
     inferior < −δ y media ≥ −δ).
2. **A contra B** (el mecanismo), sobre `H3-0.1`:
   - **Apoya (A), la muestra regulariza**: Δ con réplicas *gana* (cota inferior del IC de Welch > 0) **y** la mediana de
     `feature_fraction` entre las 8 réplicas es menor en `H3-0.1` (estudios `U0.1`, `U0.1@k`) que en `C` (estudios `C`,
     `C@k`).
   - **Apoya (B), el control tuvo mala suerte**: el IC de Welch de Δ con réplicas contiene a 0 **y** Ḡ_{C,0} queda debajo
     de la mediana de las 8 Ḡ_{C,k}.
   - **Cualquier otro resultado**: «mecanismo sin resolver». La respuesta práctica sale de la regla 1.
3. **`H3-0.05`** (Optuna sobre la muestra del 5 %, estudios `U0.05` / `U0.05@k`, final con r = 1).
   - **Predicción**: *no pierde* con réplicas **y** A ≥ 8, con A = T(`C`) / T(`H3-0.05`) y la T de cada una como mediana
     entre sus 8 réplicas.
   - **Se confirma** si se cumplen las dos condiciones; **se refuta** si sale *pierde* o A < 8; si no, *indeterminado*.
4. **`H3R-0.1`** (los estudios de `H3-0.1` con `min_data_in_leaf` × √(1/r) = × √10 en el final, recortado a
   [1; 8000]). Se mide la diferencia D = G(`H3R-0.1`) − G(`H3-0.1`), apareada por semilla dentro de cada réplica; se toma
   la media de D por réplica y el IC t 95% entre las 8 réplicas (7 g.l.).
   - **Mejora** si la cota inferior del IC de D es > 0; **empeora** si la cota superior es < 0; **no cambia** en
     cualquier otro caso.
   - **Predicción**: *mejora* (el riesgo conocido). Además, `H3R-0.1` recibe su propio veredicto con réplicas contra
     `C`, con la regla 1.

### Extensiones del exploratorio `validacion_50_semillas`

!!! info "Predicción"
    Fijada el 9-nov (cambio `incorporar-aportes`, commit `d9d9303`), antes de cualquier corrida de estas variantes, y revisada en sesión
    limpia antes de la primera. Lo anterior no cambia.

**Origen: vienen de mirar 201910.** Las cuatro variantes salen del exploratorio
[`validacion_50_semillas`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/sampling_1/exploratorios/validacion_50_semillas/README.md)
(origen en el commit `9e1889e`), que eligió el reescalado √(1/r) frente al lineal y descartó el muestreo por cliente
mirando su ganancia en 201910. Por eso estos contrastes no cuentan con un mes de test que no se haya mirado. No se usa
otro mes (consigna, Zulip 208135): entran todas, con regla escrita antes de correr, y ninguna se elige ni se descarta
por 201910.

Para las diferencias apareadas se usa el esquema de la regla 4: D = G(v₁) − G(v₂) por semilla dentro de cada réplica,
media de D por réplica e IC t 95% entre las 8 réplicas (7 g.l.).

5. **Raíz contra lineal** (`H3R-r` − `H3L-r`, r ∈ {0,25, 0,1}, apareada: comparten estudios). **Gana la raíz** si la cota
   inferior del IC de D es > 0; **gana la lineal** si la cota superior es < 0; **no cambia** en otro caso.
   **Predicción**: gana la raíz con las dos tasas, que es lo que reporta el exploratorio.
6. **Raíz contra nada en r = 0,25** (`H3R-0.25` − `H3-0.25`, apareada), con la regla de la 4. **Predicción**: *mejora*,
   por el mismo riesgo conocido.
7. **Por cliente** (`H3K-0.1` − `H3-0.1`). D_K = media_k Ḡ_{`H3K-0.1`,k} − media_k Ḡ_{`H3-0.1`,k}, con IC 95% de Welch
   entre las 8 réplicas de cada una (sin aparear: no comparten estudios). **Empeora** si la cota superior del IC de D_K
   es < 0; **mejora** si la cota inferior es > 0; **no cambia** en otro caso. **Predicción**: *empeora*, que es lo que
   reporta el exploratorio.
8. Cada variante nueva recibe además su veredicto con réplicas contra `C` con la regla 1. Se informa; no cambia el
   veredicto de H3, que es el de la regla 1 sobre `H3-0.1` y `H3-0.25`.

**Comparaciones múltiples.** Con `h4` son más de diez contrastes, sin corrección. La respuesta del experimento se apoya
en los contrastes principales fijados en [H4](../h4/README.md) (`H3-0.1`, `H4H-0.1`, `H4F-0.05` contra `C`); las reglas 5
a 8 son secundarias.

### `H3-0.5` (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Escrito el 13-nov-2026, antes de cualquier corrida de la variante, y revisado en sesión limpia antes de la primera. Lo de
arriba no se reescribe. `H3-0.5` completa la fila "al azar, solo búsqueda" de la grilla común
([`sampling_1/corridas.md`](../sampling_1/corridas.md) § Fases), que tenía 0,25; 0,1 y 0,05.

**Origen: se agrega después de ver 201910.** La variante se decide después de ver en 201910 todas las celdas vecinas
(`H3-*` con réplicas, `U0.5` y `H4O-0.5`). Entra con predicción y regla escritas acá antes de correr, junto con el resto
de la grilla, y no se elige ni se descarta por su resultado. El informe la lista entre las limitaciones ("Ideas que vienen
de mirar el test").

**"Siempre OP" (Zulip 211718).** Como el resto de H3, busca sobre una muestra y entrena el final con otra receta. Es un
apartamiento decidido el 13-nov porque es la hipótesis misma, y se declara con su id en el informe.

- **Variante.** `H3-0.5`, método `opt-muestra`: Optuna sobre la muestra al azar del 50 % (estudios `U0.5` / `U0.5@k`, de
  `h1`, compartidos con `U0.5`), final con r = 1 y los hiperparámetros sin reescalar. 8 réplicas, 20 semillas finales.
- **Qué se mide.** Ronda 201903–201908 ([`control`](../control/README.md) § Predicción de la ronda 201903–201908):
  N\* = 3.300 y δ = 0,02 · Ḡ_C de esa ronda (5,65 M$). Δ con réplicas e IC de Welch como en § H3 con réplicas de
  optimización. A con una sola referencia y T como mediana entre réplicas ([`control`](../control/README.md) § Medición
  de tiempos).

9. **`H3-0.5` contra `C`.**
   - **Predicción**: *no pierde* con réplicas (cota inferior del IC de Welch de Δ con réplicas ≥ −δ) **y** A ≥ 2.
   - **Se confirma** si se cumplen las dos; **se refuta** si sale *pierde* (media de Δ con réplicas < −δ) o A < 2; si
     no, *indeterminado*.

No cambia el veredicto de H3, que sigue siendo el de la regla 1. Las diferencias directas `U{r}` − `H3-{r}` y
`H4P-{r}` − `H3-{r}` están en [`h4`](../h4/README.md) § Grilla común.

## Diseño

Lo que no se dice acá (máquina, parámetros fijos de LightGBM, semillas finales, métricas) es lo del
[control](../control/README.md).

### Variantes

Un *estudio* es una búsqueda de Optuna: `U0.25` busca sobre una muestra uniforme del 25 % de train, y `U0.25@k` es la
misma búsqueda repetida con semilla k. Esas repeticiones son las *réplicas*, que miden cuánto depende el resultado de la
suerte de la búsqueda; la réplica 0 es la búsqueda original.

| variante | búsqueda de hiperparámetros | final |
|---|---|---|
| `H3-0.5` | `U0.5` / `U0.5@k` | r = 1 |
| `H3-0.25` | `U0.25` / `U0.25@k` | r = 1 |
| `H3-0.1` | `U0.1` / `U0.1@k` | r = 1 |
| `H3-0.05` | `U0.05` / `U0.05@k` | r = 1 |
| `H3R-0.1` | `U0.1` / `U0.1@k` | r = 1, `min_data_in_leaf` × √10 |
| `H3R-0.25` | `U0.25` / `U0.25@k` | r = 1, `min_data_in_leaf` × 2 (raíz) |
| `H3L-0.25` | `U0.25` / `U0.25@k` | r = 1, `min_data_in_leaf` × 4 (lineal) |
| `H3L-0.1` | `U0.1` / `U0.1@k` | r = 1, `min_data_in_leaf` × 10 (lineal) |
| `H3K-0.1` | `K0.1` / `K0.1@k` | r = 1, sin reescalar |

- Todas optimizan con el espacio del control (5 hp) y tienen 8 réplicas. Entre las `H3-*`, `H3-0.5` completa la fila
  «al azar, solo búsqueda» de la grilla común, con las tasas 0,5; 0,25; 0,1 y 0,05, y sin reescalar `min_data_in_leaf`.

#### Extensiones: reescalado de `min_data_in_leaf` y muestra por cliente

`H3R` y `H3L` (reescalado) y `H3K` (muestra por cliente) son extensiones de H3: usan la misma búsqueda sobre una
muestra y entrenan el final con todo, y cambian una sola cosa. Su regla está en la Predicción (reglas 5 a 8).

- **Reescalados**: el `min_data_in_leaf` del estudio se multiplica por el factor, se redondea y se recorta a [1; 8000];
  los demás hiperparámetros no cambian. Los efectivos quedan en la fila del ledger. `H3R-r` y `H3L-r` leen el mismo
  estudio que `H3-r`, así que las tres se aparean por réplica y semilla.
- **Muestra por cliente (`K0.1`)**: en la réplica k se sortea, con semilla k, el 10 % de los `numero_de_cliente` del train
  201903–201906, y se toman todas las filas de esos clientes. La cantidad de filas queda cerca del 10 % del train y se
  registra la exacta. Optuna de 40 trials sobre esa muestra, TPE con semilla k, AUC en 201908. Es una reconstrucción: el
  exploratorio describe el muestreo por cliente («a igual volumen» que el muestreo por filas) pero no trae el código.

### Estudios y réplicas

- **Réplica 0**: los estudios `U{r}` son de `h1` y H3 los lee de su `ledger/hp/`; por qué se comparten está en
  [H1](../h1/README.md). `H3-0.5` usa `U0.5`, `H3-0.25` usa `U0.25`, `H3-0.1`, `H3R-0.1` y `H3L-0.1` el `U0.1`, y
  `H3-0.05` el `U0.05`.
- **Réplica k**: semilla del sampler TPE = semilla del sorteo de la muestra de optimización = k. Las réplicas k ≥ 1 se
  llaman `<estudio>@k` (`U0.1@3`); el `id` de la fila suma `@k` solo si k ≥ 1 y la columna `replica_opt` guarda k.
- **Dueños**: todos los estudios `U{r}` y `U{r}@k` son de `h1` (`h1/ledger/hp/`), para que `h1` no dependa de `h3` y `h3`
  de `h1`. `K0.1` y `K0.1@k` son de `h3`. `C@k` es de `control`. La regla vive en el registro (`comun/variantes.py`) y la
  cubre un test.
- Pedir una réplica k ≥ 1 de una variante que no la admite falla antes de cargar datos.

### Grilla

- **Variantes y réplicas**: las 9 variantes × 8 réplicas (k = 0…7) × 20 semillas finales con la ventana 201903–201908.
  T suma el tiempo del estudio de la réplica (compartido con la `U{r}` de H1) y la media del final; es la
  mediana entre réplicas, y A usa una sola referencia ([`control`](../control/README.md) § Medición de tiempos).
- **Estudios propios**: `C@1…7` (de `control`) y `K0.1`, `K0.1@1…7` (de `h3`); el resto son de `h1`. Las listas
  están en [Fases](../sampling_1/corridas.md) § Fases.
- **Por qué R = 8.** Si el desvío entre réplicas fuera de unos 4 M$ (la escala que sugería el exploratorio
  [`sensibilidad_muestra`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/h3/sensibilidad_muestra/README.md)),
  con 8 contra 8 el IC de Welch tiene una semiamplitud cercana a ±4,3 M$: alcanza para decidir *no pierde* si el Δ real
  está cerca de 0. Con 5 réplicas la semiamplitud sube a unos ±5,8 y *no pierde* deja de ser decidible; con 10 el costo
  crece un 30 % para ganar poco.
### Reoptimización y ventana del final

La ventana vigente (201903–201908) reusa el diseño de los estudios (Optuna con 201903–201906 y AUC en 201908) y entrena
los finales con las 20 semillas. Los reescalados de `H3R` y `H3L` se calculan con la r del estudio.

**Por qué `H3` no reoptimiza para el final.** La regla del curso pide reoptimizar siempre que cambia el dataset («siempre
OP», Zulip 211718). En `H3` el dataset de la búsqueda (una muestra de tasa r de 201903–201906) y el del final
(201903–201908 completo) difieren a propósito: esa diferencia es la hipótesis. H3 pregunta si los hiperparámetros
elegidos sobre una muestra sirven para entrenar con todo; reoptimizar con el set del final convertiría a `H3` en el
control y dejaría la pregunta sin respuesta. Es un apartamiento declarado de la regla, que `H3-0.5` comparte con el resto
de la familia. El caso de `h4`, donde esa regla sí da lugar a una variante (`H4O-0.5`), está en [H4](../h4/README.md).

## Dependencias

- `control`: finales de `C` y de sus réplicas `C@1…7`, N\* y δ.
- `h1`: todos los estudios `U{r}` y sus réplicas `U{r}@k`, r ∈ {0,5; 0,25; 0,1; 0,05} (`ledger/hp/U{r}.json` y
  `ledger/hp/U{r}@k.json`), que usan `H3-*`, `H3R-*` y `H3L-*`. El estudio propio `K0.1` y sus `K0.1@k` no agregan
  dependencias.

## Resultado

<!-- generado:resultado -->
Final entrenado con 201903-201908, 20 semillas; N* = 3,300 clientes contactados (fijo, de la ronda anterior); δ = 5.65 M$. Vale la pena: no pierde y acelera 2× o más.


![9 de 9 variantes no pierden y aceleran 2× o más; la más rápida entre ellas es H3-0.05 (10.6×)](figuras/tradeoff_h3.svg)


<table><tr><th>variante</th><th>R</th><th>G media (M$)</th><th>Δ [IC 95%] (M$)</th><th>ΔAUC [IC 95%]</th><th>T mediana (s)</th><th>aceleración (×)</th><th>ganancia contra el control</th><th>vale la pena (no pierde y ≥ 2×)</th></tr><tr><td>C</td><td>—</td><td>281.78</td><td>—</td><td>—</td><td>1,002</td><td>1.00</td><td>—</td><td>—</td></tr><tr><td>H3-0.5</td><td><span class='v'>8</span></td><td>281.70</td><td><span class='v'>-0.08</span><span class='ic'>[-3.17; 3.00]</span><span class='icbar' style='--l:17.6%;--r:75.1%;--z:47.1%'></span></td><td><span class='v'>-0.0000</span><span class='ic'>[-0.0010; +0.0010]</span><span class='icbar' style='--l:59.6%;--r:91.0%;--z:75.4%'></span></td><td>440</td><td><span class='v'>2.28</span><span class='ic'>[1.55; 2.85]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3-0.25</td><td><span class='v'>8</span></td><td>283.20</td><td><span class='v'>1.42</span><span class='ic'>[-2.82; 5.67]</span><span class='icbar' style='--l:20.8%;--r:100.0%;--z:47.1%'></span></td><td><span class='v'>-0.0009</span><span class='ic'>[-0.0021; +0.0004]</span><span class='icbar' style='--l:43.2%;--r:81.4%;--z:75.4%'></span></td><td>229</td><td><span class='v'>4.38</span><span class='ic'>[2.93; 5.33]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3-0.1</td><td><span class='v'>8</span></td><td>283.49</td><td><span class='v'>1.71</span><span class='ic'>[-1.07; 4.49]</span><span class='icbar' style='--l:37.2%;--r:89.0%;--z:47.1%'></span></td><td class='sig-neg'><span class='v'>-0.0017</span><span class='ic'>[-0.0030; -0.0003]</span><span class='icbar' style='--l:29.5%;--r:70.4%;--z:75.4%'></span></td><td>129</td><td><span class='v'>7.76</span><span class='ic'>[5.56; 10.04]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3-0.05</td><td><span class='v'>8</span></td><td>283.86</td><td class='mejor'><span class='v'>2.08</span><span class='ic'>[-0.87; 5.02]</span><span class='icbar' style='--l:39.0%;--r:93.9%;--z:47.1%'></span></td><td><span class='v'>-0.0020</span><span class='ic'>[-0.0041; +0.0000]</span><span class='icbar' style='--l:13.7%;--r:75.6%;--z:75.4%'></span></td><td>95</td><td class='mejor'><span class='v'>10.56</span><span class='ic'>[8.00; 12.69]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3R-0.1</td><td><span class='v'>8</span></td><td>283.37</td><td><span class='v'>1.59</span><span class='ic'>[-1.80; 4.98]</span><span class='icbar' style='--l:30.3%;--r:93.5%;--z:47.1%'></span></td><td><span class='v'>-0.0008</span><span class='ic'>[-0.0023; +0.0006]</span><span class='icbar' style='--l:40.6%;--r:84.4%;--z:75.4%'></span></td><td>130</td><td><span class='v'>7.71</span><span class='ic'>[5.53; 9.99]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3R-0.25</td><td><span class='v'>8</span></td><td>283.72</td><td><span class='v'>1.95</span><span class='ic'>[-0.85; 4.74]</span><span class='icbar' style='--l:39.2%;--r:91.3%;--z:47.1%'></span></td><td><span class='v'>+0.0000</span><span class='ic'>[-0.0011; +0.0011]</span><span class='icbar' style='--l:58.4%;--r:92.5%;--z:75.4%'></span></td><td>225</td><td><span class='v'>4.46</span><span class='ic'>[2.95; 5.32]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3L-0.25</td><td><span class='v'>8</span></td><td>283.00</td><td><span class='v'>1.22</span><span class='ic'>[-1.59; 4.03]</span><span class='icbar' style='--l:32.3%;--r:84.7%;--z:47.1%'></span></td><td><span class='v'>+0.0004</span><span class='ic'>[-0.0008; +0.0016]</span><span class='icbar' style='--l:63.1%;--r:100.0%;--z:75.4%'></span></td><td>222</td><td><span class='v'>4.51</span><span class='ic'>[2.91; 5.32]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3L-0.1</td><td><span class='v'>8</span></td><td>281.92</td><td><span class='v'>0.14</span><span class='ic'>[-3.30; 3.57]</span><span class='icbar' style='--l:16.3%;--r:80.4%;--z:47.1%'></span></td><td><span class='v'>-0.0005</span><span class='ic'>[-0.0020; +0.0010]</span><span class='icbar' style='--l:45.0%;--r:90.4%;--z:75.4%'></span></td><td>130</td><td><span class='v'>7.73</span><span class='ic'>[5.52; 9.93]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr><tr><td>H3K-0.1</td><td><span class='v'>8</span></td><td>281.57</td><td><span class='v'>-0.21</span><span class='ic'>[-5.05; 4.63]</span><span class='icbar' style='--l:0.0%;--r:90.2%;--z:47.1%'></span></td><td class='sig-neg'><span class='v'>-0.0033</span><span class='ic'>[-0.0050; -0.0017]</span><span class='icbar' style='--l:0.0%;--r:49.8%;--z:75.4%'></span></td><td>126</td><td><span class='v'>7.98</span><span class='ic'>[4.89; 9.46]</span></td><td><span class='pill ok'>no pierde</span></td><td>sí</td></tr></table>


![H3: con N* = 3,300 clientes contactados el control rinde 281.6 M$ y la mejor variante, H3-0.25, 287.6 M$; banda: P10–P90 entre semillas, punteada: mediana del control](figuras/curvas_H3.svg)



![H3: en N* = 3,300 clientes contactados, 2 de 9 variantes quedan por debajo del control (H3-0.5, H3K-0.1); línea: mediana, banda: mín–máx entre semillas](figuras/curva_diferencia_H3.svg)

<!-- /generado:resultado -->

Las tablas con réplicas, la varianza entre réplicas y las diferencias entre variantes están en
[Resultados](../sampling_1/README.md).

## Veredicto

!!! success "Veredicto con réplicas: confirmada"
    Optimizar sobre una muestra del 5 %, 10 % o 25 % y entrenar con todas las filas no pierde contra el control, también
    cuando se mide la suerte de Optuna con 8 réplicas, y acelera de 4,38 a 10,56 veces; con 50 % tampoco pierde y
    acelera 2,28 veces. Con réplicas Δ queda entre 1,42 y 2,08 M$ en las tres primeras tasas, con IC que contiene a 0, y
    el mecanismo (regulariza o suerte del control) queda sin resolver. Las 9 variantes de H3, extensiones incluidas, *no
    pierden* contra el control y valen la pena. El δ de la ronda vigente es 5,65 M$ (el de § Predicción, 5,52 M$, era el
    de la ronda anterior: la regla de δ saca su valor del control de cada ronda).

    - Regla 1, `H3-0.1` y `H3-0.25` *no pierden* con réplicas: **se cumplió**. Las cotas inferiores del IC de Welch
      (−1,07 y −2,82 M$) quedan por encima de −5,65 M$.
    - Regla 2, A contra B: **mecanismo sin resolver**. En `H3-0.1`, el IC de Δ con réplicas, [−1,07; 4,49] M$, contiene
      a 0, pero Ḡ_{C,0} = 282,48 M$ queda arriba de la mediana de las 8 Ḡ_{C,k}, 282,40 M$, así que (B) no se cumple.
      (A) tampoco: Δ con réplicas no *gana* (cota inferior −1,07 < 0), aunque la mediana de `feature_fraction` sí es
      menor en `H3-0.1` (0,518) que en `C` (0,641).
    - Regla 3, `H3-0.05` *no pierde* y A ≥ 8: **se cumplió**. Cota inferior −0,87 ≥ −5,65 M$ y A = 10,56, con T como
      mediana entre réplicas (95 s).
    - Regla 9, `H3-0.5` *no pierde* y A ≥ 2: **se cumplió**. Δ −0,08 M$, IC de Welch [−3,17; 3,00], cota inferior
      ≥ −5,65 M$; A = 2,28, con intervalo [1,55; 2,85] que baja de 2 (la regla decide con A puntual). Muestrear también
      el final (`U{r}` − `H3-{r}`) *empeora* en las cuatro tasas (tabla «Diferencias entre variantes» del
      [Anexo](../sampling_1/anexo.md)).
    - Secundaria, A ≥ 2 con r_opt = 0,25 y A ≥ 4 con r_opt = 0,1: **se cumplió**, con A = 4,38 y 7,76.

### Extensiones: reescalado y muestra por cliente

Reglas 4 a 8 de la Predicción. No cambian el veredicto de H3, que es el de la regla 1.

- **Regla 4, `H3R-0.1`: no cambia.** La diferencia apareada `H3R-0.1` − `H3-0.1` es −0,12 M$ con IC t entre réplicas
  [−1,95; 1,71] (7 g.l.). La predicción (*mejora*) **no se cumplió**: reescalar `min_data_in_leaf` × √10 no mueve la
  ganancia. Contra `C`, `H3R-0.1` *no pierde* (cota inferior −1,80 M$).

- **Regla 5, raíz contra lineal: gana la raíz en r = 0,1; no cambia en r = 0,25.** `H3R-0.1` − `H3L-0.1` = 1,45 M$, IC t
  entre réplicas [0,65; 2,25]. `H3R-0.25` − `H3L-0.25` = 0,72 M$, IC [−0,90; 2,35]. La predicción (gana la raíz con las
  dos tasas) **se cumplió solo en r = 0,1**. La raíz no es mejor que no reescalar (reglas 4 y 6).
- **Regla 6, raíz contra nada en r = 0,25: no cambia.** `H3R-0.25` − `H3-0.25` = 0,52 M$, IC [−1,59; 2,64]. La predicción
  (*mejora*) **no se cumplió**.
- **Regla 7, por cliente: no cambia.** D_K = −1,93 M$, IC de Welch [−6,68; 2,83]. La predicción (*empeora*) **no se
  cumplió**. `H3K-0.1` es la variante con más varianza entre réplicas (58 %, sd 5,51 M$); una explicación posible, que no
  se probó, es que sortear clientes enteros hace más distinta una muestra de otra que sortear filas.
- **Regla 8, contra `C`, cada una *no pierde* con réplicas**: cotas inferiores del IC de Welch −0,85 (`H3R-0.25`), −1,59
  (`H3L-0.25`), −3,30 (`H3L-0.1`) y −5,05 M$ (`H3K-0.1`), todas ≥ −5,65 M$.

La única diferencia que sale distinta de 0 (raíz contra lineal en r = 0,1) es una de las más de diez sin corrección
por comparaciones múltiples.

**AUC y ganancia.** El veredicto es el de ganancia (Zulip 208135). Las cuatro `H3-*` tienen ΔAUC
negativo con Δ de ganancia positivo. En `H3-0.1` la diferencia de AUC es distinguible de 0 (−0,0017, IC [−0,0030;
−0,0003]) mientras Δ de ganancia es 1,71 M$ con IC que contiene a 0. `H3K-0.1` es la única extensión con ΔAUC
distinguible de 0 (−0,0033, IC [−0,0050; −0,0017]) y su Δ de ganancia (−0,21 M$) casi no se mueve. El AUC mide el orden
de todos los clientes; G solo los 3.300 de arriba, así que un modelo puede ordenar algo peor en general y quedar igual o
mejor en la cabeza.

**¿Alcanzan 50 semillas finales?** No, si hay un solo estudio de Optuna. Entre el 24 % (`H3-0.1`) y el 50 % (`H3-0.25`)
de la varianza de una corrida es suerte de Optuna (sd entre réplicas de 2,38 a 4,72 M$; 25 % en `C`). Más semillas
finales achican solo la otra parte: con un estudio, la parte de Optuna es el 77 % (`C`) a 91 % (`H3-0.25`) de la varianza
de Ḡ con 10 semillas y el 94 % a 98 % con 50. El desvío de Ḡ con un estudio baja apenas, de 2,96 a 2,67 M$ en `C` al
pasar de 10 a 50 semillas. Pasar de 10 a 20 semillas en la ronda vigente angostó el IC por semilla pero no el de
réplicas. Para medir Δ hace falta repetir la optimización, no solo el final.

## Limitaciones

- **`H3-0.5` agregada después de mirar 201910.** Se decidió después de ver el test en las celdas vecinas, con regla
    previa; su veredicto se suma a los de la grilla común sin corrección por comparaciones múltiples.

- **Depende de `h1`.** H3 usa los estudios `U0.5`, `U0.25`, `U0.1` y `U0.05` de `h1`, también sus réplicas `@k`, que desde la fase 8 son de `h1`. Δ(`H3-0.25`) y
    Δ(`U0.25`) de la réplica 0 tienen la misma suerte de optimización y no son evidencia independiente entre sí. Sin
    `h1`, H3 no se puede correr ni consolidar.

- **Variantes que comparten estudios.** `H3R-0.1` y `H3-0.1` comparten todos sus estudios: su diferencia aísla el reescalado y no es evidencia independiente
    sobre H3. Lo mismo vale para `H3R-0.25`, `H3L-0.25` y `H3-0.25`, y para `H3L-0.1`.

- **Reescalado y final de seis meses.** `H3R` y `H3L` muestran que reescalar `min_data_in_leaf` no mejora a no hacerlo en las muestras de búsqueda, pero eso
    no se probó para el salto de cuatro a seis meses del final.

- **Test ya mirado.** Las extensiones salen de un exploratorio que eligió el reescalado √(1/r) frente al lineal y descartó el muestreo por
    cliente mirando su ganancia en 201910. Entraron todas, con reglas escritas antes de correr, y ninguna se eligió ni se
    descartó acá por 201910, pero estos contrastes no cuentan con un mes de test que no se haya mirado.

- **Comparaciones múltiples.** Con `h4` son más de diez contrastes sin corrección: con un 5 % de error por contraste, alguno puede salir
    significativo por azar. Las reglas 5 a 8 son secundarias.

- **Ocho réplicas.** El IC de Welch quedó lo bastante angosto para decidir *no pierde*, pero no para separar de cero una ventaja del
    tamaño de la medida (1,42 a 2,08 M$). R = 8 quedó cerrado antes de correr y no se agregan réplicas. Los tiempos
    vienen de VMs `n2-highmem-8` distintas; T es la mediana entre réplicas y no se compara entre rondas.
