# Proyecto Sampling — DMEyF 2026

Este repositorio contiene la evaluación exhaustiva de técnicas de muestreo (Sampling) para optimizar el tiempo de búsqueda de hiperparámetros y entrenamiento de modelos LightGBM, manteniendo o superando la ganancia predictiva del modelo Baseline.

## 🎯 Objetivo General
Reducir los tiempos computacionales de nuestro pipeline (que originalmente consumía ~13 minutos solo en buscar hiperparámetros) para poder re-entrenar y ensamblar múltiples semillas dentro de una ventana de producción estricta de **15 minutos (900 segundos)**.

---

## 📂 ¿Dónde está el código final?

El código unificado que demuestra estadísticamente nuestras conclusiones (evaluado a **50 semillas** para suprimir la varianza) se encuentra en:
👉 `experimentos/Experimentos h3 y h4/validacion_50_semillas.py`

*Nota sobre reproducibilidad:* No se subieron los historiales de las bases de datos de Optuna (`.db`) dado su gran tamaño. Los hiperparámetros óptimos descubiertos fueron fijados (*hardcodeados*) directamente en el script, permitiendo que cualquier miembro del equipo ejecute la validación de 50 semillas en minutos y sin dependencias externas.

---

## ✅ LO QUE SÍ FUNCIONÓ (Recomendaciones Finales)

### 1. Validación Robusta a 50 Semillas
* **El Hallazgo:** Evaluar con solo 10 semillas dejaba muchas estrategias prometedoras en veredicto *"NO PIERDE"* porque el intervalo de confianza (IC 95%) era muy amplio y tocaba el cero. Al escalar a **50 semillas**, el error estándar cayó a la mitad.
* **Conclusión:** Pudimos demostrar estadísticamente que **todas las variantes de la Hipótesis 3 le GANAN al Control**.

### 2. Hipótesis 3 (H3): Muestrear en Optuna, Entrenar con Todo
* **El Campeón (H3-0.05):** Utilizar apenas el **5% del dataset** (muestreo uniforme) para buscar hiperparámetros en Optuna, y luego entrenar el modelo final con el 100% de los datos.
* **Por qué funciona:** En una muestra tan reducida, Optuna se ve forzado a elegir hiperparámetros fuertemente regularizados (ej. `feature_fraction = 0.34`, `min_data_in_leaf = 985`). Al aplicar estas reglas al dataset completo, actúan como un excelente antídoto contra el sobreajuste masivo que sufre el Control (`ff = 0.985`). Logró **+6,47 M$** sobre el baseline y aceleró Optuna **8.89x**.

### 3. Hipótesis 4 (H4): Retener Bajas + Hard Negatives
* **El Hallazgo:** En lugar de hacer un muestreo uniforme en Optuna (que descarta el 90% de la clase minoritaria), armamos la muestra de búsqueda conservando el **100% de las Bajas + 10% de la clase `CONTINUA` priorizando casos difíciles (Hard Negatives)**.
* **Conclusión:** Esta asimetría le dio al modelo la ganancia media más alta de todo el experimento (**+7,19 M$** sobre el Control).

### 4. Arquitectura "Fast-Retrain" (Pipeline de Producción)
* **El Problema:** El modelo Control tarda 35 segundos en entrenar una sola semilla final. En 15 minutos solo logramos ensamblar 4 semillas.
* **La Solución:** Entrenamos el modelo final usando el 100% de las Bajas y solo el **50% de la clase Continua (reponderada con peso $w=2$)**.
* **Conclusión:** El tiempo de entrenamiento final cayó a **12,3s por semilla**. Esto nos permite re-entrenar y ensamblar **más de 60 semillas** en nuestra ventana de 15 minutos, disparando la ganancia a **$283,25 M** (vs los $276,65 M del Control a tiempo igual).

### 5. Reescalado Sublineal
* **El Hallazgo:** Al pasar de la muestra chica (Optuna) al dataset completo (Final), reescalar el parámetro `min_data_in_leaf` multiplicándolo por la raíz cuadrada de la proporción ($\times \sqrt{1/r}$) redujo la varianza entre semillas y mejoró el rendimiento del ensamble.

---

## ❌ LO QUE NO FUNCIONÓ (Descartes)

Para evitar repetir errores, documentamos las estrategias que deterioraron el rendimiento y fueron descartadas del pipeline final:

### 1. Hipótesis 1 (H1): Muestreo Uniforme en el Entrenamiento Final
* **El Error:** Mantener el muestreo uniforme estricto (ej. 25% o 10%) tanto en la etapa de Optuna como en el entrenamiento final del modelo.
* **Por qué falló:** Al reducir la muestra por debajo del 50%, se pierden demasiados ejemplos de la clase positiva (`BAJA+1` y `BAJA+2`). Al árbol le faltan casos minoritarios para definir correctamente la frontera de decisión y el rendimiento predictivo se desploma estrepitosamente. **Regla de oro: En el entrenamiento final siempre se debe conservar el 100% del target positivo.**

### 2. Reescalado Lineal de Hiperparámetros
* **El Error:** Multiplicar `min_data_in_leaf` de forma directa por la inversa de la proporción (ej. $\times 4$ si la muestra era del 25%, o $\times 10$ si era del 10%).
* **Por qué falló:** Resulta en hojas excesivamente grandes y árboles muy poco profundos/conservadores cuando se aplican al 100% de los datos. La ganancia media cayó drásticamente frente al reescalado sublineal.

### 3. Optuna en H4 Uniforme (Sin Hard Negatives)
* **El Error:** Conservar el 100% de las Bajas, pero rellenar el resto de la muestra de Optuna con un 10% de clase `CONTINUA` elegida de forma *completamente aleatoria*.
* **Por qué falló:** Al presentarle al modelo todas las bajas junto con negativos "fáciles", Optuna sobreestima la capacidad del modelo y selecciona arquitecturas excesivamente complejas (ej. `num_leaves = 226`, `feature_fraction > 0.70`). Esto introduce altísima varianza predictiva cuando se evalúa de manera individual (-2,31 M$).

### 4. Muestreo Longitudinal (Por Cliente)
* **El Error:** Realizar el submuestreo agrupando por `numero_de_cliente` (conservando toda la historia de un cliente) en lugar de muestrear filas de forma independiente.
* **Por qué falló:** Como nuestros datos ya incluyen variables históricas pre-calculadas (lags y deltas), la dependencia temporal ya está capturada en las columnas. Muestrear clientes enteros reduce severamente la diversidad transversal de perfiles que el árbol puede observar en un mes determinado, resultando en un peor rendimiento que el muestreo tradicional por filas a igual volumen de datos.