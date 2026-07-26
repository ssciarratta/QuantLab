/** Panel API Explorer — navega el catálogo OpenAPI, read-only (F94). */
(function (global) {
  "use strict";

  function createApiExplorerPane() {
    const root = document.createElement("div");
    root.className = "pane-api-explorer";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Catálogo de API</h3>" +
      '<p class="muted" style="margin-top:0">Solo lectura. Generado desde <code class="mono">/api/openapi.json</code>. Sin rutas de ejecución LIVE.</p>' +
      '<div class="pane-row">' +
      '<span class="mono" id="api-badge">—</span>' +
      '<input type="search" id="api-filter" placeholder="filtrar (path, método, tag)" style="flex:1;min-width:120px">' +
      '<button type="button" class="btn secondary" id="api-refresh">Actualizar</button>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<table class="tbl" id="api-table"><thead><tr>' +
      "<th>Método</th><th>Path</th><th>Resumen</th><th>Tags</th>" +
      "</tr></thead><tbody></tbody></table>" +
      "</div>";

    const badgeEl = root.querySelector("#api-badge");
    const filterEl = root.querySelector("#api-filter");
    const tbodyEl = root.querySelector("#api-table tbody");
    let rows = [];

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function flatten(doc) {
      const out = [];
      const paths = doc && doc.paths ? doc.paths : {};
      Object.keys(paths).forEach(function (p) {
        const ops = paths[p] || {};
        Object.keys(ops).forEach(function (m) {
          const op = ops[m] || {};
          out.push({
            method: m.toUpperCase(),
            path: p,
            summary: op.summary || "",
            tags: Array.isArray(op.tags) ? op.tags : [],
          });
        });
      });
      out.sort(function (a, b) {
        if (a.path === b.path) return a.method < b.method ? -1 : 1;
        return a.path < b.path ? -1 : 1;
      });
      return out;
    }

    function draw() {
      const q = filterEl.value.trim().toLowerCase();
      const shown = rows.filter(function (r) {
        if (!q) return true;
        return (
          r.path.toLowerCase().indexOf(q) !== -1 ||
          r.method.toLowerCase().indexOf(q) !== -1 ||
          r.summary.toLowerCase().indexOf(q) !== -1 ||
          r.tags.join(" ").toLowerCase().indexOf(q) !== -1
        );
      });
      tbodyEl.innerHTML = shown
        .map(function (r) {
          const cls = r.method === "GET" ? "status-ok" : "status-bad";
          return (
            "<tr><td><span class=\"mono " +
            cls +
            "\">" +
            esc(r.method) +
            "</span></td><td class=\"mono\">" +
            esc(r.path) +
            "</td><td>" +
            esc(r.summary) +
            "</td><td class=\"mono muted\">" +
            esc(r.tags.join(", ")) +
            "</td></tr>"
          );
        })
        .join("");
      badgeEl.textContent =
        shown.length + "/" + rows.length + " rutas";
      badgeEl.className = "mono status-ok";
    }

    async function refresh() {
      try {
        const doc = await QLApi.openapi();
        rows = flatten(doc);
        draw();
      } catch (err) {
        badgeEl.textContent = "error: " + err.message;
        badgeEl.className = "mono status-bad";
      }
    }

    filterEl.addEventListener("input", draw);
    root.querySelector("#api-refresh").addEventListener("click", function () {
      refresh();
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createApiExplorerPane = createApiExplorerPane;
})(window);
