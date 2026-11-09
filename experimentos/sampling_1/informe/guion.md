# Guion del video — Sampling_1 (10 minutos)

Estructura pedida por Bolaños: hipótesis, diseño, limitaciones, resultados, conclusiones. El baseline no se explica: se
nombra y se sigue. Números de `informe/informe.md` y `informe/tabla_resultados.md`; figuras de `informe/reporte.html` y
`informe/figuras/`.

| tiempo | bloque | quién | qué se dice | en pantalla |
|---|---|---|---|---|
| 0:00–0:45 | Pregunta | Agustina | La pregunta del tutor: ¿vale la pena ganar velocidad perdiendo performance? Nosotros usamos menos filas sin tocar la proporción de clases; Sampling_2 toca la proporción. | título y pregunta |
| 0:45–2:00 | Hipótesis | Agustina | H1: muestrear el train al azar no pierde hasta r = 0,25. H2: muestrear dentro de LightGBM no pierde ni con 0,1. H3: optimizar sobre una muestra y entrenar con todo no pierde. Vale la pena = no pierde y al menos 2× más rápido. Después agregamos réplicas de Optuna para ver si la ventaja de H3 era real o suerte. | las tres hipótesis con su predicción |
| 2:00–3:30 | Diseño | Martín | Diez variantes contra el control, cada una con su Optuna y las mismas 10 semillas. Decide la ganancia en 201910 a 3.300 envíos. Δ apareado por semilla con IC 95%; margen δ = 2% del control (5,5 M$). Tiempo = optimización + un final, en la misma máquina. Para el control y las H3, 8 réplicas de la optimización (otra semilla de Optuna y otra muestra) y el veredicto sale de las 8. | tabla del bloque A de `reporte.html` |
| 3:30–4:15 | Limitaciones | Martín | Réplicas solo para el control y las H3; en H2 `bagging_fraction` sale de Optuna (adaptación del baseline); H1 y H3 comparten estudio; un solo mes de test, cuyo ruido es mayor que el de las réplicas; tiempos de un solo tipo de máquina. | lista de limitaciones |
| 4:15–5:15 | Resultado general | Luis | Un punto por variante, tiempo contra ganancia, con el rango entre réplicas. Arriba a la izquierda están las H3. Las de muestreo al azar caen a medida que aceleran. Las de bagging quedan cerca del control en tiempo. | figura de tiempo contra ganancia con réplicas (`reporte.html`) |
| 5:15–5:45 | H1 | Luis | Todas las tasas debajo de 0,5 pierden; 0,5 es indeterminado. Ninguna de las dos: no hay margen claro. | `bandas_H1.png` |
| 5:45–6:15 | H2 | Luis | Con 0,1 pierde: refutada. Con 0,5 y 0,25 no pierde, pero casi no acelera. | `bandas_H2.png` |
| 6:15–7:30 | H3 con réplicas | Agustina | Con 8 réplicas las H3 siguen sin perder y aceleran de 4,5× a 11,8× (también con el 5 %): confirmada. Pero la ventaja baja de unos 4 M$ a unos 2 M$ y su intervalo contiene a 0: la primera optimización de las H3 había salido con suerte (el control, no). Reescalar `min_data_in_leaf` no cambia nada. U0.25 y H3-0.25 tienen los mismos hiperparámetros: uno pierde y el otro no, así que lo que se pierde en H1 es por entrenar con menos filas. | bloque A, filas de H3 |
| 7:30–8:15 | Varianza | Agustina | Entre un cuarto y 40 % de la varianza de la ganancia es suerte de Optuna. Esa parte no baja con más semillas finales: 50 semillas sobre una sola optimización no alcanzan. | figura de descomposición de varianza (`reporte.html`) |
| 8:15–8:45 | A tiempo igual y exploratorios | Luis | Cada variante gasta el tiempo que le sobra en un ensamble. Ahora con intervalo: H3-0.1 queda arriba del control entre réplicas, pero con el bootstrap de clientes casi nada se distingue de 0. El estudio de Martín va aparte, en el bloque B: otro protocolo, misma conclusión, la muestra mueve la elección. | bloque A (tiempo igual) y bloque B |
| 8:45–9:30 | Conclusión | Agustina | Vale la pena achicar la optimización, no el modelo final: Optuna sobre el 10% y final con todo no pierde y es 8× más rápido. No es una mejora de ganancia: es lo mismo, más rápido. | tabla con "vale la pena" |
| 9:30–10:00 | Qué seguiría | Martín | H4 (muestras que conservan todas las bajas) con réplicas desde el principio, portar los aportes de Luis y otro mes de test. | lista |

El reparto de bloques entre personas es una propuesta; lo confirma el grupo.
