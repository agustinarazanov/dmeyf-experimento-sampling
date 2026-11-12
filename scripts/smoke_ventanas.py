"""Smoke de `final-con-julio-agosto` 2.7 en la Mac: finales de 201903-201908 con `--filas 20000`, todo en una salida temporal.

    python -m scripts.smoke_ventanas SALIDA_TEMPORAL   # como módulo: importa `comun`

Usa el panel de smoke de `DATOS_DIR` (enlazado, no copiado) y manda ledger, hp y bases de Optuna a SALIDA_TEMPORAL, así no
toca el repo ni los estudios de smoke anteriores. Corre: C y H4F-0.05 con dos semillas; `F0.5@2` con 3 trials y un final de
`H4O-0.5` (réplica 2) que lo lee. Imprime lo que hay que verificar y sale con 0 solo si todo coincide.
"""
import sys
from pathlib import Path

import pandas as pd

from comun import baseline as bl
from comun import correr, rutas
from comun import datos as dt
from comun import ledger as lg


def main(salida: Path) -> int:
    salida.mkdir(parents=True, exist_ok=True)
    panel = dt.ruta_panel(20000)
    (salida / "datos").mkdir(exist_ok=True)
    enlace = salida / "datos" / panel.name
    if not enlace.exists():
        enlace.symlink_to(panel)
    bl.DATOS_DIR = salida / "datos"
    rutas.EXPERIMENTOS = salida / "experimentos"
    comun = ["--filas", "20000", "--trials", "3"]
    por_etapa: list[tuple[str, list[int]]] = []

    def paso(argv: list[str]) -> None:
        dt.MESES_LEIDOS.clear()  # el guard de `optimizar` mira lo leído en el proceso: una etapa por vez
        correr.main(argv)
        por_etapa.append((f"{argv[1]} {argv[5]}", sorted(set(dt.MESES_LEIDOS))))

    paso(["--metodo", "uniforme", "--tasa", "1", "--etapa", "optimizar", *comun])
    paso(["--metodo", "uniforme", "--tasa", "1", "--etapa", "final", "--semilla", "100003,200003", *comun])
    paso(["--metodo", "uniforme", "--tasa", "0.05", "--etapa", "optimizar", *comun])
    paso(["--metodo", "fast-retrain", "--tasa", "0.05", "--etapa", "final", "--semilla", "100003,200003", *comun])
    paso(["--metodo", "fast-retrain-opt", "--tasa", "0.5", "--etapa", "optimizar", "--replica", "2", *comun])
    paso(["--metodo", "fast-retrain-opt", "--tasa", "0.5", "--etapa", "final", "--semilla", "100003,200003",
                 "--replica", "2", *comun])
    malas = []
    for exp, variante, n in (("control", "C", 2), ("h4", "H4F-0.05", 2), ("h4", "H4O-0.5", 2)):
        led = rutas.ledger(exp) / "exploracion"
        c = lg.leer_corridas(led / "corridas")
        f = c[(c["variante"] == variante) & (c["etapa_corrida"] == "final")]
        ok = (len(f) == n and set(f["meses_final"]) == {"201903-201908"} and f["auc_val"].isna().all()
              and f["curva_201908"].isna().all() and f["auc_test"].notna().all()
              and f["id"].str.contains("final-0308").all() and not list((led / "curvas").glob("*_201908.csv")))
        print(f"{variante}: {len(f)} finales, meses_final={sorted(set(f['meses_final']))}, auc_val vacío={f['auc_val'].isna().all()}, "
              f"curva_201908 vacía={f['curva_201908'].isna().all()}, ids con -0308={f['id'].str.contains('final-0308').all()} -> "
              f"{'OK' if ok else 'FALLA'}")
        if not ok:
            malas.append(variante)
    o = lg.leer_corridas(rutas.ledger("h4") / "exploracion" / "corridas")
    o = o[o["etapa_corrida"] == "optimizar"]
    print(f"estudios optimizados: {sorted(o['estudio'])}; meses_final de optimización vacío: {o['meses_final'].isna().all()}")
    hp = rutas.ledger("h4") / "exploracion" / "hp" / "F0.5@2.json"
    print(f"hp de F0.5@2 existe: {hp.exists()}")
    if not hp.exists() or not o["meses_final"].isna().all() or "F0.5@2" not in set(o["estudio"]):
        malas.append("F0.5@2")
    for nombre, meses in por_etapa:
        print(f"meses leídos por {nombre}: {meses}")
        if nombre.endswith("optimizar") and (201907 in meses or bl.MES_TEST in meses):
            malas.append(f"{nombre} leyó 201907 o 201910")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
