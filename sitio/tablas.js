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

// Las tablas generadas en HTML no traen <thead>: el navegador pone la fila de encabezados en el <tbody> y tablesort la
// ordenaría junto con las demás. Se pasa a un <thead> propio antes de prepararla.
function separarEncabezado(tabla) {
  if (tabla.tHead) return;
  const primera = tabla.tBodies[0].rows[0];
  if (!primera || primera.querySelector("td")) return;
  tabla.createTHead().appendChild(primera);
}

// Sin filtro en las pestañas (ya separan por hipótesis) ni en las páginas de cada hipótesis, cuyas tablas son cortas.
function llevaFiltro(tabla, filas) {
  if (filas.length < 8 || tabla.closest(".tabbed-set")) return false;
  return !/\/experimentos\/h\d\//.test(location.pathname);
}

function prepararTabla(tabla) {
  if (tabla.dataset.preparada || !tabla.tBodies[0]) return;
  tabla.dataset.preparada = "1";
  separarEncabezado(tabla);
  const filas = Array.from(tabla.tBodies[0].rows).filter((fila) => fila.querySelector("td"));
  for (const fila of filas) {
    for (const celda of fila.cells) {
      const n = numeroDe(celda.textContent);
      if (n !== null) celda.dataset.sort = String(n);
    }
  }
  new Tablesort(tabla);
  if (!llevaFiltro(tabla, filas)) return;
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
