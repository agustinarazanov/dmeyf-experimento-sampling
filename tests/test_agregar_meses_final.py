"""`scripts/agregar_meses_final.py` sobre un ledger de juguete."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agregar_meses_final", RAIZ / "scripts" / "agregar_meses_final.py")
amf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amf)

CABECERA = "id,etapa_corrida,estudio,hp,valida\n"
FILAS = 'a,final,C,"{""num_leaves"": 8, ""lr"": 0.1}",True\nb,optimizar,C,{},True\n'


def _ledger(base: Path) -> Path:
    led = base / "h1" / "ledger"
    (led / "corridas").mkdir(parents=True)
    (led / "corridas" / "a.csv").write_text(CABECERA + FILAS)
    (led / "sesiones").mkdir()
    (led / "sesiones" / "otro.csv").write_text(CABECERA + FILAS)
    (led / "curva.csv").write_text("envios,ganancia\n1,2\n")
    return base


def test_agrega_la_columna_solo_a_los_finales_y_verifica(tmp_path):
    raiz, resp = _ledger(tmp_path / "x"), tmp_path / "respaldo"
    assert amf.aplicar(raiz, resp) == 0
    nuevo = (raiz / "h1" / "ledger" / "corridas" / "a.csv").read_text().splitlines()
    assert nuevo[0] == "id,etapa_corrida,estudio,meses_final,hp,valida"
    assert nuevo[1].startswith("a,final,C,201903-201906,") and nuevo[2].startswith("b,optimizar,C,,")
    assert (raiz / "h1" / "ledger" / "sesiones" / "otro.csv").read_text() == CABECERA + FILAS
    assert (raiz / "h1" / "ledger" / "curva.csv").read_text() == "envios,ganancia\n1,2\n"
    assert amf.verificar(raiz, resp) == 0
    assert amf.aplicar(raiz, resp) == 0  # idempotente: no reescribe lo que ya tiene la columna
    assert amf.verificar(raiz, resp) == 0


def test_verificar_detecta_un_cambio_en_el_resto(tmp_path):
    raiz, resp = _ledger(tmp_path / "x"), tmp_path / "respaldo"
    amf.aplicar(raiz, resp)
    p = raiz / "h1" / "ledger" / "corridas" / "a.csv"
    p.write_text(p.read_text().replace("True", "False", 1))
    assert amf.verificar(raiz, resp) == 1
