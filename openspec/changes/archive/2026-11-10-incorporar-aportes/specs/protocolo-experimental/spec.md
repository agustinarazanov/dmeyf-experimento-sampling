## ADDED Requirements

### Requirement: Un aporte se incorpora replicándolo
Un aporte que llega de fuera del método se incorpora como estudio exploratorio, en un paquete que corre desde la raíz con
`python -m` sobre `comun/` y `DATOS_DIR`, sin rutas personales ni entornos externos.

Su `README.md` SHALL tener una tabla con estas columnas:
- cada número que reportó su autor;
- el número reproducido en `n2-highmem-8`;
- la diferencia;
- la explicación de cualquier diferencia que no sea cero.

Lo que el autor reportó sin código SHALL reconstruirse a partir de su descripción, marcarse como **reconstruido** en
el README y en el código, y dejar escrita la interpretación elegida cuando la descripción admite más de una.

#### Scenario: Número reproducido distinto del reportado
- **WHEN** la ganancia media de una estrategia de Luis reproducida en la VM difiere de la de su resumen
- **THEN** la tabla muestra las dos y la diferencia, y el README explica la causa (otro panel, otra cantidad de hilos,
  tiempos calibrados contra medidos) o dice que no se encontró

#### Scenario: Pieza sin código
- **WHEN** el resumen describe un resultado (por ejemplo, la búsqueda con hard negatives) cuyo código no está en el
  aporte
- **THEN** existe una reconstrucción marcada como tal, con la interpretación elegida escrita, y sus números van en la
  tabla con la etiqueta "reconstruido"

#### Scenario: Replicación byte a byte
- **WHEN** el aporte trae sus salidas con sha256, como `h3/sensibilidad_muestra/resultados/procedencia.json`
- **THEN** la replicación compara las huellas de las salidas nuevas con las registradas, y la tabla dice "idéntico" o
  muestra la primera diferencia

### Requirement: Ideas que vienen de mirar el test
Una variante que se registra a partir de un resultado ya visto en 201910 SHALL declararlo en su `docs/hipotesis.md`, y
el informe de su experimento y el de `sampling_1` SHALL listarla entre las limitaciones. Su predicción y su regla se
escriben igual que las demás, antes de correr.

#### Scenario: H4 viene del aporte de Luis
- **WHEN** se lee `experimentos/h4/docs/hipotesis.md`
- **THEN** dice que las variantes salieron de estrategias que Luis eligió mirando 201910, y que el resultado de H4 no
  cuenta con un mes de test que no se haya mirado

### Requirement: 201910 solo para la comparación
Como pide la consigna (Zulip 208135), toda elección SHALL hacerse con 201908. Esto vale para las variantes del registro
y para los estudios exploratorios. Una elección es:
- un orden entre estrategias;
- un descarte;
- un corte de envíos;
- una cantidad de semillas para ensamblar;
- un factor de reescalado;
- un "campeón".

201910 SHALL usarse solo para comparar, en una tabla que incluye todas las variantes o estrategias del estudio, y
ningún resultado en 201910 SHALL decidir qué se corre, qué se descarta ni con qué parámetros. 201909, 201911 y 201912 no
SHALL usarse.

#### Scenario: Exploratorio que eligió en test
- **WHEN** se porta un aporte que eligió o descartó estrategias por su resultado en 201910
- **THEN** el paquete portado ordena y clasifica con 201908, muestra 201910 solo en la tabla de comparación con todas las
  estrategias y deja los números originales en una sección de reproducción, separada de sus conclusiones

#### Scenario: Máximo de la curva
- **WHEN** un reporte muestra la ganancia máxima de una curva
- **THEN** la de 201908 puede orientar, y la de 201910 se informa como referencia pero ninguna conclusión se apoya en
  ella; la métrica que decide sigue siendo G al corte N\* fijado en 201908
