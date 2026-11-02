# Guion del video — Sampling_1 (10 minutos)

Estructura pedida por Bolaños: hipótesis, diseño, limitaciones, resultados, conclusiones. El baseline no se explica: se
nombra y se sigue. Números de `informe/decisiones.md`; figuras de `informe/figuras/`.

| tiempo | bloque | quién | qué se dice | en pantalla |
|---|---|---|---|---|
| 0:00–0:45 | Pregunta | Agustina | La pregunta del tutor: ¿vale la pena ganar velocidad perdiendo performance? Nosotros usamos menos filas sin tocar la proporción de clases; Sampling_2 toca la proporción. | título y pregunta |
| 0:45–2:15 | Hipótesis | Agustina | H1: muestrear el train al azar no pierde hasta r = 0,25. H2: muestrear dentro de LightGBM no pierde ni con 0,1. H3: optimizar sobre una muestra y entrenar con todo no pierde. Vale la pena = no pierde y al menos 2× más rápido. | las tres hipótesis con su predicción |
| 2:15–3:45 | Diseño | Martín | Diez brazos contra el control, cada uno con su Optuna y las mismas 10 semillas. Decide la ganancia en 201910 a 3.300 envíos. Δ apareado por semilla con IC 95%; margen δ = 2% del control (5,5 M$). Tiempo = optimización + un final, en la misma máquina. | tabla de brazos de `reporte.html` |
| 3:45–4:45 | Limitaciones | Martín | Una semilla de Optuna por brazo; H1 y H3 comparten estudio; un solo mes de test; tiempos de una sola máquina; la comparación a tiempo igual es un solo número por brazo, sin intervalo. | lista de limitaciones |
| 4:45–6:00 | Resultado general | Luis | Un punto por brazo, tiempo contra ganancia. Arriba a la izquierda están los dos de H3. Los de muestreo al azar caen a medida que aceleran. Los de bagging quedan cerca del control en tiempo. | `tiempo_vs_ganancia.png` |
| 6:00–6:45 | H1 | Luis | Todas las tasas debajo de 0,5 pierden; 0,5 es indeterminado. Ninguna de las dos: no hay margen claro. | `bandas_H1.png` |
| 6:45–7:30 | H2 | Luis | Con 0,1 pierde: refutada. Con 0,5 y 0,25 no pierde, pero casi no acelera. | `bandas_H2.png` |
| 7:30–8:15 | H3 | Agustina | Las dos tasas no pierden y aceleran 4,5× y 8,4×: confirmada. U0.25 y H3-0.25 tienen los mismos hiperparámetros: uno pierde y el otro no, así que lo que se pierde en H1 es por entrenar con menos filas. | `bandas_H3.png` |
| 8:15–9:00 | A tiempo igual | Luis | Cada brazo gasta el tiempo que le sobra en un ensamble de hasta 10 semillas. Los dos H3 quedan arriba del control (+3,9 y +2,8 M$), los agresivos siguen abajo y U0.5 es el que más sube (+6 M$). Ensamblar el control no le suma. Predijimos que H3 rendiría más; fue U0.5, pero es un solo número sin intervalo. | `tiempo_igual.png` |
| 9:00–9:40 | Conclusión | Agustina | Vale la pena achicar la optimización, no el modelo final: Optuna sobre el 10% y final con todo da la misma ganancia en un octavo del tiempo, y a tiempo igual sigue arriba del control. | tabla con "vale la pena" |
| 9:40–10:00 | Qué seguiría | Martín | Darle un intervalo a la comparación a tiempo igual, reescalar `min_data_in_leaf`, más semillas de Optuna, H4. | lista |

El reparto de bloques entre personas es una propuesta; lo confirma el grupo.
