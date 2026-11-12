"""Huellas por columna del panel nuevo (con 201907) contra el panel viejo (D2): 201903-201906, 201908 y 201910 no cambian.

    python scripts/huellas_panel_201907.py NUEVO.parquet VIEJO.parquet

Compara solo los clientes del panel nuevo (el smoke se queda con un subconjunto por hash del id) y las filas de los meses
que ya estaban en el panel viejo. Una huella por columna y mes: sha256 de los valores ordenados por cliente, con un solo
patrón de NaN. Sale con 0 solo si todas coinciden y 201907 está en el nuevo.
"""
import hashlib
import sys

import duckdb
import numpy as np

MESES = [201903, 201904, 201905, 201906, 201908, 201910]


def huella(v: np.ndarray) -> str:
    if v.dtype == object:
        return hashlib.sha256("\n".join(map(str, v)).encode()).hexdigest()
    v = np.where(np.isnan(v), np.float32("nan"), v) if v.dtype.kind == "f" else v
    return hashlib.sha256(v.tobytes()).hexdigest()


def main(nuevo: str, viejo: str) -> int:
    con = duckdb.connect()
    meses_nuevo = {r[0] for r in con.execute(f"select distinct foto_mes from read_parquet('{nuevo}')").fetchall()}
    cols_n = [r[0] for r in con.execute(f"describe select * from read_parquet('{nuevo}')").fetchall()]
    cols_v = [r[0] for r in con.execute(f"describe select * from read_parquet('{viejo}')").fetchall()]
    lista = ", ".join(str(m) for m in MESES)
    dn = con.execute(
        f"select * from read_parquet('{nuevo}') where foto_mes in ({lista}) order by foto_mes, numero_de_cliente").df()
    dv = con.execute(
        f"select v.* from read_parquet('{viejo}') v semi join read_parquet('{nuevo}') n "
        f"on v.numero_de_cliente = n.numero_de_cliente where v.foto_mes in ({lista}) "
        f"order by v.foto_mes, v.numero_de_cliente").df()
    malas = []
    if 201907 not in meses_nuevo:
        malas.append("el panel nuevo no tiene 201907")
    if cols_n != cols_v:
        malas.append(f"columnas distintas: solo nuevo {sorted(set(cols_n) - set(cols_v))[:5]}, "
                     f"solo viejo {sorted(set(cols_v) - set(cols_n))[:5]}")
    if len(dn) != len(dv):
        malas.append(f"filas distintas: {len(dn)} contra {len(dv)}")
    else:
        for c in cols_n:
            if c in dv.columns and huella(dn[c].to_numpy()) != huella(dv[c].to_numpy()):
                malas.append(f"columna distinta: {c}")
    print(f"{len(cols_n)} columnas, {len(dn)} filas de {lista}; 201907 en el nuevo: {201907 in meses_nuevo}; "
          f"{len(malas)} diferencias")
    for m in malas[:20]:
        print(m)
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
