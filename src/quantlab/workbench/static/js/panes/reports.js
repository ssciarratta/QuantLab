/** Panel Reports — historial metrics / preview HTML|JSON (F29). */
(function (global) {
  "use strict";

  function createReportsPane() {
    const root = document.createElement("div");
    root.className = "pane-reports";

    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Reports</h3>' +
      '<p class="muted pane-sub">Historial metrics · session/reports</p></div>' +
      '<details class="pane-more muted"><summary>Ayuda · sintético vs histórico</summary>' +
      '<p style="margin:0.35rem 0">Tras backtest lab / pipeline Binance. ' +
      '<span class="data-badge data-badge-synth">SINTÉTICO</span> o ' +
      '<span class="data-badge data-badge-real">HISTÓRICO</span> según la corrida. ' +
      "JSON: fills/orders · HTML: preview.</p></details>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn secondary" id="rp-refresh">Actualizar</button>' +
      '<span class="mono muted" id="rp-count">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="rp-list"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div class="pane-actions">' +
      '<span class="mono" id="rp-sel">sin selección</span>' +
      '<button type="button" class="btn secondary" id="rp-mode-json" disabled>JSON</button>' +
      '<button type="button" class="btn secondary" id="rp-mode-html" disabled>HTML</button>' +
      '<button type="button" class="btn" id="rp-to-mc" disabled title="Abrir Monte Carlo con este report como backtest_id">→ Monte Carlo</button>' +
      "</div>" +
      '<p class="muted mono" id="rp-nav-msg" style="margin:0.25rem 0 0"></p>' +
      '<div id="rp-preview"></div>' +
      "</div>";

    const listEl = root.querySelector("#rp-list");
    const countEl = root.querySelector("#rp-count");
    const previewEl = root.querySelector("#rp-preview");
    const selEl = root.querySelector("#rp-sel");
    const btnJson = root.querySelector("#rp-mode-json");
    const btnHtml = root.querySelector("#rp-mode-html");
    const btnMc = root.querySelector("#rp-to-mc");
    const navMsg = root.querySelector("#rp-nav-msg");

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
      btnMc.disabled = !reportId;
    }

    async function loadReport(reportId) {
      const data = await QLApi.labReport(reportId);
      selectedPayload = data;
      setSelection(reportId);
      viewMode = data.has_html ? "html" : "json";
      renderPreview();
      listEl.querySelectorAll(".report-row").forEach(function (btn) {
        btn.classList.toggle("active", btn.getAttribute("data-id") === reportId);
      });
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
            QLLabUI.escapeHtml(
              window.QLFmt && window.QLFmt.fmtDateTime
                ? window.QLFmt.fmtDateTime(r.created_at)
                : (r.created_at || "").slice(0, 19).replace("T", " ")
            ) +
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

    root.applyNavFocus = function () {
      if (!global.QLNav) return;
      const focus = global.QLNav.takeFocus("reports");
      if (!focus || !focus.focusId) return;
      navMsg.textContent = focus.message || ("focus → " + focus.focusId);
      refresh()
        .then(function () {
          return loadReport(focus.focusId);
        })
        .catch(function (err) {
          navMsg.textContent = "Report no encontrado: " + (err.message || focus.focusId);
          navMsg.className = "status-bad mono";
        });
    };

    root.querySelector("#rp-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
      });
    });

    btnMc.addEventListener("click", function () {
      if (!selectedId) return;
      const report = (selectedPayload && selectedPayload.report) || selectedPayload || {};
      const prefill = {
        backtest_id: selectedId,
        strategy_id: report.strategy_id || null,
        n_bars: report.n_bars || null,
        mode: "normal",
      };
      if (global.QLNav) {
        global.QLNav.open("montecarlo", {
          prefill: prefill,
          message: "Contexto desde report " + selectedId,
        });
      } else if (global.QLShell) {
        global.QLShell.open("montecarlo", { prefill: prefill });
      }
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
