# sampling_1

El experimento conjunto de Sampling_1 (comisión lunes): compara las hipótesis `h1`–`h3` contra `control` y entrega el
informe y el video. Su pregunta, hipótesis y diseño de fases están en `docs/`; las corridas y los resultados de cada
hipótesis, en la carpeta de cada una (`../control`, `../h1`, `../h2`, `../h3`). Operación: [`docs/operacion.md`](docs/operacion.md).

## Correspondencia de rutas (antes y después del 3-nov-2026)

Hasta el tag `informe-v1` (y los commits anteriores a la separación) el experimento era una sola carpeta,
`experimentos/sampling-velocidad/`, y se corría parado en ella con `PYTHONPATH=../..`. Ahora es `experimentos/sampling_1/`
más una carpeta por hipótesis, y todo se corre desde la raíz del repo. Quien tenga que reproducir un tag o leer un commit
viejo usa esta tabla.

| ruta vieja (`experimentos/sampling-velocidad/…`) | ruta nueva |
|---|---|
| `docs/hipotesis.md` | `experimentos/sampling_1/docs/hipotesis.md` (pregunta y comparación); G, Δ, δ, T, A, N\*, veredictos y control en `experimentos/control/docs/hipotesis.md`; cada H en `experimentos/h1`, `h2`, `h3` `/docs/hipotesis.md` |
| `docs/diseno.md` | `experimentos/sampling_1/docs/diseno.md` (fases, reparto, estimación, tutor); control, máquina y parámetros en `experimentos/control/docs/diseno.md`; variantes de cada H en su `docs/diseno.md` |
| `docs/bitacora.md`, `docs/operacion.md`, `docs/zulip/` | `experimentos/sampling_1/docs/` (la de cada hipótesis, en la suya) |
| `src/correr.py`, `src/metodos.py`, `src/muestreo.py` | `comun/correr.py`, `comun/metodos.py`, `comun/muestreo.py` |
| `src/consolidar.py` | `comun/consolidar.py` (`--experimento X`; sin argumento, todos) |
| `scripts/vm.sh` | `scripts/vm.sh` en la raíz del repo (`lanzar_fase.sh` es nuevo, en la raíz y con un atajo en `experimentos/sampling_1/scripts/`) |
| `scripts/graficar.py` | `experimentos/sampling_1/scripts/graficar.py` (junto a `fase*.txt` y `ledger_parcial.py`, posteriores al renombre) |
| `ledger/resultados.csv`, `estudios.csv`, `reemplazadas.csv`, `corridas/`, `curvas/`, `hp/`, `predicciones/` | repartidos por dueño de la variante o del estudio (`comun/variantes.py`): `experimentos/control/ledger/`, `h1/ledger/`, `h2/ledger/`, `h3/ledger/` (manifiesto en `experimentos/sampling_1/ledger/separacion_manifiesto.json`) |
| `ledger/apareado.csv` | `experimentos/sampling_1/ledger/apareado_previo.csv` (copia de lo que había) y un `apareado.csv` por hipótesis, regenerado por `python -m comun.consolidar` |
| `ledger/exploracion/`, `ledger/sesiones/`, `ledger/tokens.csv` | `experimentos/sampling_1/ledger/` (lo que no tiene variante); `tokens.csv` de cada experimento con lo que declara |
| `informe/` (informe, decisiones, guion, figuras, reporte) | `experimentos/sampling_1/informe/` (conjunto) y `informe/` de cada hipótesis |
| `$BUCKET/ledger/` | sigue sin tocarse; los ledgers nuevos van a `$BUCKET/experimentos/<exp>/ledger/` |

Comandos: `cd experimentos/sampling-velocidad && PYTHONPATH=../.. python -m src.correr …` pasa a
`python -m comun.correr …` desde la raíz; `python -m src.consolidar`, a `python -m comun.consolidar`. El cambio de
openspec que lo hizo es `separar-hipotesis`; el anterior, `experimento-sampling-velocidad`, está archivado.
