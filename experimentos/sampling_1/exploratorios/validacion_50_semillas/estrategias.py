"""Las nueve estrategias de Luis, sus semillas y sus hiperparámetros. No lee datos.

PORTADO sin cambios de lógica del commit 9e1889e (`script_de_validaci_n_50_semillas.py`): la lista de estrategias, las
semillas (`SEMILLAS_10_OFICIALES` + `110017 + i·19937`), `escalar_hp` y el modo "fast-retrain" (50 % de las CONTINUA con
peso 2). La numeración es 1…9 (la de su script empieza en 0).
RECONSTRUIDO: `--hp ledger` (lee nuestros `hp/*.json`; el de `H4_Hard` sale del estudio `NH0.1` de `h4`) y la extensión de
semillas más allá de 50 (misma fórmula, i > 39).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from comun import baseline as bl
from comun import rutas

AQUI = Path(__file__).resolve().parent
SEMILLAS_10_OFICIALES = list(bl.SEMILLAS_FINALES)
N_SEMILLAS = 50
#: Corte de envíos de Luis: el N* de 201908 del control.
N_ESTRELLA = 3300


def semillas(n: int = N_SEMILLAS) -> list[int]:
    """Las 10 oficiales y después `110017 + i·19937`, i = 0…n-11. Con n = 50 es la lista de Luis; con n > 50 la extiende."""
    if n < 1:
        raise ValueError(f"n de semillas inválido: {n}")
    return (SEMILLAS_10_OFICIALES + [110017 + i * 19937 for i in range(max(0, n - 10))])[:n]


def escalar_hp(hp_base: dict, mult_min_data: float = 1.0, mult_leaves: float = 1.0, mult_lr: float = 1.0) -> dict:
    d = dict(hp_base)
    d["min_data_in_leaf"] = int(np.clip(round(d["min_data_in_leaf"] * mult_min_data), 10, 8000))
    d["num_leaves"] = int(np.clip(round(d["num_leaves"] * mult_leaves), 8, 1024))
    d["learning_rate"] = float(np.clip(d["learning_rate"] * mult_lr, 0.005, 0.3))
    return d


@dataclass(frozen=True)
class Estrategia:
    id: int
    nombre: str
    familia: str
    estudio: str            # clave de los hiperparámetros: C, U0.25, U0.1, U0.05 o H4_Hard
    mult_min_data: float    # "Idea A": factor sobre `min_data_in_leaf`
    modo: str               # "full" o "h4_50_pesos" (fast-retrain)

    @property
    def slug(self) -> str:
        return f"e{self.id}"


ESTRATEGIAS = [
    Estrategia(1, "Control_C (Full 100%)", "Control", "C", 1.0, "full"),
    Estrategia(2, "H3-0.25 (Original 25%)", "H3_Base", "U0.25", 1.0, "full"),
    Estrategia(3, "H3-0.10 (Original 10%)", "H3_Base", "U0.1", 1.0, "full"),
    Estrategia(4, "H3-0.05 (Campeon 5%)", "H3_Campeon", "U0.05", 1.0, "full"),
    Estrategia(5, "IdeaA_H3-0.25_SqrtScale(x2)", "Idea_A_Scale", "U0.25", 2.0, "full"),
    Estrategia(6, "IdeaA_H3-0.10_SqrtScale(x3.2)", "Idea_A_Scale", "U0.1", 3.16, "full"),
    Estrategia(7, "IdeaB_OptH4_HardNeg_Full", "Idea_B_H4", "H4_Hard", 1.0, "full"),
    Estrategia(8, "IdeaC_FastRetrain_U0.05_H4_50pct", "Idea_C_Fast", "U0.05", 1.0, "h4_50_pesos"),
    Estrategia(9, "IdeaC_FastRetrain_U0.25_H4_50pct", "Idea_C_Fast", "U0.25", 1.0, "h4_50_pesos"),
]

#: Fracción de CONTINUA que conserva el fast-retrain de Luis y peso que se les da (1/f).
FRACCION_FAST = 0.5


def estrategia(id_: int) -> Estrategia:
    for e in ESTRATEGIAS:
        if e.id == id_:
            return e
    raise ValueError(f"estrategia {id_} inexistente (1…{len(ESTRATEGIAS)})")


# --- hiperparámetros ------------------------------------------------------------------------------------------------

#: Dónde vive el `hp/<estudio>.json` de cada clave en nuestro ledger (`H4_Hard` sale de `NH0.1`, reconstruido).
LEDGER_HP = {"C": ("control", "C"), "U0.25": ("h1", "U0.25"), "U0.1": ("h1", "U0.1"), "U0.05": ("h1", "U0.05"),
             "H4_Hard": ("h4", "NH0.1")}


def hp_original() -> dict[str, dict]:
    """`hp_original.json`: los hiperparámetros y `t_opt` escritos a mano en el script de Luis."""
    return json.loads((AQUI / "hp_original.json").read_text())


def hp_ledger(clave: str, raiz: Path = rutas.RAIZ) -> dict:
    """Lo mismo que una entrada de `hp_original.json`, leído de `experimentos/<exp>/ledger/hp/<estudio>.json`
    (t_opt = `tiempo_optimizacion_s`)."""
    exp, estudio = LEDGER_HP[clave]
    ruta = raiz / "experimentos" / exp / "ledger" / "hp" / f"{estudio}.json"
    if not ruta.is_file():
        raise FileNotFoundError(f"falta {ruta.relative_to(raiz)}: `--hp ledger` necesita el estudio {estudio} de {exp}")
    d = json.loads(ruta.read_text())
    return {"hp": d["hp"], "t_opt": float(d["tiempo_optimizacion_s"])}


def hp_de(e: Estrategia, modo_hp: str = "original", raiz: Path = rutas.RAIZ) -> tuple[dict, float]:
    """(hiperparámetros finales de la estrategia, tiempo de optimización en segundos)."""
    if modo_hp not in ("original", "ledger"):
        raise ValueError(f"--hp inválido: {modo_hp!r} (original o ledger)")
    base = hp_original()[e.estudio] if modo_hp == "original" else hp_ledger(e.estudio, raiz)
    return escalar_hp(base["hp"], mult_min_data=e.mult_min_data), float(base["t_opt"])
