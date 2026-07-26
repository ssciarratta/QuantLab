/** Panel Reconciliación Paper — status read-only journal/book (F90). */
(function (global) {
  "use strict";

  function createReconciliationPane() {
    const root = document.createElement("div");
    root.className = "pane-reconciliation";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Journal / Book</h3>" +
      '<p class="muted" style="margin-top:0">Solo lectura. El rebuild es exclusivamente CLI offline; esta UI nunca muta archivos.</p>' +
      '<div class="pane-row">' +
      '<span class="mono" id="recon-badge">—</span>' +
      '<button type="button" class="btn secondary" id="recon-refresh">Actualizar</button>' +
      '<label class="muted"><input type="checkbox" id="recon-auto"> Auto-refresh</label>' +
      "</div>" +
      '<dl class="kv" id="recon-summary"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Checkpoint</h3>" +
      '<dl class="kv" id="recon-checkpoint"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Issues</h3>" +
      '<div class="mono muted" id="recon-issues">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Recuperación</h3>" +
      '<p class="muted" style="margin-top:0">Si status ≠ ok, correr offline (crea backup; nunca modifica el journal):</p>' +
      '<code class="mono" id="recon-rebuild-via" style="word-break:break-all">—</code>' +
      "</div>";

    const badgeEl = root.querySelector("#recon-badge");
    const summaryEl = root.querySelector("#recon-summary");
    const checkpointEl = root.querySelector("#recon-checkpoint");
    const issuesEl = root.querySelector("#recon-issues");
    const rebuildEl = root.querySelector("#recon-rebuild-via");
    const autoEl = root.querySelector("#recon-auto");
    let timer = null;

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function render(data) {
      const ok = data.ok === true;
      badgeEl.textContent = ok ? "OK — reconciliado" : "ATENCIÓN — " + String(data.status || "?");
      badgeEl.className = ok ? "mono status-ok" : "mono status-bad";

      summaryEl.innerHTML =
        "<dt>status</dt><dd class=\"mono\">" +
        esc(data.status) +
        "</dd>" +
        "<dt>record_count</dt><dd class=\"mono num\">" +
        esc(data.record_count) +
        "</dd>" +
        "<dt>session_id</dt><dd class=\"mono\">" +
        esc(data.session_id) +
        "</dd>";

      const cp = data.checkpoint;
      if (cp && typeof cp === "object") {
        checkpointEl.innerHTML =
          "<dt>record_count</dt><dd class=\"mono num\">" +
          esc(cp.record_count) +
          "</dd>" +
          "<dt>last_fill_id</dt><dd class=\"mono\">" +
          esc(cp.last_fill_id == null ? "(null)" : cp.last_fill_id) +
          "</dd>" +
          "<dt>sha256</dt><dd class=\"mono\" style=\"word-break:break-all\">" +
          esc(cp.sha256) +
          "</dd>";
      } else {
        checkpointEl.innerHTML = "<dt>checkpoint</dt><dd class=\"mono muted\">(sin checkpoint)</dd>";
      }

      const issues = Array.isArray(data.issues) ? data.issues : [];
      if (!issues.length) {
        issuesEl.textContent = "Sin issues.";
        issuesEl.className = "mono muted";
      } else {
        issuesEl.innerHTML = issues.map(esc).join("<br>");
        issuesEl.className = "mono status-bad";
      }

      rebuildEl.textContent = String(data.rebuild_via || "—");
    }

    async function refresh() {
      try {
        const data = await QLApi.paperReconciliation();
        render(data);
      } catch (err) {
        badgeEl.textContent = "error: " + err.message;
        badgeEl.className = "mono status-bad";
      }
    }

    root.querySelector("#recon-refresh").addEventListener("click", function () {
      refresh();
    });

    autoEl.addEventListener("change", function () {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      if (autoEl.checked) {
        timer = setInterval(refresh, 10000);
      }
    });

    root.addEventListener("ql-pane-closed", function () {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createReconciliationPane = createReconciliationPane;
})(window);
