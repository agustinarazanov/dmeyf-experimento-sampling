"""Registro único de variantes y estudios: quién es dueño de qué, y de quién depende cada experimento.

    python -m comun.variantes --verificar

De acá salen el nombre de la variante y del estudio de cada `(método, tasa)`, el ledger al que va cada fila y las
dependencias implícitas entre experimentos. `## Dependencias` de cada `docs/diseno.md` las escribe una persona y
`--verificar` las compara con lo que implica el registro (`openspec/specs/dependencias-entre-experimentos`).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, NamedTuple

from comun import rutas

CONTROL = "control"
AGREGADOR = "sampling_1"  # no es dueño de variantes: compara y lee de todos los demás


class Variante(NamedTuple):
    nombre: str
    dueno: str
    metodo: str
    tasa: float
    estudio: str
    replicas: bool = False  # admite réplicas de optimización `--replica k ≥ 1` (`h3-semillas-optuna` D2)
    grilla: str = ""  # fila de la grilla común (`FILAS_GRILLA`), "control", o "" si está fuera (`FUERA_DE_GRILLA`)


def _t(tasa: float) -> str:
    return f"{tasa:g}"


TASAS_GRILLA = (0.5, 0.25, 0.1, 0.05)

#: Variantes que comparten estudios y se comparan entre sí, apareadas por réplica y semilla: (a, b) es `a − b`.
#: Los pares de dos experimentos (`U − H3`) los arma `sampling_1` (`ledger/pares.csv`); acá se declaran igual.
PARES_APAREADOS: list[tuple[str, str]] = [
    ("H3R-0.1", "H3-0.1"),
    # `incorporar-aportes` D4: raíz contra lineal y raíz contra nada en r = 0,25 (`h3/docs/hipotesis.md` reglas 5 y 6)
    ("H3R-0.25", "H3L-0.25"), ("H3R-0.1", "H3L-0.1"), ("H3R-0.25", "H3-0.25"),
    # `tiempos-confiables-y-consistencia` D12: muestrear también el final (U − H3, comparten `U{r}`) y, con bajas, H4O − H4P
    *[(f"U{_t(r)}", f"H3-{_t(r)}") for r in TASAS_GRILLA],
    *[(f"H4O-{_t(r)}", f"H4P-{_t(r)}") for r in TASAS_GRILLA],
]

#: Variantes que no comparten estudios y se comparan entre sí sin aparear, con IC de Welch entre réplicas: `a − b`
#: (`incorporar-aportes` D4: `h4/docs/hipotesis.md` regla 2 y `h3/docs/hipotesis.md` regla 7).
#: `final-con-julio-agosto` D11: `H4O-0.5` (estudio propio sobre la receta de H4F) contra `H4F-0.05` (estudio `U0.05`).
#: `tiempos-confiables-y-consistencia` D12: conservar las bajas (`H4O − U` principal, `H4P − H3`) y el peso (`H4P-0.1 − H4U-0.1`).
PARES_WELCH: list[tuple[str, str]] = [
    ("H4H-0.1", "H4U-0.1"), ("H3K-0.1", "H3-0.1"), ("H4O-0.5", "H4F-0.05"),
    *[(f"H4O-{_t(r)}", f"U{_t(r)}") for r in TASAS_GRILLA],
    *[(f"H4P-{_t(r)}", f"H3-{_t(r)}") for r in TASAS_GRILLA],
    ("H4P-0.1", "H4U-0.1"),
]

#: Por cada par declarado, la decisión que aísla y si es un contraste principal (D12). Cada par de las dos listas de arriba
#: tiene su entrada, y un test lo verifica.
PARES_INFO: dict[tuple[str, str], tuple[str, bool]] = {
    ("H3R-0.1", "H3-0.1"): ("reescalar min_data_in_leaf con la raíz en el final", False),
    ("H3R-0.25", "H3L-0.25"): ("reescalado con raíz contra lineal en r = 0,25", False),
    ("H3R-0.1", "H3L-0.1"): ("reescalado con raíz contra lineal en r = 0,1", False),
    ("H3R-0.25", "H3-0.25"): ("reescalar con la raíz contra no reescalar en r = 0,25", False),
    ("H4H-0.1", "H4U-0.1"): ("CONTINUA difíciles contra al azar en la búsqueda", False),
    ("H3K-0.1", "H3-0.1"): ("muestrear por cliente contra por fila en la búsqueda", False),
    ("H4O-0.5", "H4F-0.05"): ("reoptimizar sobre la receta de H4F (estudio propio) contra reusar `U0.05`", False),
    **{(f"U{_t(r)}", f"H3-{_t(r)}"): ("muestrear también el final, al azar", False) for r in TASAS_GRILLA},
    **{(f"H4O-{_t(r)}", f"H4P-{_t(r)}"): ("muestrear también el final, con bajas", False) for r in TASAS_GRILLA},
    **{(f"H4O-{_t(r)}", f"U{_t(r)}"): ("conservar las bajas, en búsqueda y final", True) for r in TASAS_GRILLA},
    **{(f"H4P-{_t(r)}", f"H3-{_t(r)}"): ("conservar las bajas, solo en la búsqueda", False) for r in TASAS_GRILLA},
    ("H4P-0.1", "H4U-0.1"): ("el peso en la búsqueda (misma muestra)", False),
}


VARIANTES: dict[str, Variante] = {
    b.nombre: b
    for b in [
        Variante("C", CONTROL, "uniforme", 1.0, "C", replicas=True, grilla="control"),
        Variante("C-rep", CONTROL, "uniforme", 1.0, "C", grilla="control"),
        # `tiempos-confiables-y-consistencia` D8, D9: la grilla común (cinco formas por cuatro tasas) y 8 réplicas en el bloque A
        *[Variante(f"U{_t(r)}", "h1", "uniforme", r, f"U{_t(r)}", replicas=True, grilla="U") for r in TASAS_GRILLA],
        *[Variante(f"B{_t(f)}", "h2", "bagging", f, f"B{_t(f)}", replicas=True, grilla="B") for f in TASAS_GRILLA],
        Variante("GOSS", "h2", "goss", 1.0, "GOSS", replicas=True),
        *[Variante(f"H3-{_t(r)}", "h3", "opt-muestra", r, f"U{_t(r)}", replicas=True, grilla="H3") for r in TASAS_GRILLA],
        Variante("H3R-0.1", "h3", "opt-muestra-reescalado", 0.1, "U0.1", replicas=True),
        # `incorporar-aportes` D3: extensiones de H3 (aporte de Luis) y H4, todas con réplicas de optimización
        Variante("H3R-0.25", "h3", "opt-muestra-reescalado", 0.25, "U0.25", replicas=True),
        Variante("H3L-0.25", "h3", "opt-muestra-lineal", 0.25, "U0.25", replicas=True),
        Variante("H3L-0.1", "h3", "opt-muestra-lineal", 0.1, "U0.1", replicas=True),
        Variante("H3K-0.1", "h3", "opt-muestra-cliente", 0.1, "K0.1", replicas=True),
        Variante("H4H-0.1", "h4", "clase-dificil", 0.1, "NH0.1", replicas=True),
        Variante("H4U-0.1", "h4", "clase-uniforme", 0.1, "NU0.1", replicas=True),
        Variante("H4F-0.05", "h4", "fast-retrain", 0.05, "U0.05", replicas=True),
        Variante("H4F-0.25", "h4", "fast-retrain", 0.25, "U0.25", replicas=True),
        # `final-con-julio-agosto` D11: reoptimiza sobre el set del final (receta de H4F con f = 0,5); D8 la lleva a f = 0,25; 0,1; 0,05
        *[Variante(f"H4O-{_t(f)}", "h4", "fast-retrain-opt", f, f"F{_t(f)}", replicas=True, grilla="H4O") for f in TASAS_GRILLA],
        # D8: busca como `H4O-{f}` (comparte su estudio `F{f}`) y entrena el final con todo y sin peso, como H3
        *[Variante(f"H4P-{_t(f)}", "h4", "clase-peso", f, f"F{_t(f)}", replicas=True, grilla="H4P") for f in TASAS_GRILLA],
    ]
}

ESTUDIOS: dict[str, str] = {
    "C": CONTROL,
    **{f"U{_t(r)}": "h1" for r in TASAS_GRILLA},
    **{f"B{_t(f)}": "h2" for f in TASAS_GRILLA},
    "GOSS": "h2",
    "K0.1": "h3",
    "NH0.1": "h4",
    "NU0.1": "h4",
    **{f"F{_t(f)}": "h4" for f in TASAS_GRILLA},
}

#: Las cinco formas de muestrear de la grilla común (D8): clave de `Variante.grilla` -> cómo se muestrea. Cada fila tiene una
#: variante por tasa de `TASAS_GRILLA`.
FILAS_GRILLA: dict[str, str] = {
    "U": "al azar, búsqueda y final",
    "H3": "al azar, solo búsqueda",
    "H4O": "bajas y una fracción de CONTINUA con peso, búsqueda y final",
    "H4P": "bajas y una fracción de CONTINUA con peso, solo búsqueda",
    "B": "dentro de LightGBM, por árbol",
}

#: Celdas (fila, tasa) de la grilla que no se corren y por qué (D11). Hoy no hay ninguna: las 20 celdas tienen variante.
#: Una variante nueva que deje una celda vacía la declara acá antes de correr (`docs/metodo.md` § Agregar una hipótesis).
CELDAS_SIN_CORRER: dict[tuple[str, float], str] = {}

#: Variantes fuera de la grilla (cruces o extensiones de una forma), con lo que cruzan; la tabla de cobertura las lista aparte.
FUERA_DE_GRILLA: dict[str, str] = {
    "GOSS": "muestreo de gradientes dentro de LightGBM, sin tasa",
    "H3R-0.1": "búsqueda al azar con `min_data_in_leaf` reescalado con la raíz en el final",
    "H3R-0.25": "búsqueda al azar con `min_data_in_leaf` reescalado con la raíz en el final",
    "H3L-0.25": "búsqueda al azar con `min_data_in_leaf` reescalado linealmente en el final",
    "H3L-0.1": "búsqueda al azar con `min_data_in_leaf` reescalado linealmente en el final",
    "H3K-0.1": "búsqueda por cliente (todas las filas de los clientes sorteados)",
    "H4H-0.1": "búsqueda con bajas y CONTINUA difíciles, sin peso",
    "H4U-0.1": "búsqueda con bajas y CONTINUA al azar, sin peso",
    "H4F-0.05": "búsqueda al azar con final de las bajas y la mitad de las CONTINUA",
    "H4F-0.25": "búsqueda al azar con final de las bajas y la mitad de las CONTINUA",
}


def nombre(metodo: str, tasa: float) -> str:
    """Nombre de la variante de la grilla para `(método, tasa)`; no dice si está en el registro."""
    if metodo == "opt-muestra":
        return f"H3-{_t(tasa)}"
    if metodo == "opt-muestra-reescalado":
        return f"H3R-{_t(tasa)}"
    for m, prefijo in (("opt-muestra-lineal", "H3L"), ("opt-muestra-cliente", "H3K"), ("clase-dificil", "H4H"),
                       ("clase-uniforme", "H4U"), ("fast-retrain", "H4F"), ("fast-retrain-opt", "H4O"),
                       ("clase-peso", "H4P")):
        if metodo == m:
            return f"{prefijo}-{_t(tasa)}"
    if metodo == "uniforme":
        return "C" if tasa == 1 else f"U{_t(tasa)}"
    if metodo == "bagging":
        return f"B{_t(tasa)}"
    if metodo == "goss":
        return "GOSS"
    raise ValueError(f"método desconocido: {metodo!r}")


def variante(nombre_variante: str) -> Variante:
    """La variante del registro; falla nombrándolo si no está."""
    try:
        return VARIANTES[nombre_variante]
    except KeyError:
        raise ValueError(f"variante {nombre_variante!r} no está en el registro de comun/variantes.py "
                         f"(variantes: {', '.join(VARIANTES)})") from None


def partir_estudio(estudio: str) -> tuple[str, int]:
    """`U0.1@3` -> (`U0.1`, 3); sin `@k` es la réplica 0."""
    base, _, k = estudio.partition("@")
    if not k:
        return estudio, 0
    if not k.isdigit() or int(k) < 1:
        raise ValueError(f"estudio {estudio!r}: la réplica tiene que ser un entero ≥ 1 después de '@'")
    return base, int(k)


def nombre_estudio(estudio: str, replica: int = 0) -> str:
    """`<estudio>@k` para k ≥ 1; la réplica 0 conserva el nombre de siempre."""
    return estudio if replica == 0 else f"{estudio}@{replica}"


def validar_replica(nombre_variante: str, replica: int) -> None:
    """Falla nombrando la variante y la réplica si k < 0 o si k ≥ 1 y el registro no habilita réplicas de la variante."""
    if replica < 0:
        raise ValueError(f"réplica {replica} inválida para {nombre_variante}: tiene que ser ≥ 0")
    if replica and not variante(nombre_variante).replicas:
        raise ValueError(f"la variante {nombre_variante} no admite réplicas de optimización (pedida la réplica {replica}); "
                         f"las admiten: {', '.join(b.nombre for b in VARIANTES.values() if b.replicas)}")


def dueno_variante(nombre_variante: str, replica: int = 0) -> str:
    """Dueño de las filas de la variante, con o sin réplica: las réplicas k ≥ 1 de `U{r}` también son de `h1`."""
    return variante(nombre_variante).dueno


def dueno_estudio(estudio: str) -> str:
    """Dueño del estudio, el mismo con o sin réplica: `U{r}` y `U{r}@k` son de `h1`, `C@k` es de `control`."""
    base, k = partir_estudio(estudio)
    try:
        dueno = ESTUDIOS[base]
    except KeyError:
        raise ValueError(f"estudio {estudio!r} no está en el registro de comun/variantes.py "
                         f"(estudios: {', '.join(ESTUDIOS)})") from None
    if k and not any(b.replicas and b.estudio == base for b in VARIANTES.values()):
        raise ValueError(f"estudio {estudio!r}: el estudio {base} no admite réplicas de optimización")
    return dueno


def variantes_de(exp: str) -> list[Variante]:
    return [b for b in VARIANTES.values() if b.dueno == exp]


def duenos() -> list[str]:
    """Experimentos dueños de alguna variante, el control primero."""
    return sorted({b.dueno for b in VARIANTES.values()}, key=lambda e: (e != CONTROL, e))


# --- dependencias -----------------------------------------------------------------------------


def implicitas(variantes: dict[str, Variante] | None = None, estudios: dict[str, str] | None = None) -> dict[str, set[str]]:
    """De quién depende cada experimento según el registro: del control (finales de C, N*, δ), del dueño de cada
    estudio que usa y, el agregador, de todos."""
    variantes = VARIANTES if variantes is None else variantes
    estudios = ESTUDIOS if estudios is None else estudios
    dueños = {b.dueno for b in variantes.values()}
    dep: dict[str, set[str]] = {e: set() for e in dueños}
    for b in variantes.values():
        if b.dueno != CONTROL:
            dep[b.dueno].add(CONTROL)
        dueno_est = estudios[b.estudio]
        if dueno_est != b.dueno:
            dep[b.dueno].add(dueno_est)
    dep[AGREGADOR] = set(dueños)
    return dep


def declaradas(raiz: Path, conocidos: Iterable[str]) -> dict[str, set[str] | None]:
    """Lo que declara la sección `## Dependencias` de cada `experimentos/*/docs/diseno.md` (None si falta el archivo
    o la sección). Cuenta cada nombre de experimento entre comillas invertidas."""
    conocidos = set(conocidos)
    out: dict[str, set[str] | None] = {}
    base = raiz / "experimentos"
    for diseno in sorted(base.glob("*/docs/diseno.md")):
        exp = diseno.parents[1].name
        m = re.search(r"^## Dependencias[^\n]*\n(.*?)(?=^## |\Z)", diseno.read_text(), re.S | re.M)
        out[exp] = None if m is None else {n for n in re.findall(r"`([^`\n]+)`", m.group(1)) if n in conocidos}
    return out


def ciclos(grafo: dict[str, set[str]]) -> list[list[str]]:
    """Ciclos del grafo `experimento -> dependencias`, cada uno como lista que vuelve al primer nodo."""
    encontrados: list[list[str]] = []
    visto: set[str] = set()

    def visitar(nodo: str, camino: list[str]) -> None:
        if nodo in camino:
            ciclo = camino[camino.index(nodo):] + [nodo]
            if not any(set(ciclo) == set(c) for c in encontrados):
                encontrados.append(ciclo)
            return
        if nodo in visto:
            return
        for sig in sorted(grafo.get(nodo, ())):
            visitar(sig, camino + [nodo])
        visto.add(nodo)

    for n in sorted(grafo):
        visitar(n, [])
    return encontrados


def rotos_si_falta(grafo: dict[str, set[str]], exp: str) -> list[str]:
    """Experimentos que dejan de andar si falta la carpeta `exp`: los que lo declaran, directa o indirectamente."""
    rotos: set[str] = set()
    pendientes = [exp]
    while pendientes:
        actual = pendientes.pop()
        for otro, deps in grafo.items():
            if actual in deps and otro not in rotos and otro != exp:
                rotos.add(otro)
                pendientes.append(otro)
    return sorted(rotos)


CAMPOS_EXPLORATORIO = ("autor", "fecha", "pregunta", "protocolo", "advertencia", "tablas")


def manifiestos(raiz: Path = rutas.RAIZ) -> list[Path]:
    """Los `exploratorio.json` de `experimentos/*/` (a cualquier profundidad) y de `sampling_1/exploratorios/*/`."""
    return sorted((raiz / "experimentos").glob("**/exploratorio.json"))


def problemas_exploratorios(raiz: Path = rutas.RAIZ) -> list[str]:
    """Carpeta y campo que faltan o están vacíos en cada manifiesto de exploratorio."""
    out: list[str] = []
    for m in manifiestos(raiz):
        carpeta = m.parent.relative_to(raiz)
        try:
            datos = json.loads(m.read_text())
        except ValueError as e:
            out.append(f"{carpeta}: exploratorio.json no es JSON válido ({e})")
            continue
        for campo in CAMPOS_EXPLORATORIO:
            if not datos.get(campo):
                out.append(f"{carpeta}: a exploratorio.json le falta el campo `{campo}`")
        for t in datos.get("tablas") or []:
            if not isinstance(t, dict) or not t.get("csv") or not t.get("columnas"):
                out.append(f"{carpeta}: cada tabla de exploratorio.json necesita `csv` y `columnas`")
        if not (m.parent / "README.md").is_file():
            out.append(f"{carpeta}: falta README.md junto al exploratorio.json")
    return out


def verificar(raiz: Path = rutas.RAIZ, variantes: dict[str, Variante] | None = None,
              estudios: dict[str, str] | None = None) -> tuple[list[str], list[str]]:
    """(problemas, informe). Problemas: carpeta o sección que falta, declaración distinta de la implícita, ciclos."""
    implicito = implicitas(variantes, estudios)
    conocidos = set(implicito) | {p.name for p in (raiz / "experimentos").glob("*") if p.is_dir()}
    declarado = declaradas(raiz, conocidos)
    problemas: list[str] = []
    for exp in sorted(implicito):
        if not (raiz / "experimentos" / exp).is_dir():
            problemas.append(f"falta la carpeta experimentos/{exp}/ (la usa el registro de variantes)")
        elif declarado.get(exp) is None:
            problemas.append(f"{exp}: falta la sección `## Dependencias` en docs/diseno.md")
        elif declarado[exp] != implicito[exp]:
            falta, sobra = sorted(implicito[exp] - declarado[exp]), sorted(declarado[exp] - implicito[exp])
            problemas.append(f"{exp}: `## Dependencias` no coincide con el registro"
                             + (f"; falta declarar {falta}" if falta else "") + (f"; declara de más {sobra}" if sobra else ""))
    grafo = {e: set(d or ()) for e, d in declarado.items()}
    for e, d in implicito.items():
        grafo.setdefault(e, set())
    for ciclo in ciclos(grafo):
        problemas.append("ciclo de dependencias: " + " -> ".join(ciclo))
    problemas += problemas_exploratorios(raiz)
    informe = []
    for exp in sorted(set(grafo) | set(implicito)):
        rotos = rotos_si_falta({e: (declarado.get(e) or set()) | implicito.get(e, set()) for e in grafo | implicito}, exp)
        informe.append(f"si falta experimentos/{exp}/ se rompen: {', '.join(rotos) if rotos else '(ninguno)'}")
    return problemas, informe


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--verificar", action="store_true", help="compara `## Dependencias`, busca ciclos y lista qué se rompe")
    a = p.parse_args()
    if not a.verificar:
        for b in VARIANTES.values():
            print(f"{b.nombre:8} dueño={b.dueno:8} método={b.metodo:11} tasa={b.tasa:g} estudio={b.estudio} "
                  f"(de {ESTUDIOS[b.estudio]})")
        return
    problemas, informe = verificar()
    print("\n".join(informe))
    for pr in problemas:
        print("PROBLEMA", pr)
    raise SystemExit(1 if problemas else 0)


if __name__ == "__main__":
    main()
