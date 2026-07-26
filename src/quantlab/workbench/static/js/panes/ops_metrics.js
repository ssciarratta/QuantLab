/** Panel Ops Metrics — counters in-process (F42). */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createOpsMetricsPane() {
    const root = document.createElement("div");
    root.className = "pane-ops-metrics";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Ops metrics</h3>" +
      '<p class="muted" style="margin-top:0">Contadores in-process · GET /api/ops/metrics · Prometheus /api/ops/prometheus</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="ops-refresh">Actualizar</button>' +
      '<span class="mono muted" id="ops-count">—</span>' +
      "</div>" +
      '<p class="mono" id="ops-gate">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="ops-table"></div>' +
      "</div>";

    const countEl = root.querySelector("#ops-count");
    const gateEl = root.querySelector("#ops-gate");
    const tableEl = root.querySelector("#ops-table");

    function render(data) {
      const rows = data.rows || [];
      const blocked = Number(data.live_gate_blocked || 0);
      const highlight = data.highlight_live_gate_blocked === true || blocked > 0;
      countEl.textContent = rows.length + " counters";
      gateEl.textContent = "live_gate.blocked=" + blocked;
      gateEl.className = "mono" + (highlight ? " ops-gate--blocked" : " muted");

      if (!rows.length) {
        tableEl.innerHTML = '<p class="muted mono">sin counters (proceso fresco)</p>';
        return;
      }

      const body = rows
        .map(function (row) {
          const name = String(row.name || "");
          const isBlocked = name === "live_gate.blocked";
          const trClass = isBlocked && highlight ? ' class="ops-row--blocked"' : "";
          return (
            "<tr" +
            trClass +
            '><td class="mono">' +
            escapeHtml(name) +
            '</td><td class="mono ops-val">' +
            escapeHtml(String(row.value)) +
            "</td></tr>"
          );
        })
        .join("");

      tableEl.innerHTML =
        '<table class="data-table ops-metrics-table"><thead><tr><th>Counter</th><th>Value</th></tr></thead><tbody>' +
        body +
        "</tbody></table>" +
        '<p class="muted mono" style="margin-top:0.5rem">v' +
        escapeHtml(data.version || "?") +
        " · LIVE_BLOCKED=" +
        String(data.live_blocked) +
        "</p>";
    }

    async function refresh() {
      const data = await QLApi.getOpsMetrics();
      render(data);
    }

    root.querySelector("#ops-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        tableEl.innerHTML =
          '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createOpsMetricsPane = createOpsMetricsPane;
})(window);
