/** Panel Reports — historial metrics / preview HTML|JSON (F29). */
(function (global) {
  "use strict";

  function createReportsPane() {
    const root = document.createElement("div");
    root.className = "pane-reports";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Reports / Metrics history</h3>" +
      '<p class="muted" style="margin-top:0">Persistidos tras backtest lab / pipeline Binance en session <span class="mono">reports/</span>. ' +
      '<span class="data-badge data-badge-synth">SINTÉTICO</span> o ' +
      '<span class="data-badge data-badge-real">HISTÓRICO</span> según la corrida. ' +
      "JSON incluye <span class=\"mono\">fills</span>/<span class=\"mono\">orders</span>; HTML = preview.</p>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="rp-refresh">Actualizar lista</button>' +
      '<span class="mono muted" id="rp-count">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="rp-list"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div class="pane-row">' +
      '<span class="mono" id="rp-sel">sin selección</span>' +
      '<button type="button" class="btn secondary" id="rp-mode-json" disabled>JSON</button>' +
      '<button type="button" class="btn secondary" id="rp-mode-html" disabled>HTML</button>' +
      "</div>" +
      '<div id="rp-preview"></div>' +
      "</div>";

    const listEl = root.querySelector("#rp-list");
    const countEl = root.querySelector("#rp-count");
    const previewEl = root.querySelector("#rp-preview");
    const selEl = root.querySelector("#rp-sel");
    const btnJson = root.querySelector("#rp-mode-json");
    const btnHtml = root.querySelector("#rp-mode-html");

    let selectedId = null;
    let selectedPayload = null;
    let viewMode = "json";

    function renderPreview() {
      if (!selectedPayload) {
        previewEl.innerHTML = '<p class="muted mono">seleccioná un report</p>';
        return;
      }
      if (viewMode === "html" && selectedPayload.has_html && selectedPayload.html) {
        const iframe = document.createElement("iframe");
        iframe.className = "report-preview-frame";
        iframe.title = "Report HTML";
        iframe.sandbox = "";
        previewEl.innerHTML = "";
        previewEl.appendChild(iframe);
        iframe.srcdoc = selectedPayload.html;
        return;
      }
      const body = selectedPayload.report || selectedPayload;
      previewEl.innerHTML = QLLabUI.preJson(body);
    }

    function setSelection(reportId) {
      selectedId = reportId;
      selEl.textContent = reportId ? "report " + reportId : "sin selección";
      btnJson.disabled = !reportId;
      btnHtml.disabled = !reportId;
    }

    async function loadReport(reportId) {
      const data = await QLApi.labReport(reportId);
      selectedPayload = data;
      setSelection(reportId);
      viewMode = data.has_html ? "html" : "json";
      renderPreview();
    }

    function renderList(reports) {
      const rows = reports || [];
      countEl.textContent = rows.length + " reports";
      if (!rows.length) {
        listEl.innerHTML =
          '<p class="muted mono">sin reports — correr Backtest lab para persistir</p>';
        return;
      }
      const html = rows
        .map(function (r) {
          const active = r.report_id === selectedId ? " active" : "";
          return (
            '<button type="button" class="report-row' +
            active +
            '" data-id="' +
            QLLabUI.escapeHtml(r.report_id) +
            '">' +
            '<span class="mono">' +
            QLLabUI.escapeHtml(r.report_id) +
            "</span>" +
            '<span class="muted">' +
            QLLabUI.escapeHtml(r.strategy_id || "—") +
            " · " +
            QLLabUI.escapeHtml((r.created_at || "").slice(0, 19).replace("T", " ")) +
            (r.has_html ? " · HTML" : "") +
            "</span>" +
            "</button>"
          );
        })
        .join("");
      listEl.innerHTML = '<div class="report-list">' + html + "</div>";
      listEl.querySelectorAll("[data-id]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          loadReport(id).catch(function (err) {
            previewEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
          });
        });
      });
    }

    async function refresh() {
      const data = await QLApi.labReports();
      renderList(data.reports || []);
    }

    root.querySelector("#rp-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
      });
    });

    btnJson.addEventListener("click", function () {
      viewMode = "json";
      renderPreview();
    });
    btnHtml.addEventListener("click", function () {
      viewMode = "html";
      renderPreview();
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createReportsPane = createReportsPane;
})(window);
