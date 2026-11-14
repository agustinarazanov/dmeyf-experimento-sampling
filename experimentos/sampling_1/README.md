# Resultados

Todas las variantes de las cuatro hipótesis contra el control, con la respuesta a la pregunta del experimento.

## Pregunta

**¿Vale la pena el tradeoff entre velocidad y pérdida de performance?** (Zulip 208986, 1-nov.)

Sobre el baseline (Zulip 208135), ¿cuánto tiempo se ahorra y cuánta ganancia se pierde en test (201910) si se usan menos
filas para entrenar u optimizar? En H1, H2 y H3 la proporción de BAJA+1 ∪ BAJA+2 queda igual, en esperanza, en todas las
variantes; el undersampling de la clase mayoritaria lo estudia Sampling_2. H4 es la excepción declarada: conserva todas
las bajas y recorta solo CONTINUA.

| hipótesis | qué achica | página |
|---|---|---|
| H1 | el train, al azar, en la búsqueda y en el final | [H1](../h1/README.md) |
| H2 | las filas que ve cada árbol (`bagging_fraction`, GOSS) | [H2](../h2/README.md) |
| H3 | solo la búsqueda de Optuna; el final entrena con todo | [H3](../h3/README.md) |
| H4 | CONTINUA, conservando todas las bajas, en la búsqueda o en el final | [H4](../h4/README.md) |

