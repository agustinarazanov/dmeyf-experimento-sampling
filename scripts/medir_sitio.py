"""Mide el sitio construido (site/) en Chrome headless: desborde a 390 px, ancho único a 1440 px y alto de figuras y
tablas de Resultados. Lo usan las tareas de inicio-y-resultados (D6, D12, D16) y la sesión del orquestador.

uso:  mkdocs build  &&  python -m scripts.medir_sitio [--sitio site] [--alto-max 800] [--pagina experimentos/h3/ ...]

Sale con código 1 si algo no pasa. Imprime una línea por página y por problema; nada más.
"""
import argparse
import functools
import http.server
import json
import pathlib
import socketserver
import subprocess
import sys
import tempfile
import threading

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RESULTADOS = "experimentos/sampling_1/"

# Corre dentro de la página medida (en un iframe del ancho pedido) y devuelve un objeto con lo medido.
MEDIR_JS = r"""
(d, ancho) => {
  const W = d.documentElement.clientWidth;
  const r = {desborde: d.documentElement.scrollWidth - W, columna: null, anchos: [], altos: []};
  const col = d.querySelector('.md-content__inner');
  if (!col) return r;
  const cs = getComputedStyle(col);
  const cw = col.getBoundingClientRect().width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  r.columna = Math.round(cw);
  const sel = 'article > p, article > pre, article > .highlight, article > .admonition, article > details,' +
              'article > p > img, article > p > a > img, article .mermaid svg, article > .md-typeset__scrollwrap table,' +
              'article > .tabbed-set';
  for (const e of d.querySelectorAll(sel)) {
    const b = e.getBoundingClientRect();
    if (b.width === 0) continue;
    const nombre = e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '');
    // Párrafos y tablas pueden ser más angostos que la columna; nada puede ser más ancho.
    const angosto_ok = e.tagName === 'P' || e.tagName === 'TABLE';
    if (b.width - cw > 2 || (!angosto_ok && cw - b.width > 2)) r.anchos.push([nombre, Math.round(b.width)]);
    if (/img|svg|table|tabbed/.test(nombre)) r.altos.push([nombre, Math.round(b.height), (e.getAttribute('alt') || e.textContent || '').trim().slice(0, 50)]);
  }
  return r;
}
"""

ARNES = """<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">
<pre id="o"></pre><script>
const medir = {js};
const pags = {pags}, anchos = [390, 1440], out = {{}};
let falta = pags.length * anchos.length;
for (const p of pags) for (const a of anchos) {{
  const f = document.createElement('iframe');
  f.style = `width:${{a}}px;height:900px;border:0`;
  f.src = '/' + p;
  f.onload = () => setTimeout(() => {{
    try {{ out[p + '@' + a] = medir(f.contentDocument, a); }} catch (e) {{ out[p + '@' + a] = {{error: String(e)}}; }}
    if (--falta === 0) document.getElementById('o').textContent = JSON.stringify(out);
  }}, 1500);
  document.body.appendChild(f);
}}
</script></body></html>"""


def paginas(sitio: pathlib.Path) -> list[str]:
    return sorted(
        str(p.parent.relative_to(sitio)).replace(".", "") + "/" if p.parent != sitio else ""
        for p in sitio.rglob("index.html")
        if "assets" not in p.parts and "search" not in p.parts
    )


def medir(sitio: pathlib.Path, pags: list[str]) -> dict:
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    manejador = functools.partial(Silencioso, directory=str(sitio))
    with socketserver.TCPServer(("127.0.0.1", 0), manejador) as srv:
        puerto = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with tempfile.NamedTemporaryFile("w", suffix=".html", dir=sitio, delete=False, encoding="utf-8") as f:
            f.write(ARNES.format(js=MEDIR_JS, pags=json.dumps([p.lstrip("/") for p in pags])))
            arnes = pathlib.Path(f.name)
        try:
            salida = subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=30000", "--dump-dom",
                 f"http://127.0.0.1:{puerto}/{arnes.name}"],
                capture_output=True, text=True, timeout=180,
            ).stdout
        finally:
            arnes.unlink()
            srv.shutdown()
    ini, fin = salida.find('<pre id="o">'), salida.find("</pre>")
    texto = salida[ini + len('<pre id="o">'):fin]
    import html
    return json.loads(html.unescape(texto)) if texto.strip() else {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sitio", default="site")
    ap.add_argument("--alto-max", type=int, default=800, help="alto máximo de figuras y tablas en Resultados (D16)")
    ap.add_argument("--pagina", nargs="*", help="páginas a medir (por defecto, todas)")
    a = ap.parse_args()
    sitio = pathlib.Path(a.sitio)
    if not (sitio / "index.html").exists():
        print(f"no existe {sitio}/index.html: corré mkdocs build antes")
        return 1
    pags = a.pagina or paginas(sitio)
    res = medir(sitio, pags)
    if not res:
        print("Chrome no devolvió mediciones")
        return 1
    problemas = 0
    for p in pags:
        tel, esc = res.get(p.lstrip("/") + "@390", {}), res.get(p.lstrip("/") + "@1440", {})
        malos, avisos = [], []
        if tel.get("error") or esc.get("error"):
            malos.append(f"error: {tel.get('error') or esc.get('error')}")
        if tel.get("desborde", 0) > 0:
            malos.append(f"a 390 px desborda {tel['desborde']} px")
        for nombre, w in esc.get("anchos", []):
            texto = f"a 1440 px {nombre} mide {w} px (columna {esc.get('columna')})"
            # Una tabla más ancha se desplaza dentro de su recuadro (D6): se avisa, no falla.
            (avisos if nombre == "table" else malos).append(texto)
        if p.lstrip("/") == RESULTADOS:
            for nombre, h, txt in esc.get("altos", []):
                if h > a.alto_max:
                    malos.append(f"en Resultados {nombre} mide {h} px de alto (> {a.alto_max}): {txt}")
        print(f"{'ok ' if not malos else 'MAL'} /{p.lstrip('/')}  columna {esc.get('columna')} px")
        for m in malos:
            print(f"     {m}")
        for m in avisos:
            print(f"     aviso: {m} (se desplaza en su recuadro)")
        problemas += len(malos)
    print(f"{problemas} problemas en {len(pags)} páginas")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
