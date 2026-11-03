¡Hola @**Joaquín I. Aramendía**! Acá va lo nuestro.

**Hipótesis.** Entrenar con menos filas ahorra tiempo casi en proporción y, hasta cierto tamaño de muestra, no pierde ganancia. Probamos cuatro formas de usar menos filas:
- **H1**: sacar filas al azar del train (50%, 25%, 10%, 5%).
- **H2**: dejar que LightGBM muestree por árbol (`bagging_fraction` fijo).
- **H3**: optimizar los hiperparámetros sobre una muestra y entrenar el modelo final con todo.
- **H4**: quedarse con todas las bajas y una parte de los CONTINUA, elegidos con un criterio o con peso por fila.

**Diseño.** El control es el baseline de Bolaños sin tocar, con 10 semillas. Cada variante cambia una sola cosa y se corre con las mismas 10 semillas; arrancamos por el control y H3, y seguimos con las demás. Comparamos la ganancia en 201910 semilla contra semilla y medimos el tiempo de cada corrida en la misma máquina. Una variante "no pierde" si su ganancia queda dentro del 2% del control. De ahí salen las tablas y la curva tiempo contra ganancia.

**¿Vale la pena el tradeoff?** Creemos que sí, hasta cierto punto: hay un tamaño de muestra por debajo del cual la ganancia empieza a caer, y arriba de ese punto se puede ir mucho más rápido sin perder nada. Dónde está ese punto, y cuál de las cuatro formas lo aprovecha mejor, es lo que queremos medir.
