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
