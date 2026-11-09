"""Registro único de variantes y estudios: quién es dueño de qué, y de quién depende cada experimento.

    python -m comun.variantes --verificar

De acá salen el nombre de la variante y del estudio de cada `(método, tasa)`, el ledger al que va cada fila y las
dependencias implícitas entre experimentos. `## Dependencias` de cada `docs/diseno.md` las escribe una persona y
`--verificar` las compara con lo que implica el registro (`openspec/specs/dependencias-entre-experimentos`).
"""

from __future__ import annotations

import argparse
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


def _t(tasa: float) -> str:
    return f"{tasa:g}"


VARIANTES: dict[str, Variante] = {
    b.nombre: b
    for b in [
        Variante("C", CONTROL, "uniforme", 1.0, "C", replicas=True),
        Variante("C-rep", CONTROL, "uniforme", 1.0, "C"),
        *[Variante(f"U{_t(r)}", "h1", "uniforme", r, f"U{_t(r)}") for r in (0.5, 0.25, 0.1, 0.05)],
        *[Variante(f"B{_t(f)}", "h2", "bagging", f, f"B{_t(f)}") for f in (0.5, 0.25, 0.1)],
        Variante("GOSS", "h2", "goss", 1.0, "GOSS"),
        *[Variante(f"H3-{_t(r)}", "h3", "opt-muestra", r, f"U{_t(r)}", replicas=True) for r in (0.25, 0.1, 0.05)],
        Variante("H3R-0.1", "h3", "opt-muestra-reescalado", 0.1, "U0.1", replicas=True),
    ]
}

ESTUDIOS: dict[str, str] = {
    "C": CONTROL,
    **{f"U{_t(r)}": "h1" for r in (0.5, 0.25, 0.1, 0.05)},
    **{f"B{_t(f)}": "h2" for f in (0.5, 0.25, 0.1)},
    "GOSS": "h2",
}


def nombre(metodo: str, tasa: float) -> str:
    """Nombre de la variante de la grilla para `(método, tasa)`; no dice si está en el registro."""
    if metodo == "opt-muestra":
        return f"H3-{_t(tasa)}"
    if metodo == "opt-muestra-reescalado":
        return f"H3R-{_t(tasa)}"
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
    """Dueño de las filas de la variante. Las réplicas k ≥ 1 de las optimizaciones `U{r}` son de `h3`, no de `h1`."""
    dueno = variante(nombre_variante).dueno
    return "h3" if replica and dueno == "h1" else dueno


def dueno_estudio(estudio: str) -> str:
    """Dueño del estudio. `U{r}` es de `h1`, sus réplicas `U{r}@k` son de `h3`; `C@k` es de `control`."""
    base, k = partir_estudio(estudio)
    try:
        dueno = ESTUDIOS[base]
    except KeyError:
        raise ValueError(f"estudio {estudio!r} no está en el registro de comun/variantes.py "
                         f"(estudios: {', '.join(ESTUDIOS)})") from None
    if k and not any(b.replicas and b.estudio == base for b in VARIANTES.values()):
        raise ValueError(f"estudio {estudio!r}: el estudio {base} no admite réplicas de optimización")
    return "h3" if k and dueno == "h1" else dueno


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
