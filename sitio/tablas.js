// Tablas ordenables (clic en el encabezado) y, las de 8 filas o más, con un campo para filtrar filas.
// Los números de las celdas vienen en formato del sitio (−8,4 [−11,0, −6,1], 3.300, 4.6×): se ordena por el primero.
// document$ es el observable de Material: corre en cada página, también con la navegación instantánea.

function numeroDe(texto) {
  const m = texto.replace(/−/g, "-").match(/-?\d[\d.,]*/);
  if (!m) return null;
  let s = m[0];
  if (/,\d+$/.test(s)) s = s.replace(/\./g, "").replace(",", ".");  // 3.300,5 → 3300.5
  else if (/^\-?\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, "");  // 3.300 → 3300
  const n = parseFloat(s);
  return Number.isNaN(n) ? null : n;
}

function prepararTabla(tabla) {
  // Sin tbody no hay filas que ordenar. Sin thead, tablesort toma la primera fila como encabezado; las filas de solo
  // encabezados (th) no se marcan ni se filtran.
  if (tabla.dataset.preparada || !tabla.tBodies[0]) return;
  tabla.dataset.preparada = "1";
  const filas = Array.from(tabla.tBodies[0].rows).filter((fila) => fila.querySelector("td"));
  for (const fila of filas) {
    for (const celda of fila.cells) {
      const n = numeroDe(celda.textContent);
      if (n !== null) celda.dataset.sort = String(n);
    }
  }
  new Tablesort(tabla);
  if (filas.length < 8) return;
  const campo = document.createElement("input");
  campo.type = "search";
  campo.className = "filtro-tabla";
  campo.placeholder = "Filtrar filas (por ejemplo, H3 o pierde)";
  campo.setAttribute("aria-label", "Filtrar filas de la tabla");
  campo.addEventListener("input", () => {
    const q = campo.value.trim().toLowerCase();
    for (const fila of filas) fila.hidden = q !== "" && !fila.textContent.toLowerCase().includes(q);
  });
  const envoltura = tabla.closest(".md-typeset__scrollwrap") || tabla;
  envoltura.parentNode.insertBefore(campo, envoltura);
}

document$.subscribe(() => {
  document.querySelectorAll("article table:not([class])").forEach(prepararTabla);
});
