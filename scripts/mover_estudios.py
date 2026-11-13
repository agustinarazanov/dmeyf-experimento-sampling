"""Mueve de `h3` a `h1` los estudios `U{r}@k` (cambio `tiempos-confiables-y-consistencia`, D10). Se corre una vez.

    python -m scripts.mover_estudios --en-seco             # el reparto del repo, sin tocar nada
    python -m scripts.mover_estudios                       # lo mueve en el repo
    python -m scripts.mover_estudios --bucket --en-seco    # los cinco pasos del bucket, impresos
    python -m scripts.mover_estudios --bucket              # los corre (sin ninguna VM viva en el proyecto)
    python -m scripts.mover_estudios --deshacer [--bucket] # vuelve atrás: el repo, o el bucket desde el respaldo

Qué se mueve: de `experimentos/h3/ledger` al ledger del dueño que fija `comun/variantes.py`, el `hp/<estudio>.json`, los
archivos de `corridas/`, `curvas/` y `predicciones/` de las variantes de otro dueño y sus filas de `resultados.csv`,
`estudios.csv` y `reemplazadas.csv`, sin cambiar ids ni contenido. No mueve `exploracion/`. Con `--deshacer` rige la regla
vieja (las réplicas k ≥ 1 de `U{r}` eran de `h3`) y se mueve de `h1` a `h3`.

Bucket (D10), en este orden: 1 ninguna VM viva; 2 respaldo de `h1/ledger` y `h3/ledger` en `$BUCKET/respaldo/2026-11-mover-U/`
(que `vm.sh` no sincroniza); 3 copiar cada archivo a su carpeta nueva y comparar tamaño y crc32c; 4 borrar el original;
5 verificar. En el bucket solo viajan `hp/`, `corridas/`, `curvas/` y `predicciones/`: los CSV de la raíz se arman acá.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from comun import rutas, variantes

ORIGEN = "h3"
TABLAS = ("resultados", "estudios", "reemplazadas")
CARPETAS = ("corridas", "curvas", "predicciones")
RESPALDO = "respaldo/2026-11-mover-U"
FILTROS_VM = r"^(exploracion|sesiones)/|^[^/]*\.csv$"  # los de `scripts/vm.sh` al subir


# --- quién es dueño de qué -----------------------------------------------------------------------


def dueno_nuevo_variante(nombre: str) -> str:
    return variantes.dueno_variante(variantes.partir_estudio(nombre)[0])


def dueno_viejo_variante(nombre: str) -> str:
    """Regla anterior a D10: las réplicas k ≥ 1 de las variantes de `h1` eran de `h3`."""
    base, k = variantes.partir_estudio(nombre)
    d = variantes.dueno_variante(base)
    return "h3" if k and d == "h1" else d


def dueno_nuevo_estudio(nombre: str) -> str:
    return variantes.dueno_estudio(nombre)


def dueno_viejo_estudio(nombre: str) -> str:
    base, k = variantes.partir_estudio(nombre)
    d = variantes.ESTUDIOS[base]
    return "h3" if k and d == "h1" else d


def _variante_de_archivo(nombre: str) -> str:
    """Lo que va antes del primer `_` del nombre (los ids son `<variante>_<método>_<tasa>_...`)."""
    return nombre.split("_", 1)[0]


# --- plan ----------------------------------------------------------------------------------------


def planificar(origen: str, deshacer: bool = False, raiz: Path | None = None) -> dict:
    """Qué sale de `origen`: `{'hp': {archivo: destino}, carpeta: {archivo: destino}, tabla: {destino: DataFrame}}`.
    Solo se mueve lo que la regla (nueva, o vieja con `deshacer`) asigna a otro dueño."""
    led = (lambda e: raiz / "experimentos" / e / "ledger") if raiz else rutas.ledger
    d_var = dueno_viejo_variante if deshacer else dueno_nuevo_variante
    d_est = dueno_viejo_estudio if deshacer else dueno_nuevo_estudio
    base = led(origen)
    plan: dict = {"hp": {}, "tablas": {}, **{c: {} for c in CARPETAS}}
    if (base / "hp").is_dir():
        for p in sorted((base / "hp").glob("*.json")):
            if d_est(p.stem) != origen:
                plan["hp"][p.name] = d_est(p.stem)
    for c in CARPETAS:
        if (base / c).is_dir():
            for p in sorted(x for x in (base / c).iterdir() if x.is_file()):
                d = d_var(_variante_de_archivo(p.name))
                if d != origen:
                    plan[c][p.name] = d
    for t in TABLAS:
        f = base / f"{t}.csv"
        if not f.exists():
            continue
        tabla = pd.read_csv(f, dtype=str, keep_default_na=False)
        # el nombre de variante de una fila no lleva `@k`: la réplica sale de `replica_opt` (columna vacía = réplica 0)
        replica = tabla["replica_opt"].replace("", "0").astype(int) if "replica_opt" in tabla else pd.Series(0, index=tabla.index)
        duenos = pd.Series([d_var(v if not k else f"{v}@{k}") for v, k in zip(tabla["variante"], replica)], index=tabla.index)
        for exp, parte in tabla.groupby(duenos, sort=True):
            if exp != origen:
                plan["tablas"].setdefault(t, {})[exp] = parte
    return plan


def resumen(plan: dict) -> list[str]:
    out = [f"hp/: {len(plan['hp'])} archivos"] + [f"{c}/: {len(plan[c])} archivos" for c in CARPETAS]
    for t, por in plan["tablas"].items():
        out.append(f"{t}.csv: " + ", ".join(f"{len(p)} filas -> {e}" for e, p in por.items()))
    destinos = sorted({d for sec in ("hp", *CARPETAS) for d in plan[sec].values()})
    out.append("destinos: " + (", ".join(destinos) or "(ninguno)"))
    return out


def mover_repo(origen: str, deshacer: bool = False, raiz: Path | None = None) -> dict:
    """Mueve archivos y filas en el repo. No pisa nada: un archivo que ya existe en el destino falla sin mover."""
    led = (lambda e: raiz / "experimentos" / e / "ledger") if raiz else rutas.ledger
    plan = planificar(origen, deshacer, raiz)
    for sec in ("hp", *CARPETAS):
        for nombre, dest in plan[sec].items():
            if (led(dest) / sec / nombre).exists():
                raise FileExistsError(f"{led(dest) / sec / nombre} ya existe: no se pisa")
    for sec in ("hp", *CARPETAS):
        for nombre, dest in plan[sec].items():
            (led(dest) / sec).mkdir(parents=True, exist_ok=True)
            shutil.move(led(origen) / sec / nombre, led(dest) / sec / nombre)
    for t, por in plan["tablas"].items():
        ids_movidos = {i for p in por.values() for i in p["id"]}
        fo = led(origen) / f"{t}.csv"
        tabla = pd.read_csv(fo, dtype=str, keep_default_na=False)
        tabla[~tabla["id"].isin(ids_movidos)].to_csv(fo, index=False)
        for dest, parte in por.items():
            fd = led(dest) / f"{t}.csv"
            previa = pd.read_csv(fd, dtype=str, keep_default_na=False) if fd.exists() else parte.iloc[:0]
            if set(previa["id"]) & set(parte["id"]):
                raise ValueError(f"{fd}: ya tiene ids que se iban a mover")
            pd.concat([previa, parte[previa.columns]], ignore_index=True).to_csv(fd, index=False)
    return plan


# --- bucket --------------------------------------------------------------------------------------


def _env() -> dict[str, str]:
    """PROYECTO y BUCKET del entorno o de `.env` (el mismo que lee `scripts/vm.sh`)."""
    out = {k: os.environ[k] for k in ("PROYECTO", "BUCKET") if k in os.environ}
    f = rutas.RAIZ / ".env"
    if f.exists():
        for linea in f.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?(PROYECTO|BUCKET)=(.*)", linea)
            if m and m.group(1) not in out:
                out[m.group(1)] = m.group(2).strip().strip("'\"")
    return out


class Bucket:
    def __init__(self, bucket: str, proyecto: str, en_seco: bool):
        self.bucket, self.proyecto, self.en_seco = bucket.rstrip("/"), proyecto, en_seco

    def correr(self, *cmd: str, ok_si_falla: bool = False) -> str:
        print("  $", " ".join(cmd), flush=True)
        if self.en_seco:
            return ""
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode and not ok_si_falla:
            raise RuntimeError(f"falló {' '.join(cmd)}:\n{r.stderr[-2000:]}")
        return r.stdout

    def listar(self, exp: str, sec: str) -> list[str]:
        """Nombres de los archivos de `sec/` del ledger de `exp` en el bucket (lectura: corre también en seco)."""
        r = subprocess.run(["gsutil", "ls", self.url(exp, sec)], capture_output=True, text=True)
        return sorted(x.rsplit("/", 1)[1] for x in r.stdout.splitlines() if x and not x.endswith("/"))

    def url(self, exp: str, sec: str, nombre: str = "") -> str:
        return f"{self.bucket}/experimentos/{exp}/ledger/{sec}/{nombre}"

    def vms_vivas(self) -> list[str]:
        """Paso 1. En seco solo imprime el comando."""
        if self.en_seco:
            self.correr("gcloud", "compute", "instances", "list", f"--project={self.proyecto}", "--format=value(name,status)")
            return []
        out = subprocess.run(["gcloud", "compute", "instances", "list", f"--project={self.proyecto}",
                              "--format=value(name,status)"], capture_output=True, text=True, check=True).stdout
        return [x for x in out.splitlines() if x.strip()]

    def huellas(self, urls: list[str]) -> dict[str, tuple[str, str]]:
        """`{url: (tamaño, crc32c)}` de `gsutil ls -L`."""
        out: dict[str, tuple[str, str]] = {}
        for i in range(0, len(urls), 100):
            txt = subprocess.run(["gsutil", "ls", "-L", *urls[i:i + 100]], capture_output=True, text=True).stdout
            for bloque in re.split(r"\n(?=gs://)", txt):
                m = re.match(r"(gs://\S+?):", bloque)
                tam = re.search(r"Content-Length:\s+(\d+)", bloque)
                crc = re.search(r"Hash \(crc32c\):\s+(\S+)", bloque)
                if m and tam and crc:
                    out[m.group(1)] = (tam.group(1), crc.group(1))
        return out


def plan_bucket(b: Bucket, origen: str) -> dict:
    """Lo que hay que mover en el bucket, listado del propio bucket: el repo ya se movió antes y no sirve de fuente."""
    plan: dict = {"hp": {}, **{c: {} for c in CARPETAS}}
    for sec in plan:
        for n in b.listar(origen, sec):
            d = dueno_nuevo_estudio(Path(n).stem) if sec == "hp" else dueno_nuevo_variante(_variante_de_archivo(n))
            if d != origen:
                plan[sec][n] = d
    return plan


def comparar_nombres(b: Bucket, exp: str) -> tuple[list[str], list[str]]:
    """(solo en el bucket, solo en el repo) de `experimentos/<exp>/ledger/`, con los filtros de `vm.sh`. Compara nombres y no
    fechas: `rsync -n` marca todo como distinto porque el checkout del repo cambia el mtime."""
    base = b.url(exp, "").rstrip("/") + "/"
    out = subprocess.run(["gsutil", "ls", "-r", base + "**"], capture_output=True, text=True).stdout.splitlines()
    en_b = {x[len(base):] for x in out if x.startswith(base) and not x.endswith(("/", ":"))}
    led = rutas.ledger(exp)
    en_r = {str(p.relative_to(led)) for p in led.rglob("*") if p.is_file() and p.name != ".DS_Store"}
    filtro = re.compile(FILTROS_VM)
    en_b, en_r = {x for x in en_b if not filtro.match(x)}, {x for x in en_r if not filtro.match(x)}
    return sorted(en_b - en_r), sorted(en_r - en_b)


def pasos_bucket(origen: str, en_seco: bool, deshacer: bool = False) -> list[str]:
    """Los cinco pasos de D10. Devuelve el listado de lo movido (una línea por archivo) para la bitácora."""
    env = _env()
    if not en_seco and not {"PROYECTO", "BUCKET"} <= set(env):
        raise SystemExit("faltan PROYECTO o BUCKET (entorno o .env)")
    b = Bucket(env.get("BUCKET", "<BUCKET>"), env.get("PROYECTO", "<PROYECTO>"), en_seco)
    if deshacer:
        return _deshacer_bucket(b, en_seco)
    plan = plan_bucket(b, origen) if not en_seco or "BUCKET" in env else {"hp": {}, **{c: {} for c in CARPETAS}}
    mov = [(sec, n, d) for sec in ("hp", *CARPETAS) for n, d in plan[sec].items()]
    print(f"== bucket {b.bucket}: {len(mov)} archivos de {origen}")
    print("== paso 1: ninguna VM viva")
    vivas = b.vms_vivas()
    if vivas:
        raise SystemExit("hay VMs vivas en el proyecto, no se mueve nada: " + "; ".join(vivas))
    print("== paso 2: respaldo (el listado queda en el resultado)")
    for e in sorted({origen, *(d for _, _, d in mov)}):
        b.correr("gsutil", "-q", "-m", "rsync", "-r", b.url(e, "").rstrip("/"), f"{b.bucket}/{RESPALDO}/{e}/ledger")
    urls_o = [b.url(origen, s, n) for s, n, _ in mov]
    urls_d = [b.url(d, s, n) for s, n, d in mov]
    print("== paso 3: copiar y comparar tamaño y crc32c")
    for uo, ud in zip(urls_o, urls_d):
        b.correr("gsutil", "-q", "cp", "-n", uo, ud)
    h_o = b.huellas(urls_o) if not en_seco else {}
    h_d = b.huellas(urls_d) if not en_seco else {}
    if not en_seco:
        malos = [uo for uo, ud in zip(urls_o, urls_d) if h_o.get(uo) is None or h_o.get(uo) != h_d.get(ud)]
        if malos:
            raise SystemExit(f"tamaño o crc32c distintos (o sin huella) en {len(malos)} archivos, no se borra nada: {malos[:3]}")
    print("== paso 4: borrar los originales")
    for uo in urls_o:
        b.correr("gsutil", "-q", "rm", uo)
    print("== paso 5: verificar")
    if not en_seco:
        quedan = subprocess.run(["gsutil", "ls", f"{b.bucket}/experimentos/{origen}/ledger/*/U*@*"], capture_output=True, text=True).stdout
        if quedan.strip():
            raise SystemExit("quedan U*@k en el origen del bucket:\n" + quedan)
        resp = b.huellas([f"{b.bucket}/{RESPALDO}/{origen}/ledger/{s}/{n}" for s, n, _ in mov])
        h_n = b.huellas(urls_d)
        malos = [ud for (s, n, _), ud in zip(mov, urls_d)
                 if resp.get(f"{b.bucket}/{RESPALDO}/{origen}/ledger/{s}/{n}") != h_n.get(ud)]
        if malos:
            raise SystemExit(f"destino con crc32c distinto del respaldo: {malos[:3]}")
        print(f"  {len(mov)} archivos en su carpeta nueva con el crc32c del respaldo; ningún U*@k en {origen}/")
        for e in sorted({origen, *(d for _, _, d in mov)}):
            solo_b, solo_r = comparar_nombres(b, e)
            print(f"  {e}: {len(solo_b)} archivos solo en el bucket, {len(solo_r)} solo en el repo (mismos filtros que vm.sh)"
                  + "".join(f"\n    solo bucket: {x}" for x in solo_b[:10]) + "".join(f"\n    solo repo: {x}" for x in solo_r[:10]))
    else:
        b.correr("gsutil", "ls", f"{b.bucket}/experimentos/{origen}/ledger/*/U*@*")
        print("  (compara los nombres de archivo del bucket y del repo, con los filtros de vm.sh)")
    return [f"{s}/{n}: {origen} -> {d}" for s, n, d in mov]


def _deshacer_bucket(b: Bucket, en_seco: bool) -> list[str]:
    """Restaura `h1/ledger` y `h3/ledger` del bucket desde el respaldo (con `-d`: lo que no está en el respaldo se borra)."""
    print("== paso 1: ninguna VM viva")
    vivas = b.vms_vivas()
    if vivas:
        raise SystemExit("hay VMs vivas en el proyecto, no se restaura nada: " + "; ".join(vivas))
    for e in ("h1", "h3"):
        b.correr("gsutil", "-q", "-m", "rsync", "-r", "-d", f"{b.bucket}/{RESPALDO}/{e}/ledger", b.url(e, "").rstrip("/"))
    return []


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--en-seco", action="store_true", help="imprime lo que haría sin tocar nada")
    p.add_argument("--bucket", action="store_true", help="la mudanza en el bucket (cinco pasos) en vez de en el repo")
    p.add_argument("--comparar", action="store_true", help="solo compara los nombres de archivo del bucket y del repo")
    p.add_argument("--deshacer", action="store_true", help="vuelve atrás (regla vieja, de h1 a h3, o respaldo del bucket)")
    a = p.parse_args()
    origen = "h1" if a.deshacer else ORIGEN
    if a.comparar:
        env = _env()
        b = Bucket(env["BUCKET"], env["PROYECTO"], False)
        for e in sorted(variantes.duenos()):
            solo_b, solo_r = comparar_nombres(b, e)
            print(f"{e}: solo bucket {len(solo_b)} {solo_b[:3]}; solo repo {len(solo_r)} {solo_r[:3]}")
        sys.exit(0)
    if a.bucket:
        print("\n".join(pasos_bucket(ORIGEN, a.en_seco, a.deshacer)))
        sys.exit(0)
    plan = planificar(origen, a.deshacer)
    print("\n".join(resumen(plan)))
    if not a.en_seco:
        mover_repo(origen, a.deshacer)
        print("movido")
    sys.exit(0)


if __name__ == "__main__":
    main()
