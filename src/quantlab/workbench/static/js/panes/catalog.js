/** Panel Catalog — browser read-only Data Catalog (F30). */
(function (global) {
  "use strict";

  function createCatalogPane() {
    const root = document.createElement("div");
    root.className = "pane-catalog";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Data Catalog</h3>" +
      '<p class="muted" style="margin-top:0">Browse read-only de datasets locales (SQLite/DuckDB vía <span class="mono">quantlab.data.catalog</span>). Sin catálogo → lista vacía.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="cat-refresh">Actualizar</button>' +
      '<span class="mono muted" id="cat-meta">—</span>' +
      "</div>" +
      '<p class="muted" id="cat-msg"></p>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="cat-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#cat-list");
    const metaEl = root.querySelector("#cat-meta");
    const msgEl = root.querySelector("#cat-msg");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function render(data) {
      metaEl.textContent =
        (data.available ? "ok" : "ausente") +
        (data.backend ? " · " + data.backend : "") +
        (data.catalog_path ? " · " + data.catalog_path : "") +
        " · " +
        (data.count || 0) +
        " datasets";
      msgEl.textContent = data.message || "";
      msgEl.className = data.available ? "muted" : "muted status-warn";

      const rows = data.datasets || [];
      if (!rows.length) {
        listEl.innerHTML =
          '<p class="muted mono">' +
          (data.available
            ? "catálogo vacío"
            : "sin catálogo local — ok (respuesta vacía)") +
          "</p>";
        return;
      }

      listEl.innerHTML =
        '<table class="data-table catalog-table"><thead><tr>' +
        "<th>dataset_id</th><th>kind</th><th>provider</th><th>symbol</th><th>tf</th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (d) {
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(d.dataset_id) +
              "</td>" +
              "<td>" +
              esc(d.kind) +
              "</td>" +
              "<td>" +
              esc(d.provider) +
              "</td>" +
              '<td class="mono">' +
              esc(d.symbol || "—") +
              "</td>" +
              "<td>" +
              esc(d.timeframe || "—") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    root.querySelector("#cat-refresh").addEventListener("click", function () {
      root.refresh().catch(function () {});
    });

    root.refresh = async function () {
      try {
        const data = await QLApi.catalog();
        render(data);
      } catch (err) {
        metaEl.textContent = "error";
        msgEl.textContent = err.message;
        msgEl.className = "status-bad";
        listEl.innerHTML = "";
      }
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createCatalogPane = createCatalogPane;
})(window);
