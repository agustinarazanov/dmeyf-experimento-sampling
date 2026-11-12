---
title: Inicio
nav_order: 1
---

# Sampling_1: velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026, comisión lunes. Integrantes: Agustina Razanov, Martín López y Luis María Laguinge. Tutor:
Joaquín I. Aramendía.

**La pregunta del tutor:** ¿vale la pena el tradeoff entre velocidad y pérdida de performance?

Sobre el baseline oficial de Bolaños (2019, LightGBM con Optuna) medimos cuánto tiempo se ahorra y cuánta ganancia se
pierde en 201910 cuando se usan menos filas, sin cambiar la proporción de clases.

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 5 %, 10 % o 25 % de las filas y entrenar con todas no pierde contra el control, también cuando se mide la suerte
de Optuna con 8 réplicas, y es de 4,53 a 11,82 veces más rápido. Entrenar el final con menos filas sí pierde, al azar
desde r = 0,25 y dentro de LightGBM con f = 0,1.

La respuesta al tutor se amplía: vale la pena achicar la optimización (al azar, no informada por clase) y, si además se
quiere el final más rápido, achicar CONTINUA conservando las bajas con peso. `H4F-0.05` (final achicado, conservando todas
las bajas y la mitad de CONTINUA con peso 2) no pierde contra el control, acelera 13,17 veces y a tiempo igual gana; la
cota inferior está cerca de 0, y esta variante viene de una idea vista en 201910. `H4H-0.1` (achicar la búsqueda
conservando todas las bajas y recortando CONTINUA) pierde. Ninguna de las dos es una mejora de ganancia por modelo; la
ganancia extra, si la hay, viene de ensamblar con el tiempo ahorrado.
{: .conclusion }

[Leer el informe conjunto](experimentos/sampling_1/informe/informe.md){: .btn .btn-primary }

## Dónde seguir

- [Tabla de resultados](experimentos/sampling_1/informe/tabla_resultados.md): todas las variantes con su ganancia y su
  velocidad.
- [Experimentos](sitio/experimentos.md): el control y las hipótesis H1 a H4, cada una con informe, reporte, hipótesis y
  diseño.
- [Método](docs/metodo.md): cómo se diseña, se corre y se revisa un experimento.
- [README del repositorio](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/README.md): cómo
  correr el código.
