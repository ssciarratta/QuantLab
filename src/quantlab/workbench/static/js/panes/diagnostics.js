/** Panel Diagnostics — snapshot read-only agregado para soporte (F95). */
(function (global) {
  "use strict";

  function createDiagnosticsPane() {
    const root = document.createElement("div");
    root.className = "pane-diagnostics";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Snapshot de diagnóstico</h3>" +
      '<p class="muted" style="margin-top:0">Solo lectura. Agrega versión, modo, salud y reconciliación desde <code class="mono">/api/diagnostics</code>.</p>' +
      '<div class="pane-row">' +
      '<span class="mono" id="diag-badge">—</span>' +
      '<button type="button" class="btn secondary" id="diag-refresh">Actualizar</button>' +
      '<button type="button" class="btn secondary" id="diag-copy">Copiar JSON</button>' +
      '<a class="btn secondary" id="diag-download" href="/api/diagnostics.json" download>Descargar</a>' +
      '<a class="btn secondary" id="diag-bundle" href="/api/support-bundle.zip" download>Support ZIP</a>' +
      "</div>" +
      '<dl class="kv" id="diag-summary"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>JSON</h3>" +
      '<pre class="mono" id="diag-json" style="white-space:pre-wrap;word-break:break-all">—</pre>' +
      "</div>";

    const badgeEl = root.querySelector("#diag-badge");
    const summaryEl = root.querySelector("#diag-summary");
    const jsonEl = root.querySelector("#diag-json");
    let last = null;

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function row(k, v) {
      return "<dt>" + esc(k) + "</dt><dd class=\"mono\">" + esc(v) + "</dd>";
    }

    function render(data) {
      last = data;
      const healthy =
        data.live_blocked === true &&
        data.health &&
        data.health.checks_ok === data.health.checks_total;
      badgeEl.textContent = healthy ? "OK" : "REVISAR";
      badgeEl.className = healthy ? "mono status-ok" : "mono status-bad";

      const h = data.health || {};
      const r = data.reconciliation || {};
      summaryEl.innerHTML =
        row("version", data.version) +
        row("phases", data.phases_summary) +
        row("mode", data.mode) +
        row("live_blocked", data.live_blocked) +
        row("connected_venue", data.connected_venue == null ? "(desconectado)" : data.connected_venue) +
        row("md_provider", data.md_provider == null ? "(n/a)" : data.md_provider) +
        row("broker_connected", data.broker_connected) +
        row("paper_kill_engaged", data.paper_kill_engaged) +
        row("health", esc(h.status) + " (" + esc(h.checks_ok) + "/" + esc(h.checks_total) + ")") +
        row("reconciliation", esc(r.status) + (r.ok ? " · ok" : " · atención"));

      jsonEl.textContent = JSON.stringify(data, null, 2);
    }

    async function refresh() {
      try {
        const data = await QLApi.diagnostics();
        render(data);
      } catch (err) {
        badgeEl.textContent = "error: " + err.message;
        badgeEl.className = "mono status-bad";
      }
    }

    root.querySelector("#diag-refresh").addEventListener("click", function () {
      refresh();
    });

    root.querySelector("#diag-copy").addEventListener("click", function () {
      if (last == null) return;
      const text = JSON.stringify(last, null, 2);
      if (global.navigator && global.navigator.clipboard) {
        global.navigator.clipboard.writeText(text).catch(function () {});
      }
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createDiagnosticsPane = createDiagnosticsPane;
})(window);
