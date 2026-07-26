/** Panel Features — Feature Store browser + pipeline runner (F31). */
(function (global) {
  "use strict";

  function createFeaturesPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-features";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Features pipeline</h3>" +
      '<p class="muted" style="margin-top:0">Demo causal: close_price + simple_return + log_return → persiste en <span class="mono">session/features</span> (FeatureStore).</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="ft-run">Correr pipeline</button>' +
      '<button type="button" class="btn secondary" id="ft-refresh">Actualizar store</button>' +
      '<span class="mono" id="ft-status">—</span>' +
      "</div>" +
      '<p class="muted mono" id="ft-meta">—</p>' +
      '<div id="ft-out"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Feature Store</h3>" +
      '<p class="muted" id="ft-store-msg" style="margin-top:0"></p>' +
      '<div id="ft-store-list"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Columnas</h3>" +
      '<p class="mono muted" id="ft-columns">—</p>' +
      "</div>";

    const statusEl = root.querySelector("#ft-status");
    const metaEl = root.querySelector("#ft-meta");
    const msgEl = root.querySelector("#ft-store-msg");
    const listEl = root.querySelector("#ft-store-list");
    const colsEl = root.querySelector("#ft-columns");

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function renderStore(data) {
      metaEl.textContent =
        (data.source || "?") +
        (data.store_path ? " · " + data.store_path : "") +
        " · " +
        (data.count || 0) +
        " artifacts";
      msgEl.textContent = data.message || "";
      msgEl.className = data.count ? "muted" : "muted status-warn";

      const union = data.columns_union || [];
      if (union.length) {
        colsEl.textContent = union.join(", ");
      }

      const rows = data.artifacts || [];
      if (!rows.length) {
        listEl.innerHTML =
          '<p class="muted mono">store vacío — corré el pipeline</p>';
        return;
      }

      listEl.innerHTML =
        '<table class="data-table features-store-table"><thead><tr>' +
        "<th>instrument</th><th>pipeline</th><th>version</th><th>columns</th><th>bars</th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (a) {
            const cols = (a.columns || a.series || []).join(", ");
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(a.instrument_id) +
              "</td>" +
              '<td class="mono">' +
              esc(a.pipeline_name) +
              "</td>" +
              '<td class="mono">' +
              esc(a.version) +
              "</td>" +
              '<td class="mono">' +
              esc(cols || "—") +
              "</td>" +
              '<td class="num">' +
              esc(a.bar_count != null ? a.bar_count : "—") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    root.querySelector("#ft-refresh").addEventListener("click", function () {
      root.refresh().catch(function () {});
    });

    QLLabUI.bindRun(root, "#ft-run", "#ft-status", "#ft-out", function () {
      return QLApi.labFeaturesRun({ n_bars: 20 }).then(function (data) {
        if (data.columns && data.columns.length) {
          colsEl.textContent = data.columns.join(", ");
        }
        root.refresh().catch(function () {});
        return data;
      });
    });

    root.refresh = async function () {
      try {
        const data = await QLApi.labFeaturesStore();
        renderStore(data);
        if (!statusEl.textContent || statusEl.textContent === "—") {
          QLLabUI.setStatus(statusEl, true, "store " + (data.count || 0));
        }
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
  global.QLPanes.createFeaturesPane = createFeaturesPane;
})(window);