Una variante **vale la pena** si *no pierde* contra el control y además es al menos 2 veces más rápida (aceleración ≥ 2). Las
reglas (G, Δ, δ, T, aceleración, N\*, veredictos) están en [Control y reglas](../control/README.md); cómo se corrió, en
[Corridas](corridas.md#protocolo).

## Respuesta

!!! success "Respuesta"
    Vale la pena achicar la **optimización**, al azar: correr Optuna sobre el 10 % de las filas y entrenar el final con
    todas no pierde contra el control y es casi 8 veces más rápido. Si además se quiere un final más rápido, conservar
    todas las bajas y la mitad de CONTINUA con peso 2 tampoco pierde. Ninguna de las dos es una mejora de ganancia por
    modelo: es lo mismo, más rápido, y el tiempo que sobra se puede gastar en ensamblar.

<!-- generado:mapa -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![15 de 30 variantes no pierden y aceleran 2× o más; la más rápida entre ellas es H4F-0.05 (12.5×)](figuras/tradeoff.svg)

<!-- /generado:mapa -->

## ¿Qué conviene achicar?

La optimización domina el tiempo del control, así que achicarla es lo que más acelera. La grilla dice qué variantes
pierden; la tabla, cuánto y a qué velocidad.

<!-- generado:grilla -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![De 30 variantes: no pierden 17, pierden 9, indeterminadas 4, pendientes 0](figuras/grilla_veredictos.svg)

<!-- /generado:grilla -->

<!-- generado:desglose -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![En el control la optimización es el 94 % de T (748 s de 797 s); la variante con la optimización más corta, U0.05, la baja a 67 s](figuras/desglose_tiempo.svg)

<!-- /generado:desglose -->

Las variantes `U*`, `B*` y `GOSS` no tienen réplicas (pierden o no aceleran, y las réplicas no cambian eso). En `C`, H3
y H4, el veredicto sale de Δ con 8 réplicas de la optimización. La primera pestaña muestra la mejor variante de cada
hipótesis, valga la pena o no: la de H2, `B0.25`, no pierde pero acelera 1,23 veces, así que no vale la pena.

<!-- generado:bloque-a -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

Final entrenado con 201903-201908, 20 semillas por réplica; N* = 3,300 clientes contactados; Ḡ_C (réplica 0) = 282.48 M$; Ḡ_C con réplicas = 281.78 M$ (R=8); ensamble de 20 semillas del control = 286.55 M$.

Ḡ, T y la aceleración salen de la réplica 0 en las variantes sin réplicas; en las que tienen réplicas (columna R), Ḡ es la media entre réplicas, T la mediana entre réplicas y la aceleración = T_C / T con T_C también mediana entre réplicas, así que se comparan con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.

=== "Lo mejor de cada hipótesis"

    <table><tr><th>variante</th><th>hipótesis</th><th>R</th><th>Δ [IC 95%] (M$)</th><th>aceleración (×)</th><th>ganancia contra el control</th></tr><tr><td>U0.5</td><td>H1</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-3.64</span><span class='ic'>[-6.58; -0.71]</span><span class='icbar' style='--l:0.0%;--r:50.6%;--z:56.7%'></span></td><td><span class='v'>2.37</span></td><td><span class='pill ind'>indeterminado</span></td></tr><tr><td>B0.5</td><td>H2</td><td><span class='v'>8</span></td><td><span class='v'>0.35</span><span class='ic'>[-2.16; 2.86]</span><span class='icbar' style='--l:38.1%;--r:81.4%;--z:56.7%'></span></td><td><span class='v'>1.18</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3-0.05</td><td>H3</td><td><span class='v'>8</span></td><td class='mejor'><span class='v'>2.08</span><span class='ic'>[-0.87; 5.02]</span><span class='icbar' style='--l:49.3%;--r:100.0%;--z:56.7%'></span></td><td><span class='v'>10.56</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4F-0.05</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>1.41</span><span class='ic'>[-1.58; 4.40]</span><span class='icbar' style='--l:43.1%;--r:94.7%;--z:56.7%'></span></td><td class='mejor'><span class='v'>12.50</span></td><td><span class='pill ok'>no pierde</span></td></tr></table>

=== "H1"

    <table><tr><th>variante</th><th>hipótesis</th><th>R</th><th>Δ [IC 95%] (M$)</th><th>aceleración (×)</th><th>ganancia contra el control</th></tr><tr><td>U0.05</td><td>H1</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-27.74</span><span class='ic'>[-30.35; -25.13]</span><span class='icbar' style='--l:0.0%;--r:17.2%;--z:100.0%'></span></td><td><span class='v'>15.94</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>U0.1</td><td>H1</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-17.47</span><span class='ic'>[-20.23; -14.71]</span><span class='icbar' style='--l:33.3%;--r:51.6%;--z:100.0%'></span></td><td><span class='v'>10.13</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>U0.25</td><td>H1</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-8.09</span><span class='ic'>[-11.58; -4.60]</span><span class='icbar' style='--l:61.8%;--r:84.8%;--z:100.0%'></span></td><td><span class='v'>4.99</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>U0.5</td><td>H1</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-3.64</span><span class='ic'>[-6.58; -0.71]</span><span class='icbar' style='--l:78.3%;--r:97.7%;--z:100.0%'></span></td><td><span class='v'>2.37</span></td><td><span class='pill ind'>indeterminado</span></td></tr></table>

=== "H2"

    <table><tr><th>variante</th><th>hipótesis</th><th>R</th><th>Δ [IC 95%] (M$)</th><th>aceleración (×)</th><th>ganancia contra el control</th></tr><tr><td>B0.05</td><td>H2</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-14.55</span><span class='ic'>[-17.44; -11.66]</span><span class='icbar' style='--l:0.0%;--r:28.5%;--z:85.9%'></span></td><td><span class='v'>3.09</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>B0.1</td><td>H2</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-7.31</span><span class='ic'>[-9.76; -4.86]</span><span class='icbar' style='--l:37.8%;--r:62.0%;--z:85.9%'></span></td><td><span class='v'>2.96</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>B0.25</td><td>H2</td><td><span class='v'>8</span></td><td><span class='v'>-2.20</span><span class='ic'>[-4.95; 0.55]</span><span class='icbar' style='--l:61.5%;--r:88.6%;--z:85.9%'></span></td><td class='mejor'><span class='v'>1.67</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>GOSS</td><td>H2</td><td><span class='v'>8</span></td><td><span class='v'>-2.96</span><span class='ic'>[-6.13; 0.21]</span><span class='icbar' style='--l:55.7%;--r:86.9%;--z:85.9%'></span></td><td><span class='v'>1.27</span></td><td><span class='pill ind'>indeterminado</span></td></tr><tr><td>B0.5</td><td>H2</td><td><span class='v'>8</span></td><td class='mejor'><span class='v'>0.35</span><span class='ic'>[-2.16; 2.86]</span><span class='icbar' style='--l:75.3%;--r:100.0%;--z:85.9%'></span></td><td><span class='v'>1.18</span></td><td><span class='pill ok'>no pierde</span></td></tr></table>

=== "H3"

    <table><tr><th>variante</th><th>hipótesis</th><th>R</th><th>Δ [IC 95%] (M$)</th><th>aceleración (×)</th><th>ganancia contra el control</th></tr><tr><td>H3-0.05</td><td>H3</td><td><span class='v'>8</span></td><td class='mejor'><span class='v'>2.08</span><span class='ic'>[-0.87; 5.02]</span><span class='icbar' style='--l:39.0%;--r:93.9%;--z:47.1%'></span></td><td class='mejor'><span class='v'>10.56</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3K-0.1</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>-0.21</span><span class='ic'>[-5.05; 4.63]</span><span class='icbar' style='--l:0.0%;--r:90.2%;--z:47.1%'></span></td><td><span class='v'>7.98</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3-0.1</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>1.71</span><span class='ic'>[-1.07; 4.49]</span><span class='icbar' style='--l:37.2%;--r:89.0%;--z:47.1%'></span></td><td><span class='v'>7.76</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3L-0.1</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>0.14</span><span class='ic'>[-3.30; 3.57]</span><span class='icbar' style='--l:16.3%;--r:80.4%;--z:47.1%'></span></td><td><span class='v'>7.73</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3R-0.1</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>1.59</span><span class='ic'>[-1.80; 4.98]</span><span class='icbar' style='--l:30.3%;--r:93.5%;--z:47.1%'></span></td><td><span class='v'>7.71</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3L-0.25</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>1.22</span><span class='ic'>[-1.59; 4.03]</span><span class='icbar' style='--l:32.3%;--r:84.7%;--z:47.1%'></span></td><td><span class='v'>4.51</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3R-0.25</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>1.95</span><span class='ic'>[-0.85; 4.74]</span><span class='icbar' style='--l:39.2%;--r:91.3%;--z:47.1%'></span></td><td><span class='v'>4.46</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3-0.25</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>1.42</span><span class='ic'>[-2.82; 5.67]</span><span class='icbar' style='--l:20.8%;--r:100.0%;--z:47.1%'></span></td><td><span class='v'>4.38</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H3-0.5</td><td>H3</td><td><span class='v'>8</span></td><td><span class='v'>-0.08</span><span class='ic'>[-3.17; 3.00]</span><span class='icbar' style='--l:17.6%;--r:75.1%;--z:47.1%'></span></td><td><span class='v'>2.28</span></td><td><span class='pill ok'>no pierde</span></td></tr></table>

=== "H4"

    <table><tr><th>variante</th><th>hipótesis</th><th>R</th><th>Δ [IC 95%] (M$)</th><th>aceleración (×)</th><th>ganancia contra el control</th></tr><tr><td>H4F-0.05</td><td>H4</td><td><span class='v'>8</span></td><td class='mejor'><span class='v'>1.41</span><span class='ic'>[-1.58; 4.40]</span><span class='icbar' style='--l:70.4%;--r:100.0%;--z:78.2%'></span></td><td class='mejor'><span class='v'>12.50</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4H-0.1</td><td>H4</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-11.41</span><span class='ic'>[-15.80; -7.03]</span><span class='icbar' style='--l:0.0%;--r:43.4%;--z:78.2%'></span></td><td><span class='v'>7.93</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>H4O-0.1</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>-2.25</span><span class='ic'>[-4.91; 0.41]</span><span class='icbar' style='--l:53.9%;--r:80.2%;--z:78.2%'></span></td><td><span class='v'>5.29</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4O-0.05</td><td>H4</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-6.14</span><span class='ic'>[-10.53; -1.75]</span><span class='icbar' style='--l:26.1%;--r:69.6%;--z:78.2%'></span></td><td><span class='v'>4.78</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>H4F-0.25</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>1.26</span><span class='ic'>[-1.42; 3.94]</span><span class='icbar' style='--l:71.2%;--r:97.7%;--z:78.2%'></span></td><td><span class='v'>4.77</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4P-0.1</td><td>H4</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-5.37</span><span class='ic'>[-9.81; -0.93]</span><span class='icbar' style='--l:29.7%;--r:73.6%;--z:78.2%'></span></td><td><span class='v'>4.51</span></td><td><span class='pill ind'>indeterminado</span></td></tr><tr><td>H4P-0.05</td><td>H4</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-6.47</span><span class='ic'>[-10.11; -2.83]</span><span class='icbar' style='--l:28.2%;--r:64.2%;--z:78.2%'></span></td><td><span class='v'>3.93</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>H4O-0.25</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>-0.30</span><span class='ic'>[-2.97; 2.38]</span><span class='icbar' style='--l:63.5%;--r:90.0%;--z:78.2%'></span></td><td><span class='v'>3.65</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4U-0.1</td><td>H4</td><td><span class='v'>8</span></td><td class='sig-neg'><span class='v'>-8.02</span><span class='ic'>[-11.52; -4.53]</span><span class='icbar' style='--l:21.2%;--r:55.8%;--z:78.2%'></span></td><td><span class='v'>3.41</span></td><td><span class='pill pierde'>pierde</span></td></tr><tr><td>H4P-0.25</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>-1.33</span><span class='ic'>[-4.46; 1.81]</span><span class='icbar' style='--l:56.1%;--r:87.2%;--z:78.2%'></span></td><td><span class='v'>3.35</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4O-0.5</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>-1.33</span><span class='ic'>[-4.27; 1.60]</span><span class='icbar' style='--l:57.1%;--r:86.1%;--z:78.2%'></span></td><td><span class='v'>2.31</span></td><td><span class='pill ok'>no pierde</span></td></tr><tr><td>H4P-0.5</td><td>H4</td><td><span class='v'>8</span></td><td><span class='v'>-2.55</span><span class='ic'>[-5.82; 0.72]</span><span class='icbar' style='--l:49.4%;--r:81.8%;--z:78.2%'></span></td><td><span class='v'>2.20</span></td><td><span class='pill ind'>indeterminado</span></td></tr></table>

<details markdown="1">
<summary>Detalle del bloque A</summary>

<table><tr><th>variante</th><th>Ḡ (M$)</th><th>Δ réplica 0 [IC] (M$)</th><th>Δ con réplicas [IC] (M$)</th><th>ΔAUC en 201910 [IC]</th><th>T mediana (s)</th><th>tiempo igual, réplicas [IC t] (M$)</th><th>tiempo igual, bootstrap de clientes [IC] (M$)</th></tr><tr><td>U0.05</td><td>254.04</td><td class='sig-neg'><span class='v'>-30.14</span><span class='ic'>[-34.56; -25.72]</span><span class='icbar' style='--l:0.0%;--r:21.0%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-27.74</span><span class='ic'>[-30.35; -25.13]</span><span class='icbar' style='--l:0.0%;--r:14.5%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0166</span><span class='ic'>[-0.0184; -0.0149]</span><span class='icbar' style='--l:0.0%;--r:17.4%;--z:91.9%'></span></td><td>63</td><td class='sig-neg'><span class='v'>-8.70</span><span class='ic'>[-13.09; -4.32]</span><span class='icbar' style='--l:0.0%;--r:37.4%;--z:55.8%'></span></td><td class='sig-neg'><span class='v'>-13.72</span><span class='ic'>[-26.90; -0.92]</span><span class='icbar' style='--l:0.0%;--r:57.8%;--z:59.9%'></span></td></tr><tr><td>U0.1</td><td>264.31</td><td class='sig-neg'><span class='v'>-16.28</span><span class='ic'>[-19.83; -12.73]</span><span class='icbar' style='--l:35.0%;--r:51.9%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-17.47</span><span class='ic'>[-20.23; -14.71]</span><span class='icbar' style='--l:28.1%;--r:43.4%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0108</span><span class='ic'>[-0.0123; -0.0094]</span><span class='icbar' style='--l:30.5%;--r:44.8%;--z:91.9%'></span></td><td>99</td><td><span class='v'>-4.58</span><span class='ic'>[-9.22; 0.06]</span><span class='icbar' style='--l:16.5%;--r:56.1%;--z:55.8%'></span></td><td><span class='v'>-5.82</span><span class='ic'>[-15.73; 3.85]</span><span class='icbar' style='--l:24.9%;--r:68.4%;--z:59.9%'></span></td></tr><tr><td>U0.25</td><td>273.69</td><td class='sig-neg'><span class='v'>-9.57</span><span class='ic'>[-12.65; -6.49]</span><span class='icbar' style='--l:52.1%;--r:66.7%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-8.09</span><span class='ic'>[-11.58; -4.60]</span><span class='icbar' style='--l:52.1%;--r:71.5%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0054</span><span class='ic'>[-0.0066; -0.0042]</span><span class='icbar' style='--l:58.7%;--r:71.0%;--z:91.9%'></span></td><td>201</td><td><span class='v'>1.33</span><span class='ic'>[-1.60; 4.27]</span><span class='icbar' style='--l:49.0%;--r:74.0%;--z:55.8%'></span></td><td><span class='v'>-0.52</span><span class='ic'>[-8.86; 7.54]</span><span class='icbar' style='--l:40.1%;--r:76.6%;--z:59.9%'></span></td></tr><tr><td>U0.5</td><td>278.13</td><td><span class='v'>-1.38</span><span class='ic'>[-3.99; 1.24]</span><span class='icbar' style='--l:72.7%;--r:85.1%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-3.64</span><span class='ic'>[-6.58; -0.71]</span><span class='icbar' style='--l:66.0%;--r:82.3%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0018</span><span class='ic'>[-0.0029; -0.0007]</span><span class='icbar' style='--l:77.5%;--r:88.3%;--z:91.9%'></span></td><td>423</td><td class='sig-pos'><span class='v'>3.67</span><span class='ic'>[0.64; 6.71]</span><span class='icbar' style='--l:58.5%;--r:84.4%;--z:55.8%'></span></td><td><span class='v'>5.98</span><span class='ic'>[-1.71; 13.53]</span><span class='icbar' style='--l:56.1%;--r:90.0%;--z:59.9%'></span></td></tr><tr><td>B0.05</td><td>267.23</td><td class='sig-neg'><span class='v'>-16.34</span><span class='ic'>[-19.86; -12.81]</span><span class='icbar' style='--l:35.0%;--r:51.7%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-14.55</span><span class='ic'>[-17.44; -11.66]</span><span class='icbar' style='--l:35.8%;--r:51.9%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0109</span><span class='ic'>[-0.0124; -0.0093]</span><span class='icbar' style='--l:29.7%;--r:45.4%;--z:91.9%'></span></td><td>324</td><td class='sig-neg'><span class='v'>-8.57</span><span class='ic'>[-11.78; -5.35]</span><span class='icbar' style='--l:5.6%;--r:33.0%;--z:55.8%'></span></td><td><span class='v'>-4.49</span><span class='ic'>[-14.85; 6.55]</span><span class='icbar' style='--l:26.8%;--r:74.4%;--z:59.9%'></span></td></tr><tr><td>B0.1</td><td>274.47</td><td class='sig-neg'><span class='v'>-8.47</span><span class='ic'>[-11.02; -5.92]</span><span class='icbar' style='--l:56.0%;--r:68.1%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-7.31</span><span class='ic'>[-9.76; -4.86]</span><span class='icbar' style='--l:57.2%;--r:70.8%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0068</span><span class='ic'>[-0.0079; -0.0056]</span><span class='icbar' style='--l:52.4%;--r:63.8%;--z:91.9%'></span></td><td>338</td><td><span class='v'>-2.38</span><span class='ic'>[-5.13; 0.37]</span><span class='icbar' style='--l:33.9%;--r:57.4%;--z:55.8%'></span></td><td><span class='v'>-2.34</span><span class='ic'>[-11.66; 6.44]</span><span class='icbar' style='--l:33.9%;--r:74.2%;--z:59.9%'></span></td></tr><tr><td>B0.25</td><td>279.58</td><td><span class='v'>0.88</span><span class='ic'>[-1.95; 3.71]</span><span class='icbar' style='--l:77.6%;--r:91.0%;--z:82.2%'></span></td><td><span class='v'>-2.20</span><span class='ic'>[-4.95; 0.55]</span><span class='icbar' style='--l:70.5%;--r:85.8%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0026</span><span class='ic'>[-0.0038; -0.0015]</span><span class='icbar' style='--l:73.0%;--r:84.6%;--z:91.9%'></span></td><td>601</td><td><span class='v'>3.12</span><span class='ic'>[-0.09; 6.33]</span><span class='icbar' style='--l:55.4%;--r:82.8%;--z:55.8%'></span></td><td><span class='v'>3.72</span><span class='ic'>[-6.00; 13.31]</span><span class='icbar' style='--l:46.5%;--r:89.5%;--z:59.9%'></span></td></tr><tr><td>GOSS</td><td>278.82</td><td class='sig-neg'><span class='v'>-4.01</span><span class='ic'>[-7.03; -1.00]</span><span class='icbar' style='--l:65.5%;--r:79.8%;--z:82.2%'></span></td><td><span class='v'>-2.96</span><span class='ic'>[-6.13; 0.21]</span><span class='icbar' style='--l:67.2%;--r:84.8%;--z:84.3%'></span></td><td><span class='v'>+0.0003</span><span class='ic'>[-0.0008; +0.0014]</span><span class='icbar' style='--l:87.9%;--r:98.9%;--z:91.9%'></span></td><td>790</td><td><span class='v'>1.58<sup>c</sup></span><span class='ic'>[-1.83; 4.99]</span><span class='icbar' style='--l:48.0%;--r:77.0%;--z:55.8%'></span></td><td><span class='v'>—<sup>b</sup></span></td></tr><tr><td>B0.5</td><td>282.13</td><td><span class='v'>-0.94</span><span class='ic'>[-3.62; 1.75]</span><span class='icbar' style='--l:73.6%;--r:86.4%;--z:82.2%'></span></td><td><span class='v'>0.35</span><span class='ic'>[-2.16; 2.86]</span><span class='icbar' style='--l:78.3%;--r:92.2%;--z:84.3%'></span></td><td><span class='v'>-0.0005</span><span class='ic'>[-0.0015; +0.0004]</span><span class='icbar' style='--l:84.4%;--r:94.1%;--z:91.9%'></span></td><td>849</td><td class='sig-pos'><span class='v'>5.05<sup>c</sup></span><span class='ic'>[0.65; 9.45]</span><span class='icbar' style='--l:58.6%;--r:96.1%;--z:55.8%'></span></td><td><span class='v'>—<sup>b</sup></span></td></tr><tr><td>H3-0.05</td><td>283.86</td><td class='sig-pos'><span class='v'>5.22</span><span class='ic'>[2.96; 7.49]</span><span class='icbar' style='--l:89.2%;--r:100.0%;--z:82.2%'></span></td><td><span class='v'>2.08</span><span class='ic'>[-0.87; 5.02]</span><span class='icbar' style='--l:81.9%;--r:98.2%;--z:84.3%'></span></td><td><span class='v'>-0.0020</span><span class='ic'>[-0.0041; +0.0000]</span><span class='icbar' style='--l:71.6%;--r:92.0%;--z:91.9%'></span></td><td>95</td><td class='sig-pos'><span class='v'>4.77</span><span class='ic'>[1.01; 8.53]</span><span class='icbar' style='--l:60.1%;--r:92.2%;--z:55.8%'></span></td><td class='sig-pos'><span class='v'>7.74</span><span class='ic'>[0.06; 16.23]</span><span class='icbar' style='--l:60.0%;--r:96.0%;--z:59.9%'></span></td></tr><tr><td>H3K-0.1</td><td>281.57</td><td><span class='v'>0.44</span><span class='ic'>[-1.91; 2.79]</span><span class='icbar' style='--l:77.7%;--r:88.8%;--z:82.2%'></span></td><td><span class='v'>-0.21</span><span class='ic'>[-5.05; 4.63]</span><span class='icbar' style='--l:70.2%;--r:97.1%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0033</span><span class='ic'>[-0.0050; -0.0017]</span><span class='icbar' style='--l:67.1%;--r:83.5%;--z:91.9%'></span></td><td>126</td><td><span class='v'>3.95</span><span class='ic'>[-1.58; 9.47]</span><span class='icbar' style='--l:49.1%;--r:96.2%;--z:55.8%'></span></td><td><span class='v'>4.24</span><span class='ic'>[-6.33; 15.40]</span><span class='icbar' style='--l:45.8%;--r:94.1%;--z:59.9%'></span></td></tr><tr><td>H3-0.1</td><td>283.49</td><td><span class='v'>1.26</span><span class='ic'>[-1.95; 4.48]</span><span class='icbar' style='--l:77.5%;--r:92.9%;--z:82.2%'></span></td><td><span class='v'>1.71</span><span class='ic'>[-1.07; 4.49]</span><span class='icbar' style='--l:81.3%;--r:96.7%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0017</span><span class='ic'>[-0.0030; -0.0003]</span><span class='icbar' style='--l:76.8%;--r:90.3%;--z:91.9%'></span></td><td>129</td><td class='sig-pos'><span class='v'>5.46</span><span class='ic'>[2.93; 7.98]</span><span class='icbar' style='--l:68.3%;--r:89.8%;--z:55.8%'></span></td><td><span class='v'>6.04</span><span class='ic'>[-2.37; 15.30]</span><span class='icbar' style='--l:54.6%;--r:93.9%;--z:59.9%'></span></td></tr><tr><td>H3L-0.1</td><td>281.92</td><td><span class='v'>-1.43</span><span class='ic'>[-4.02; 1.16]</span><span class='icbar' style='--l:72.6%;--r:84.9%;--z:82.2%'></span></td><td><span class='v'>0.14</span><span class='ic'>[-3.30; 3.57]</span><span class='icbar' style='--l:75.1%;--r:94.2%;--z:84.3%'></span></td><td><span class='v'>-0.0005</span><span class='ic'>[-0.0020; +0.0010]</span><span class='icbar' style='--l:81.9%;--r:96.9%;--z:91.9%'></span></td><td>130</td><td class='sig-pos'><span class='v'>2.98</span><span class='ic'>[0.05; 5.92]</span><span class='icbar' style='--l:56.0%;--r:81.0%;--z:55.8%'></span></td><td><span class='v'>1.76</span><span class='ic'>[-7.26; 10.72]</span><span class='icbar' style='--l:43.7%;--r:83.7%;--z:59.9%'></span></td></tr><tr><td>H3R-0.1</td><td>283.37</td><td><span class='v'>0.82</span><span class='ic'>[-1.79; 3.44]</span><span class='icbar' style='--l:77.9%;--r:90.4%;--z:82.2%'></span></td><td><span class='v'>1.59</span><span class='ic'>[-1.80; 4.98]</span><span class='icbar' style='--l:79.3%;--r:98.1%;--z:84.3%'></span></td><td><span class='v'>-0.0008</span><span class='ic'>[-0.0023; +0.0006]</span><span class='icbar' style='--l:80.5%;--r:94.9%;--z:91.9%'></span></td><td>130</td><td class='sig-pos'><span class='v'>5.87</span><span class='ic'>[4.27; 7.47]</span><span class='icbar' style='--l:74.0%;--r:87.7%;--z:55.8%'></span></td><td><span class='v'>5.06</span><span class='ic'>[-2.15; 13.31]</span><span class='icbar' style='--l:55.1%;--r:89.5%;--z:59.9%'></span></td></tr><tr><td>H3L-0.25</td><td>283.00</td><td><span class='v'>1.32</span><span class='ic'>[-1.36; 4.00]</span><span class='icbar' style='--l:79.0%;--r:91.7%;--z:82.2%'></span></td><td><span class='v'>1.22</span><span class='ic'>[-1.59; 4.03]</span><span class='icbar' style='--l:79.8%;--r:95.5%;--z:84.3%'></span></td><td><span class='v'>+0.0004</span><span class='ic'>[-0.0008; +0.0016]</span><span class='icbar' style='--l:87.9%;--r:100.0%;--z:91.9%'></span></td><td>222</td><td class='sig-pos'><span class='v'>5.46</span><span class='ic'>[0.83; 10.08]</span><span class='icbar' style='--l:59.3%;--r:98.8%;--z:55.8%'></span></td><td class='sig-pos'><span class='v'>9.00</span><span class='ic'>[2.14; 16.83]</span><span class='icbar' style='--l:64.6%;--r:97.3%;--z:59.9%'></span></td></tr><tr><td>H3R-0.25</td><td>283.72</td><td><span class='v'>2.04</span><span class='ic'>[-0.81; 4.88]</span><span class='icbar' style='--l:80.3%;--r:93.8%;--z:82.2%'></span></td><td><span class='v'>1.95</span><span class='ic'>[-0.85; 4.74]</span><span class='icbar' style='--l:81.9%;--r:97.4%;--z:84.3%'></span></td><td><span class='v'>+0.0000</span><span class='ic'>[-0.0011; +0.0011]</span><span class='icbar' style='--l:86.3%;--r:97.5%;--z:91.9%'></span></td><td>225</td><td class='sig-pos'><span class='v'>5.32</span><span class='ic'>[2.93; 7.71]</span><span class='icbar' style='--l:68.3%;--r:88.7%;--z:55.8%'></span></td><td><span class='v'>6.65</span><span class='ic'>[-0.28; 14.19]</span><span class='icbar' style='--l:59.2%;--r:91.4%;--z:59.9%'></span></td></tr><tr><td>H3-0.25</td><td>283.20</td><td class='sig-pos'><span class='v'>4.73</span><span class='ic'>[2.48; 6.98]</span><span class='icbar' style='--l:88.1%;--r:98.8%;--z:82.2%'></span></td><td><span class='v'>1.42</span><span class='ic'>[-2.82; 5.67]</span><span class='icbar' style='--l:76.4%;--r:100.0%;--z:84.3%'></span></td><td><span class='v'>-0.0009</span><span class='ic'>[-0.0021; +0.0004]</span><span class='icbar' style='--l:81.3%;--r:93.9%;--z:91.9%'></span></td><td>229</td><td class='sig-pos'><span class='v'>6.15</span><span class='ic'>[3.95; 8.34]</span><span class='icbar' style='--l:72.6%;--r:91.4%;--z:55.8%'></span></td><td class='sig-pos'><span class='v'>8.85</span><span class='ic'>[1.87; 16.83]</span><span class='icbar' style='--l:64.0%;--r:97.3%;--z:59.9%'></span></td></tr><tr><td>H3-0.5</td><td>281.70</td><td><span class='v'>-0.88</span><span class='ic'>[-3.79; 2.03]</span><span class='icbar' style='--l:73.2%;--r:87.0%;--z:82.2%'></span></td><td><span class='v'>-0.08</span><span class='ic'>[-3.17; 3.00]</span><span class='icbar' style='--l:75.5%;--r:92.6%;--z:84.3%'></span></td><td><span class='v'>-0.0000</span><span class='ic'>[-0.0010; +0.0010]</span><span class='icbar' style='--l:86.7%;--r:97.1%;--z:91.9%'></span></td><td>440</td><td><span class='v'>2.98</span><span class='ic'>[-0.53; 6.49]</span><span class='icbar' style='--l:53.5%;--r:83.5%;--z:55.8%'></span></td><td><span class='v'>3.82</span><span class='ic'>[-4.51; 12.33]</span><span class='icbar' style='--l:49.8%;--r:87.3%;--z:59.9%'></span></td></tr><tr><td>H4F-0.05</td><td>283.19</td><td class='sig-pos'><span class='v'>4.18</span><span class='ic'>[1.11; 7.25]</span><span class='icbar' style='--l:84.8%;--r:99.4%;--z:82.2%'></span></td><td><span class='v'>1.41</span><span class='ic'>[-1.58; 4.40]</span><span class='icbar' style='--l:79.9%;--r:96.5%;--z:84.3%'></span></td><td><span class='v'>-0.0019</span><span class='ic'>[-0.0041; +0.0003]</span><span class='icbar' style='--l:71.6%;--r:93.4%;--z:91.9%'></span></td><td>80</td><td class='sig-pos'><span class='v'>4.63</span><span class='ic'>[0.77; 8.50]</span><span class='icbar' style='--l:59.1%;--r:92.0%;--z:55.8%'></span></td><td class='sig-pos'><span class='v'>9.29</span><span class='ic'>[1.53; 18.04]</span><span class='icbar' style='--l:63.3%;--r:100.0%;--z:59.9%'></span></td></tr><tr><td>H4H-0.1</td><td>270.37</td><td class='sig-neg'><span class='v'>-9.19</span><span class='ic'>[-12.06; -6.31]</span><span class='icbar' style='--l:53.5%;--r:67.2%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-11.41</span><span class='ic'>[-15.80; -7.03]</span><span class='icbar' style='--l:40.4%;--r:64.7%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0045</span><span class='ic'>[-0.0062; -0.0028]</span><span class='icbar' style='--l:61.0%;--r:77.8%;--z:91.9%'></span></td><td>126</td><td class='sig-neg'><span class='v'>-5.68</span><span class='ic'>[-10.71; -0.65]</span><span class='icbar' style='--l:10.1%;--r:53.0%;--z:55.8%'></span></td><td><span class='v'>-8.72</span><span class='ic'>[-17.99; 0.44]</span><span class='icbar' style='--l:19.8%;--r:60.8%;--z:59.9%'></span></td></tr><tr><td>H4O-0.1</td><td>279.53</td><td><span class='v'>-2.92</span><span class='ic'>[-6.48; 0.65]</span><span class='icbar' style='--l:66.8%;--r:83.7%;--z:82.2%'></span></td><td><span class='v'>-2.25</span><span class='ic'>[-4.91; 0.41]</span><span class='icbar' style='--l:70.6%;--r:85.4%;--z:84.3%'></span></td><td><span class='v'>-0.0003</span><span class='ic'>[-0.0014; +0.0009]</span><span class='icbar' style='--l:85.0%;--r:96.2%;--z:91.9%'></span></td><td>189</td><td class='sig-pos'><span class='v'>6.56</span><span class='ic'>[3.65; 9.46]</span><span class='icbar' style='--l:71.4%;--r:96.1%;--z:55.8%'></span></td><td><span class='v'>2.17</span><span class='ic'>[-7.92; 13.04]</span><span class='icbar' style='--l:42.2%;--r:88.9%;--z:59.9%'></span></td></tr><tr><td>H4O-0.05</td><td>275.64</td><td><span class='v'>-2.48</span><span class='ic'>[-5.36; 0.41]</span><span class='icbar' style='--l:69.4%;--r:83.2%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-6.14</span><span class='ic'>[-10.53; -1.75]</span><span class='icbar' style='--l:55.0%;--r:79.4%;--z:84.3%'></span></td><td><span class='v'>-0.0009</span><span class='ic'>[-0.0024; +0.0006]</span><span class='icbar' style='--l:79.7%;--r:94.8%;--z:91.9%'></span></td><td>210</td><td class='sig-pos'><span class='v'>5.60</span><span class='ic'>[2.69; 8.50]</span><span class='icbar' style='--l:67.3%;--r:92.0%;--z:55.8%'></span></td><td><span class='v'>6.06</span><span class='ic'>[-3.09; 16.12]</span><span class='icbar' style='--l:53.0%;--r:95.7%;--z:59.9%'></span></td></tr><tr><td>H4F-0.25</td><td>283.04</td><td><span class='v'>1.04</span><span class='ic'>[-2.02; 4.11]</span><span class='icbar' style='--l:77.4%;--r:92.0%;--z:82.2%'></span></td><td><span class='v'>1.26</span><span class='ic'>[-1.42; 3.94]</span><span class='icbar' style='--l:80.3%;--r:95.2%;--z:84.3%'></span></td><td><span class='v'>-0.0002</span><span class='ic'>[-0.0013; +0.0009]</span><span class='icbar' style='--l:85.3%;--r:96.6%;--z:91.9%'></span></td><td>210</td><td class='sig-pos'><span class='v'>4.91</span><span class='ic'>[2.09; 7.73]</span><span class='icbar' style='--l:64.7%;--r:88.7%;--z:55.8%'></span></td><td><span class='v'>2.39</span><span class='ic'>[-4.62; 10.01]</span><span class='icbar' style='--l:49.6%;--r:82.1%;--z:59.9%'></span></td></tr><tr><td>H4P-0.1</td><td>276.41</td><td class='sig-neg'><span class='v'>-6.21</span><span class='ic'>[-8.86; -3.57]</span><span class='icbar' style='--l:61.1%;--r:73.7%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-5.37</span><span class='ic'>[-9.81; -0.93]</span><span class='icbar' style='--l:57.0%;--r:81.7%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0035</span><span class='ic'>[-0.0053; -0.0016]</span><span class='icbar' style='--l:65.4%;--r:83.8%;--z:91.9%'></span></td><td>222</td><td class='sig-pos'><span class='v'>4.91</span><span class='ic'>[1.57; 8.24]</span><span class='icbar' style='--l:62.5%;--r:90.9%;--z:55.8%'></span></td><td><span class='v'>0.98</span><span class='ic'>[-9.79; 11.66]</span><span class='icbar' style='--l:38.1%;--r:85.8%;--z:59.9%'></span></td></tr><tr><td>H4P-0.05</td><td>275.31</td><td><span class='v'>-3.19</span><span class='ic'>[-6.49; 0.11]</span><span class='icbar' style='--l:66.8%;--r:82.4%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-6.47</span><span class='ic'>[-10.11; -2.83]</span><span class='icbar' style='--l:56.2%;--r:76.4%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0034</span><span class='ic'>[-0.0045; -0.0024]</span><span class='icbar' style='--l:69.6%;--r:79.7%;--z:91.9%'></span></td><td>255</td><td class='sig-pos'><span class='v'>5.46</span><span class='ic'>[0.55; 10.37]</span><span class='icbar' style='--l:58.1%;--r:100.0%;--z:55.8%'></span></td><td><span class='v'>0.72</span><span class='ic'>[-11.16; 12.54]</span><span class='icbar' style='--l:35.0%;--r:87.8%;--z:59.9%'></span></td></tr><tr><td>H4O-0.25</td><td>281.48</td><td><span class='v'>-2.81</span><span class='ic'>[-6.37; 0.76]</span><span class='icbar' style='--l:67.0%;--r:84.0%;--z:82.2%'></span></td><td><span class='v'>-0.30</span><span class='ic'>[-2.97; 2.38]</span><span class='icbar' style='--l:76.0%;--r:90.9%;--z:84.3%'></span></td><td><span class='v'>-0.0000</span><span class='ic'>[-0.0011; +0.0011]</span><span class='icbar' style='--l:86.4%;--r:97.2%;--z:91.9%'></span></td><td>274</td><td class='sig-pos'><span class='v'>4.36</span><span class='ic'>[0.54; 8.17]</span><span class='icbar' style='--l:58.1%;--r:90.6%;--z:55.8%'></span></td><td><span class='v'>1.36</span><span class='ic'>[-6.88; 9.85]</span><span class='icbar' style='--l:44.6%;--r:81.8%;--z:59.9%'></span></td></tr><tr><td>H4U-0.1</td><td>273.76</td><td class='sig-neg'><span class='v'>-7.70</span><span class='ic'>[-10.81; -4.59]</span><span class='icbar' style='--l:56.5%;--r:71.3%;--z:82.2%'></span></td><td class='sig-neg'><span class='v'>-8.02</span><span class='ic'>[-11.52; -4.53]</span><span class='icbar' style='--l:52.3%;--r:71.7%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0037</span><span class='ic'>[-0.0054; -0.0021]</span><span class='icbar' style='--l:64.8%;--r:81.6%;--z:91.9%'></span></td><td>293</td><td><span class='v'>3.95</span><span class='ic'>[-1.40; 9.29]</span><span class='icbar' style='--l:49.8%;--r:95.4%;--z:55.8%'></span></td><td><span class='v'>2.91</span><span class='ic'>[-7.54; 14.25]</span><span class='icbar' style='--l:43.1%;--r:91.6%;--z:59.9%'></span></td></tr><tr><td>H4P-0.25</td><td>280.45</td><td class='sig-neg'><span class='v'>-3.52</span><span class='ic'>[-6.13; -0.91]</span><span class='icbar' style='--l:67.6%;--r:80.0%;--z:82.2%'></span></td><td><span class='v'>-1.33</span><span class='ic'>[-4.46; 1.81]</span><span class='icbar' style='--l:71.9%;--r:89.3%;--z:84.3%'></span></td><td class='sig-neg'><span class='v'>-0.0021</span><span class='ic'>[-0.0036; -0.0006]</span><span class='icbar' style='--l:74.1%;--r:88.8%;--z:91.9%'></span></td><td>299</td><td class='sig-pos'><span class='v'>6.01</span><span class='ic'>[2.88; 9.14]</span><span class='icbar' style='--l:68.1%;--r:94.8%;--z:55.8%'></span></td><td><span class='v'>5.76</span><span class='ic'>[-3.08; 14.75]</span><span class='icbar' style='--l:53.0%;--r:92.7%;--z:59.9%'></span></td></tr><tr><td>H4O-0.5</td><td>280.44</td><td><span class='v'>-0.71</span><span class='ic'>[-3.83; 2.40]</span><span class='icbar' style='--l:73.1%;--r:87.9%;--z:82.2%'></span></td><td><span class='v'>-1.33</span><span class='ic'>[-4.27; 1.60]</span><span class='icbar' style='--l:72.4%;--r:88.7%;--z:84.3%'></span></td><td><span class='v'>+0.0004</span><span class='ic'>[-0.0007; +0.0015]</span><span class='icbar' style='--l:88.2%;--r:99.6%;--z:91.9%'></span></td><td>434</td><td class='sig-pos'><span class='v'>4.08</span><span class='ic'>[0.49; 7.67]</span><span class='icbar' style='--l:57.9%;--r:88.5%;--z:55.8%'></span></td><td><span class='v'>4.34</span><span class='ic'>[-3.79; 12.60]</span><span class='icbar' style='--l:51.4%;--r:87.9%;--z:59.9%'></span></td></tr><tr><td>H4P-0.5</td><td>279.23</td><td><span class='v'>-1.10</span><span class='ic'>[-3.63; 1.43]</span><span class='icbar' style='--l:73.6%;--r:85.6%;--z:82.2%'></span></td><td><span class='v'>-2.55</span><span class='ic'>[-5.82; 0.72]</span><span class='icbar' style='--l:68.1%;--r:86.3%;--z:84.3%'></span></td><td><span class='v'>-0.0008</span><span class='ic'>[-0.0022; +0.0007]</span><span class='icbar' style='--l:80.8%;--r:95.3%;--z:91.9%'></span></td><td>455</td><td><span class='v'>3.26</span><span class='ic'>[-0.49; 7.01]</span><span class='icbar' style='--l:53.7%;--r:85.7%;--z:55.8%'></span></td><td><span class='v'>2.73</span><span class='ic'>[-6.00; 11.88]</span><span class='icbar' style='--l:46.5%;--r:86.3%;--z:59.9%'></span></td></tr></table><p class='nota'><sup>b</sup> no aplica: K &lt; 2, en el tiempo del control no entra un segundo modelo final de la variante.</p><p class='nota'><sup>c</sup> con menos réplicas que Δ: en alguna réplica K &lt; 2.</p>

</details>

<!-- /generado:bloque-a -->

- **H1, ninguna de las dos** ([H1](../h1/README.md)): `U0.5` *no pierde* y `U0.25` ya *pierde*; la frontera observada es
  r = 0,5. La pérdida crece a medida que baja r.
- **H2, refutada** ([H2](../h2/README.md)): con f = 0,1 pierde y con 0,5 y 0,25 casi no acelera (aceleración ≤ 1,23). GOSS es
  descriptiva y queda *indeterminado*.
- **H3, confirmada también con réplicas** ([H3](../h3/README.md)): `H3-0.1` y `H3-0.25` no pierden con réplicas (cotas
  inferiores −1,07 y −2,82 M$, contra −δ = −5,65 M$) y aceleran 7,76 y 4,38 veces. La réplica 0 sola movía Δ en los dos
  sentidos: de 4,73 a 1,42 M$ con réplicas en `H3-0.25`, de 1,26 a 1,71 M$ en `H3-0.1`. El mecanismo (la muestra
  regulariza o el control tuvo mala suerte) queda sin resolver. `H3-0.05` también se confirma (aceleración 10,56) y reescalar
  `min_data_in_leaf` no cambia.
- **Extensiones de H3** (secundarias): las cuatro no pierden contra el control. La raíz no mejora a no reescalar; le
  gana a la lineal en r = 0,1 y no en r = 0,25; buscar sobre el 10 % de los clientes no cambia contra el 10 % de las
  filas.
- **H4, búsqueda informada: refutada** ([H4](../h4/README.md)). `H4H-0.1` y `H4U-0.1` *pierden* con réplicas (−11,41 y
  −8,02 M$, con los IC enteros debajo de −δ). Elegir negativos difíciles en vez de uniformes no cambia.
- **H4, fast-retrain: confirmada en las dos tasas.** `H4F-0.05` no pierde, acelera 12,50 veces (más que `H3-0.05`,
  10,56) y a tiempo igual *gana*. `H4F-0.25` también cumple las tres condiciones.
- **`H4O-0.5`, reoptimizar sobre el set del final** (respuesta a Zulip 211718): no pierde contra el control y no cambia
  contra `H4F-0.05`, con aceleración 2,31 contra 12,50. Seguir el «siempre OP» en fast-retrain cuesta más de 5 veces el tiempo y
  no suma ganancia medible.
- `U0.25` y `H3-0.25` comparten el estudio de Optuna de la réplica 0, o sea los mismos hiperparámetros. `U0.25` pierde y
  `H3-0.25` no, así que en H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una
  muestra.
- **Vale la pena** (no pierde y aceleración ≥ 2): las ocho variantes de H3, las de fast-retrain (`H4F-0.05`,
  `H4F-0.25` y `H4O-0.5`) y, en esta ronda, `U0.5` (aceleración 2,25). Ninguna de H2 (las que no pierden, `B0.25` y
  `B0.5`, aceleran menos de 2 veces) ni de la búsqueda informada de H4, que pierde.

## ¿Cuánto se puede achicar?

Depende de qué se achique. Si es solo la búsqueda (H3), hasta el 5 % de las filas no pierde. Si es también el final al
azar (H1), la pérdida crece a medida que baja la fracción y la frontera observada es r = 0,5.

<!-- generado:fraccion -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![Δ contra la fracción de muestra: el punto más bajo es U0.05 (-27.7 M$), por debajo de −δ (punteada)](figuras/fraccion.svg)

<!-- /generado:fraccion -->

## ¿Qué se hace con el tiempo ahorrado?

Cada variante gasta el tiempo que le sobra respecto del control en un ensamble de K semillas finales, K = ⌊(T(C) −
T_opt) / T_final⌋ acotado a las semillas que hay, y se mide la ganancia en 201910 al corte N\* del promedio de sus
probabilidades. Con réplicas, el IC es t entre réplicas; el bootstrap de clientes de 201910 mide el ruido del mes de test.

<!-- generado:ensamble -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![Con el tiempo del control (797 s), H4P-0.25 ensambla hasta 296.4 M$; el control con sus 20 semillas llega a 286.6 M$](figuras/ensamble.svg)



![G del ensamble según K: el control con sus 20 semillas llega a 286.6 M$](figuras/ensamble_k.svg)

<!-- /generado:ensamble -->

<!-- generado:tiempo-igual -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

<p>Se le da a cada variante el tiempo del control: después de su optimización, el sobrante se gasta en K modelos finales con semillas distintas, K = ⌊(T(C) − T_opt) / T_final⌋, acotado a las 20 semillas que hay. T_final es la media de <code>tiempo_entrenamiento_s</code> de la variante y T_opt = T − T_final. Para K ≥ 2 se promedia fila a fila <code>prob</code> de las primeras K semillas (en el orden de <code>semillas_pedidas</code>) y se mide la ganancia en 201910 al corte N*. Se compara con Ḡ_C (un modelo del control, media de sus 10 semillas) y, como referencia, con el ensamble de las 20 semillas del control.</p><p>Ḡ_C = 282.48 M$; ensamble de 20 semillas del control = 286.55 M$.</p>

=== "H1"

    <table><tr><th>variante</th><th>T_opt (s)</th><th>T_final (s)</th><th>K</th><th>G del ensamble en 201910 (M$)</th><th>G − Ḡ_C (M$)</th><th>G − ensamble 20 de C (M$)</th></tr><tr><td>U0.5</td><td>328</td><td>25.9</td><td>18</td><td>288.75</td><td>6.27</td><td>2.20</td></tr><tr><td>U0.25</td><td>153</td><td>10.3</td><td>62 (se usan 20)</td><td>281.05</td><td>-1.43</td><td>-5.50</td></tr><tr><td>U0.1</td><td>77</td><td>3.7</td><td>194 (se usan 20)</td><td>276.65</td><td>-5.83</td><td>-9.90</td></tr><tr><td>U0.05</td><td>67</td><td>2.7</td><td>273 (se usan 20)</td><td>267.85</td><td>-14.63</td><td>-18.70</td></tr></table>

=== "H2"

    <table><tr><th>variante</th><th>T_opt (s)</th><th>T_final (s)</th><th>K</th><th>G del ensamble en 201910 (M$)</th><th>G − Ḡ_C (M$)</th><th>G − ensamble 20 de C (M$)</th></tr><tr><td>B0.5</td><td>973</td><td>37.6</td><td>0</td><td>no aplica (K &lt; 2)</td><td>no aplica (K &lt; 2)</td><td>no aplica (K &lt; 2)</td></tr><tr><td>B0.25</td><td>612</td><td>37.4</td><td>4</td><td>285.45</td><td>2.97</td><td>-1.10</td></tr><tr><td>B0.1</td><td>404</td><td>29.4</td><td>13</td><td>278.85</td><td>-3.63</td><td>-7.70</td></tr><tr><td>B0.05</td><td>318</td><td>23.5</td><td>20</td><td>277.75</td><td>-4.73</td><td>-8.80</td></tr><tr><td>GOSS</td><td>1,059</td><td>43.0</td><td>0</td><td>no aplica (K &lt; 2)</td><td>no aplica (K &lt; 2)</td><td>no aplica (K &lt; 2)</td></tr></table>

=== "H3"

    <table><tr><th>variante</th><th>T_opt (s)</th><th>T_final (s)</th><th>K</th><th>G del ensamble en 201910 (M$)</th><th>G − Ḡ_C (M$)</th><th>G − ensamble 20 de C (M$)</th></tr><tr><td>H3-0.5</td><td>328</td><td>42.1</td><td>11</td><td>287.65</td><td>5.17</td><td>1.10</td></tr><tr><td>H3-0.25</td><td>153</td><td>29.3</td><td>21 (se usan 20)</td><td>292.05</td><td>9.57</td><td>5.50</td></tr><tr><td>H3-0.1</td><td>77</td><td>22.2</td><td>32 (se usan 20)</td><td>288.75</td><td>6.27</td><td>2.20</td></tr><tr><td>H3-0.05</td><td>67</td><td>30.9</td><td>23 (se usan 20)</td><td>289.85</td><td>7.37</td><td>3.30</td></tr><tr><td>H3R-0.1</td><td>77</td><td>24.0</td><td>29 (se usan 20)</td><td>287.65</td><td>5.17</td><td>1.10</td></tr><tr><td>H3R-0.25</td><td>153</td><td>28.7</td><td>22 (se usan 20)</td><td>288.75</td><td>6.27</td><td>2.20</td></tr><tr><td>H3L-0.25</td><td>153</td><td>28.7</td><td>22 (se usan 20)</td><td>292.05</td><td>9.57</td><td>5.50</td></tr><tr><td>H3L-0.1</td><td>77</td><td>23.2</td><td>31 (se usan 20)</td><td>283.25</td><td>0.77</td><td>-3.30</td></tr><tr><td>H3K-0.1</td><td>227</td><td>70.0</td><td>8</td><td>285.45</td><td>2.97</td><td>-1.10</td></tr></table>

=== "H4"

    <table><tr><th>variante</th><th>T_opt (s)</th><th>T_final (s)</th><th>K</th><th>G del ensamble en 201910 (M$)</th><th>G − Ḡ_C (M$)</th><th>G − ensamble 20 de C (M$)</th></tr><tr><td>H4H-0.1</td><td>99</td><td>31.2</td><td>22 (se usan 20)</td><td>274.45</td><td>-8.03</td><td>-12.10</td></tr><tr><td>H4U-0.1</td><td>203</td><td>50.8</td><td>11</td><td>285.45</td><td>2.97</td><td>-1.10</td></tr><tr><td>H4F-0.05</td><td>67</td><td>17.4</td><td>42 (se usan 20)</td><td>292.05</td><td>9.57</td><td>5.50</td></tr><tr><td>H4F-0.25</td><td>153</td><td>17.1</td><td>37 (se usan 20)</td><td>284.35</td><td>1.87</td><td>-2.20</td></tr><tr><td>H4O-0.5</td><td>367</td><td>27.1</td><td>15</td><td>286.55</td><td>4.07</td><td>0.00</td></tr><tr><td>H4O-0.25</td><td>192</td><td>10.7</td><td>56 (se usan 20)</td><td>282.15</td><td>-0.33</td><td>-4.40</td></tr><tr><td>H4O-0.1</td><td>170</td><td>10.8</td><td>58 (se usan 20)</td><td>284.35</td><td>1.87</td><td>-2.20</td></tr><tr><td>H4O-0.05</td><td>240</td><td>12.1</td><td>45 (se usan 20)</td><td>287.65</td><td>5.17</td><td>1.10</td></tr><tr><td>H4P-0.5</td><td>367</td><td>37.9</td><td>11</td><td>284.35</td><td>1.87</td><td>-2.20</td></tr><tr><td>H4P-0.25</td><td>192</td><td>30.3</td><td>19</td><td>287.65</td><td>5.17</td><td>1.10</td></tr><tr><td>H4P-0.1</td><td>170</td><td>46.5</td><td>13</td><td>284.35</td><td>1.87</td><td>-2.20</td></tr><tr><td>H4P-0.05</td><td>240</td><td>85.8</td><td>6</td><td>282.15</td><td>-0.33</td><td>-4.40</td></tr></table>


![A tiempo igual, 18 de 30 variantes superan al control (intervalo entero sobre 0)](figuras/tiempo_igual.svg)

<!-- /generado:tiempo-igual -->

Con réplicas, todas las H3 salvo `H3K-0.1` y las tres de fast-retrain quedan arriba del control; `H4U-0.1` tiene IC que
contiene a 0 aunque pierda con réplicas, porque el ensamble suma ganancia por sí solo, y `H4H-0.1` queda abajo. El
bootstrap de clientes da IC de unos ±8 M$ o más. Con 20 semillas ensamblar el control sí suma, así que la ventaja a
tiempo igual es en buena parte ensamble. Las variantes que pierden a datos iguales no se rescatan ensamblando.

## ¿Qué tan estable es?

<!-- generado:semillas -->
Generado por `comun/reporte.py` el 2026-11-14; no editar.

![Cada punto es una semilla: la dispersión entre semillas llega a 38.5 M$ (B0.05)](figuras/semillas_replicas.svg)

<!-- /generado:semillas -->

**¿Alcanzan más semillas finales?** No, con un solo estudio de Optuna: entre el 24 % (`H3-0.1`) y el 58 % (`H3K-0.1`) de
la varianza de G es suerte de la optimización (25 % en `C`), y esa parte no baja con más semillas finales. Pasar de 10 a
20 semillas angostó el IC por semilla pero no el de réplicas. Las cuentas están en [H3](../h3/README.md); las tablas de
varianza y de diferencias entre variantes, en el [Anexo](anexo.md).

**Entre rondas** (final de cuatro meses contra final de seis; el detalle, con el gráfico y la tabla, en el
[Anexo](anexo.md#rondas)):

- ningún veredicto cambia de lado;
- el IC por semilla se angosta (mediana de la razón de anchos 1,44);
- con réplicas el IC prácticamente no se angosta (0,96), porque la suerte de Optuna no depende de las semillas finales.

**AUC y ganancia.** El veredicto es el de ganancia (Zulip 208135). En H3 y `H4F-0.05` el ΔAUC es negativo o cercano a
0 (`H3L-0.25` y `H3R-0.25`) mientras la ganancia no pierde: en `H3-0.1` la caída de AUC es distinguible de 0 y el Δ de
ganancia no. En GOSS va al revés. El AUC mide el orden de todos los clientes; G, solo los 3.300 de arriba. En H1, `B0.1`
y la búsqueda informada de H4 las dos bajan juntas.

## Limitaciones comunes

Las propias de cada hipótesis están en su página.

- **Hiperparámetros de cuatro meses en un final de seis.** Se usan sin cambios, incluido `min_data_in_leaf`, que es
  absoluto y ahora se aplica sobre más filas. Reescalarlo sería una variante nueva (la idea está en `H3R` y `H3L`).
- **Test ya mirado.** H4 (salvo `H4O-0.5`) y las extensiones de H3 salen de un exploratorio que eligió y descartó
  estrategias mirando su ganancia en 201910, y no hay otro mes de test (la consigna lo reserva para la comparación).
  Entraron todas juntas, con reglas escritas antes de correr, y ninguna se eligió ni se descartó acá por 201910; aun
  así, esos resultados no cuentan con un mes de test que no se haya mirado.
- **Comparaciones múltiples.** Entre H4 y las extensiones de H3 hay más de diez contrastes sin corrección: con un 5 % de
  error por contraste, alguno puede salir significativo por azar. Las conclusiones se apoyan en los contrastes
  principales; el resto es secundario.
- **Réplicas solo en parte de las variantes.** Solo `C`, H3 y H4 tienen réplicas de Optuna. Para `U*`, `B*` y GOSS, Δ
  sigue incluyendo la suerte de una sola optimización; como pierden por mucho o no aceleran, no cambia la respuesta
  (`U0.5`, que vale la pena por poco, es la excepción: su veredicto es de una sola búsqueda). Ocho réplicas alcanzan
  para decidir *no pierde*, pero no para separar de 0 una ventaja de 1,42 a 2,08 M$.
- **Evidencia no independiente.** `U0.25`/`H3-0.25` y `U0.1`/`H3-0.1` comparten el estudio de la réplica 0; `H3R`,
  `H3L` y H3 de la misma tasa comparten todos, y `H4F-0.05`/`H4F-0.25` comparten los de `H3-0.05`/`H3-0.25`.
- **Un mes, un año, una máquina.** Un solo año (2019) y un solo mes de test (201910): el bootstrap de clientes muestra
  que el ruido de ese mes es mayor que el de las réplicas. A N\* fijo la ganancia se mueve en pasos de 1,1 M$, así que
  diferencias de uno o dos BAJA+2 no se distinguen del ruido. El corte N\* sale de 201908: si la tasa de bajas de 201910
  es distinta, todas las variantes pagan igual. Los tiempos valen para `n2-highmem-8` (VMs distintas; T es la mediana
  entre réplicas), y en otra máquina solo se trasladan las aceleraciones relativas. `num_iterations = 100` fijo y
  `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática. La réplica del control (`C-rep`)
  se corrió en otra VM de la misma cuenta.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 5 %, 10 % o 25 % de las filas y entrenar con todas las de 201903–201908 no pierde contra el control, también
cuando se mide la suerte de Optuna con 8 réplicas, y es de 4,38 a 10,56 veces más rápido. Entrenar el final con menos
filas al azar pierde desde r = 0,25 (r = 0,5 no pierde y acelera 2,25 veces), y dentro de LightGBM pierde con f = 0,1.
Por qué: la optimización es lo que domina T, y los hiperparámetros que elige Optuna sobre la muestra sirven para el
total.

Lo que las réplicas corrigen es el tamaño de la ventaja: con una sola optimización, H3 puede parecer que le gana al
control o que empata, según la suerte del estudio; con 8 réplicas la diferencia queda entre 1,42 y 2,08 M$ y su IC
contiene a 0. La respuesta práctica no cambia (H3 no pierde y acelera), pero no hay que venderla como una mejora de
ganancia. Para comparar variantes con Optuna, más semillas finales no alcanzan: hay que repetir la optimización.

Con los tres contrastes principales, fijados antes de correr H4:

- **`H3-0.1` contra el control: no pierde** (1,71 M$ [−1,07; 4,49] con réplicas) y acelera 7,76 veces.
- **`H4H-0.1` contra el control: pierde** (−11,41 M$ [−15,80; −7,03]). Achicar la búsqueda conservando todas las bajas y
  recortando CONTINUA rinde peor que achicarla al azar, elijan como se elijan los negativos. La ventaja que reportaba el
  exploratorio no se sostiene al repetir la búsqueda.
- **`H4F-0.05` contra el control: no pierde** (1,41 M$ [−1,58; 4,40]), acelera 12,50 veces y **a tiempo igual gana**
  (4,63 M$ [0,77; 8,50]). Achicar también el final, conservando todas las bajas y la mitad de CONTINUA con peso 2,
  agrega velocidad sin perder; con el tiempo que sobra se ensamblan más semillas. Esta variante viene de una idea vista
  en 201910, y reoptimizarla sobre su propio set (`H4O-0.5`) no la mejora.

Con el final de seis meses y 20 semillas la respuesta es la misma que con cuatro meses y 10.

**La predicción** ([Predicción del experimento](../control/README.md#prediccion-del-experimento-1-nov)):

- **Qué vale la pena: acertó con H3 y falló con H1.** H3 vale la pena con las dos tasas, pero `U0.25` pierde; en H1
  solo vale la pena `U0.5`.
- **A tiempo igual: acertó para las variantes que valen la pena.** Las rápidas que no pierden quedan arriba del control
  ensamblando; las que pierden a datos iguales no se rescatan.
- **Ronda 201903–201908: acertó en las tres reglas** (detalle en el [Anexo](anexo.md#rondas)).

## Qué sigue

- Otro mes de test, para separar el ruido de 201910 del efecto de las variantes y para tener uno que no se haya mirado al
  elegir H4 y las extensiones de H3.
- Fast-retrain sobre otras búsquedas (por ejemplo, `H3-0.1`) y con otras fracciones de CONTINUA, con réplicas desde el
  principio: la suerte de la optimización es del mismo orden que las diferencias entre variantes.

## Exploratorios

Tres estudios con su propio protocolo motivaron las réplicas de Optuna, H4 y las extensiones de H3; sus cifras no se
comparan una a una con las de arriba y están en [Exploratorios](exploratorios/README.md).

## Dependencias

Lee los ledgers de todos los experimentos para la comparación conjunta:

- `control`
- `h1`
- `h2`
- `h3`
- `h4`

Una hipótesis nueva suma su línea acá: es la única que se toca fuera de su carpeta y de `comun/`.
