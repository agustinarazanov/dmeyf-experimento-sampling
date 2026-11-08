# Proposal

## Why

Martín y Luis sumaron trabajo que hoy no se puede reproducir desde el repo.

**Martín** (`h3/sensibilidad_muestra/`) sigue las convenciones, pero nadie volvió a correr sus pasos 07 y 08.

**Luis** subió un script de Colab y un resumen en `experimentos/Experimentos h3 y h4/`, fuera del método:
- carpeta con espacios y archivo con el nombre roto;
- arma su propio panel en lugar de usar `comun.datos`;
- rutas de Drive;
- hiperparámetros escritos a mano;
- tiempos escalados con un factor de calibración en lugar de medidos en la VM;
- sin ledger.

Además, la mitad de lo que su resumen reporta no tiene código:
- la búsqueda de Optuna con hard negatives (sus hiperparámetros están hardcodeados);
- H4 con negativos uniformes;
- el muestreo por cliente;
- el reescalado lineal;
- el análisis del presupuesto de 15 minutos, con "más de 60 semillas" y 283,25 M$;
- el `resumen_50_semillas.csv`, que el HTML anuncia pero el script nunca escribe.

Queremos poder **replicar todo lo que hicieron los dos**, y que sus ideas se prueben con nuestro protocolo como
variantes. El grupo queda con **cuatro hipótesis**:
- H1: submuestreo uniforme;
- H2: bagging y GOSS;
- H3: optimizar con muestra y entrenar con todo;
- **H4: muestras informadas por clase**, que conservan todas las bajas.

Reconstruimos nosotros lo que falta, sin esperar el código de Luis.

## What Changes

- **Migración de Luis a las convenciones del repo.** Desaparece `experimentos/Experimentos h3 y h4/` y su trabajo
  queda en `experimentos/sampling_1/exploratorios/validacion_50_semillas/` como un paquete Python:
  - corre desde la raíz con `python -m`;
  - importa solo de `comun/` y de su carpeta;
  - usa el panel de `comun.datos` y `DATOS_DIR`;
  - lee los hiperparámetros de los ledgers, con un modo `--hp-original` que usa los que él tenía escritos;
  - mide los tiempos en la VM;
  - escribe sus CSV en `resultados/`, con procedencia;
  - tiene tests sin datos, `README.md` y `exploratorio.json`.

  Su resumen se conserva como `resumen_original.md`.
- **Reconstrucción de lo que falta:**
  - el CSV por estrategia y semilla;
  - el análisis del presupuesto de 900 s: cuántas semillas entran y qué ganancia da el ensamble;
  - el estudio de Optuna con hard negatives.
- **Replicación de lo reportado.**
  - Se corre el paquete de Luis completo (9 estrategias × 50 semillas) y se compara con cada número de su resumen.
  - Se corren de nuevo 07 y 08 de Martín y se comparan con sus CSV por sha256.
  - Cada README suma una tabla de tres columnas: reportado, reproducido y diferencia.
- **Variantes nuevas, pre-registradas y con 8 réplicas de optimización** (reusan los estudios `@k` de
  `h3-semillas-optuna`):
  - en `h3`:
    - `H3R-0.25`: reescalado √(1/r);
    - `H3L-0.25` y `H3L-0.1`: reescalado lineal 1/r;
    - `H3K-0.1`: busca sobre el 10 % de los clientes con toda su historia, en lugar del 10 % de las filas.
  - en el nuevo experimento `h4`:
    - `H4H-0.1`: busca con todas las bajas + 10 % de CONTINUA tomada de los negativos difíciles; entrena con todo;
    - `H4U-0.1`: igual, pero con CONTINUA uniforme;
    - `H4F-0.05` y `H4F-0.25`: buscan como H3 y entrenan con todas las bajas + 50 % de CONTINUA con peso 2
      (fast-retrain).
- **`h4` como experimento completo**, desde `plantilla/`, con su hipótesis, diseño, ledger, informe y reporte.
  `sampling_1` lo suma a la comparación de cuatro hipótesis.
- **Informes.**
  - `sampling_1/informe/informe.md`, `guion.md` y el README de la raíz pasan a cuatro hipótesis, con los dos
    exploratorios replicados en el bloque B.
  - El informe declara que las ideas de H4 y de los reescalados surgieron mirando 201910, el mismo mes con el que se
    evalúan.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `protocolo-experimental`:
  - un aporte se incorpora replicándolo, con la tabla reportado/reproducido;
  - lo que no tiene código se reconstruye y se marca como reconstruido;
  - una idea que viene de mirar el test lo declara.
- `corrida-reproducible`: métodos de muestra por cliente, muestra de búsqueda informada por clase (con la sonda que
  elige los negativos difíciles), final submuestreado con pesos y reescalado de hiperparámetros.

## Impact

- `comun/` (anunciar en el commit):
  - `variantes.py`: 8 variantes, 3 estudios nuevos con dueño y el experimento `h4`;
  - `metodos.py`: muestras por cliente y por clase, sonda, final con pesos y reescalados;
  - `muestreo.py`.
- Experimentos:
  - `experimentos/h4/` nuevo;
  - `h3/docs` e `informe`;
  - `h3/sensibilidad_muestra/` (README con la tabla de replicación y salidas nuevas en `DATOS_DIR`);
  - `sampling_1/exploratorios/`;
  - `sampling_1/informe`;
  - README.
- Cómputo en `n2-highmem-8` spot, todo lanzado por Agustina en VMs paralelas:
  - variantes nuevas: ~5,8 h, en 8 VMs por réplica;
  - Luis: ~3,7 h, en 9 VMs por estrategia;
  - Martín: ~2,1 h, en una VM.

  Son unas 12 h de VM y ~2 h de pared.
- Depende de `renombrar-brazos` y de `h3-semillas-optuna` archivados, porque usa sus estudios `@k`, `replica_opt` y
  la comparación en dos bloques.
- Fuera de alcance: otros meses de test, e ideas que no estén en los aportes de Martín o de Luis.
