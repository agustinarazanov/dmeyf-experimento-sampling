"""Replicación de Martín en la VM (incorporar-aportes, D5): corre su paquete tal cual, en el orden de D5.

0. las versiones fijas de su `requirements.txt` (además de las de la raíz, como dice su README);
1. `insumos` y `insumos --solo-verificar`;
2. `sensibilidad_07`;
3. `ganancia_08 --corrida-07 <la nueva>`.

Solo agrega lo que la VM necesita: las salidas van a `ledger/martin/` de `sampling_1` (07 y 08, cada una con su
`<marca>`), así suben al bucket, y la corrida nueva de 07 se busca ahí para pasársela a 08.

    python -m experimentos.sampling_1.exploratorios.replicacion_martin [--en-seco]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from comun import rutas

PAQUETE = "experimentos.h3.sensibilidad_muestra"
SALIDA = rutas.ledger("sampling_1") / "martin"


def corrida_07_nueva(salida_07: Path, antes: set[Path]) -> Path:
    """La carpeta de 07 que apareció en esta ejecución (07 escribe `<salida>/<nombre>/<marca>/diseno.json`)."""
    nuevas = sorted(p.parent for p in salida_07.glob("*/*/diseno.json") if p.parent not in antes)
    if len(nuevas) != 1:
        raise RuntimeError(f"se esperaba una corrida nueva de 07 en {salida_07}, hay {len(nuevas)}: {nuevas}")
    return nuevas[0]


REQUISITOS = Path(__file__).resolve().parents[2] / "h3" / "sensibilidad_muestra" / "requirements.txt"


def pasos(salida: Path) -> list[list[str]]:
    s07 = salida / "07"
    return [
        ["pip", "install", "-q", "-r", str(REQUISITOS)],
        [f"{PAQUETE}.insumos"],
        [f"{PAQUETE}.insumos", "--solo-verificar"],
        [f"{PAQUETE}.sensibilidad_07", "--salida", str(s07)],
        [f"{PAQUETE}.ganancia_08", "--corrida-07", "<la nueva de 07>", "--salida", str(salida / "08")],
    ]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--salida", type=Path, default=SALIDA)
    p.add_argument("--en-seco", action="store_true", help="imprime los pasos y sale")
    a = p.parse_args()
    s07 = a.salida / "07"
    if a.en_seco:
        for paso in pasos(a.salida):
            print("python -m", " ".join(paso))
        return
    s07.mkdir(parents=True, exist_ok=True)
    antes = {d.parent for d in s07.glob("*/*/diseno.json")}
    for paso in pasos(a.salida):
        if "<la nueva de 07>" in paso:
            paso = [str(corrida_07_nueva(s07, antes)) if x == "<la nueva de 07>" else x for x in paso]
        print("== python -m", " ".join(paso), flush=True)
        subprocess.run([sys.executable, "-m", *paso], check=True)


if __name__ == "__main__":
    main()
