¡Hola @**Joaquín I. Aramendía**! Les pasamos las hipótesis; el diseño (la grilla, las VMs y el reparto) va en el próximo mensaje.

**Pregunta**: con el baseline de Bolaños, ¿cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 si se usan menos filas, **sin tocar la proporción de clases**? (El undersampling de CONTINUA lo hace Sampling_2.)

**Control**: el baseline tal cual (Optuna de 40 trials con nuestros rangos y 100 iteraciones), con 10 semillas finales. Cada brazo se compara contra el control, apareado por semilla, por la ganancia en 201910. El corte de envíos se fija en 201908 con el control.

- **H1, submuestreo uniforme** (r = 0,5 / 0,25 / 0,1 / 0,05, reoptimizando en cada tasa): predecimos que con 0,5 y 0,25 no se pierde y que con 0,1 o menos sí.
- **H2, muestrear dentro de LightGBM** (`bagging_fraction` fijo en 0,5 / 0,25 / 0,1): predecimos que no se pierde ni siquiera con 0,1, porque cada árbol ve filas distintas. GOSS va como brazo descriptivo.
- **H3, optimizar sobre una muestra** (Optuna con el 10% o el 25%, modelo final con el 100%): predecimos que no pierde. Es la que más nos interesa para un pipeline con tiempo acotado.

**Reglas**: un brazo "no pierde" si la cota inferior del IC 95% de la diferencia apareada es ≥ −2% de la ganancia del control, y "pierde" si la media cae por debajo de −2%. Lo que quede en el medio se informa como indeterminado. **Vale la pena** si no pierde y el pipeline completo (optimización y modelo final) es ≥ 2× más rápido.

**Una consulta**: en H2 sacamos `bagging_fraction` de Optuna porque es la variable que estudiamos, y los otros cuatro hiperparámetros se siguen optimizando. ¿Te parece bien esa adaptación del baseline, o preferís que lo dejemos optimizado y comparemos solo GOSS?

¡Gracias!
