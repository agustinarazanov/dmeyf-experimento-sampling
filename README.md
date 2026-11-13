# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026 (comisión lunes): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?**
(Zulip 208986). Sobre el baseline del curso (2019, LightGBM con Optuna), mide cuánto tiempo se ahorra y cuánta ganancia
se pierde en test (201910) cuando se usan menos filas para entrenar u optimizar, sin cambiar la proporción de clases
(eso lo estudia Sampling_2).

**Respuesta corta:** vale la pena achicar la optimización, no el entrenamiento del modelo final. Optuna sobre una muestra
al azar y el final con todas las filas no pierde contra el control y es varias veces más rápido; achicar el final
conservando todas las bajas y la mitad de CONTINUA con peso tampoco pierde. Ninguna de las dos mejora la ganancia por
modelo.

## El sitio

Los resultados, las hipótesis y el método se leen en el sitio:
<https://agustinarazanov.github.io/dmeyf-experimento-sampling/>. Cada página es un archivo de este repo, en la misma
ruta: [Resultados](experimentos/sampling_1/README.md), [H1](experimentos/h1/README.md), [H2](experimentos/h2/README.md),
[H3](experimentos/h3/README.md), [H4](experimentos/h4/README.md), [Control y reglas](experimentos/control/README.md),
[Corridas](experimentos/sampling_1/corridas.md), [Exploratorios](experimentos/sampling_1/exploratorios/README.md) y
[Cómo trabajamos](docs/metodo.md).

### Ver el sitio localmente

Con el entorno de Python del repo:

```bash
pip install -r requirements-sitio.txt
scripts/sitio.sh serve    # busca nombres de personas, construye, verifica los enlaces y sirve en http://127.0.0.1:8000
```

Sin `serve`, `scripts/sitio.sh` solo verifica y construye en `site/`, igual que en CI. Las páginas publicadas son las
del `nav` de `mkdocs.yml`; un enlace relativo a un archivo que no se publica hace fallar el build y va como URL de GitHub.

## Cómo correr

### En la Mac (prueba)

Necesita Python 3.14 (pyenv `facultad`) y `libomp` para LightGBM. Todo se corre desde la **raíz del repo**:

```bash
brew install libomp
pip install -r requirements.txt
python -m comun.datos --filas 20000
python -m comun.correr --metodo uniforme --tasa 0.25 --etapa optimizar --filas 20000
python -m comun.consolidar --experimento h1       # o sin argumento, para todos
python -m comun.reporte --exp h1                  # bloques generados del README de h1; --todos para todos
python -m comun.variantes --verificar             # dependencias, ciclos y qué se rompe si falta una carpeta
python -m pytest
```

`comun.correr` escribe la fila en el ledger del dueño de la variante (`comun/variantes.py`) y lee y escribe los
hiperparámetros en el del dueño del estudio. Las corridas en la Mac son exploratorias (`etapa = exploracion`) y no
entran en los resultados.

### En la VM

Las corridas que cuentan van en `n2-highmem-8` con Ice Lake, desde el template del curso. `PROYECTO` y `BUCKET` salen de
`.env` en la raíz del repo (ver `.env.ejemplo`):

```bash
scripts/lanzar_fase.sh <lista>                # una VM por lista; vuelve enseguida y deja la VM trabajando
scripts/vm.sh <lista-de-configuraciones> --en-seco
```

`vm.sh` crea la VM, copia el repo, instala dependencias, lanza las corridas con `nohup`, sube los `ledger/` de cada
experimento al bucket, los trae y borra la VM. Las fases, las listas y el costo están en
[Corridas](experimentos/sampling_1/corridas.md).

## Estructura

- `comun/`: datos (panel con lags y deltas), baseline, ganancia, ledger, registro de variantes (`variantes.py`),
  muestreo, métodos, `correr.py`, `consolidar.py`, `reporte.py` (los bloques generados de cada README) y registro de
  tokens. Lo usan todos los experimentos; un cambio acá se anuncia en el commit.
- `experimentos/<nombre>/`: un experimento por carpeta (`control`, `h1` a `h4`, `sampling_1`). Cada uno tiene su
  `README.md` (la página del sitio, con las tablas y figuras entre marcadores `<!-- generado:… -->` y las figuras en
  `figuras/`), `docs/bitacora.md` y `ledger/`. Declara en `## Dependencias` de su README de quién lee y no toca carpetas
  ni ledgers ajenos. `sampling_1` además tiene `corridas.md`, `exploratorios/`, `src/`, `scripts/` (las listas de las
  fases) y `docs/` (guion del video y rutas viejas).
- `plantilla/`: la estructura vacía de un experimento. Para agregar una hipótesis: [Cómo trabajamos](docs/metodo.md)
  § Agregar una hipótesis.
- `docs/`: [`metodo.md`](docs/metodo.md) (cómo se trabaja) y [`revision.md`](docs/revision.md) (listas de revisión).
- `sitio/`: páginas de sección, estilos y hooks del sitio; `mkdocs.yml` y `requirements-sitio.txt` en la raíz.
- `scripts/`: `vm.sh`, `lanzar_fase.sh`, `etapa.sh`, `etapas.sh`, `sitio.sh`, `comparar_rondas.py`, los verificadores
  (`verificar_readme.py` comprueba los números de este README; `verificar_informe_h3.py`, los del texto de cada README de
  hipótesis) y scripts de una sola vez de cambios ya aplicados.
- `openspec/`: planes de cambio (proposal, specs, design, tasks); los cerrados en `openspec/changes/archive/` y las specs
  vigentes en `openspec/specs/`.

Los datos no están en el repo. Viven en `DATOS_DIR` (por defecto `~/datos/experimentos-dmeyf`).
