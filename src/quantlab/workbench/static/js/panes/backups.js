/** Panel Backups — session/backups/ ZIP (F64). */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatBytes(n) {
    var bytes = Number(n) || 0;
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KiB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MiB";
  }

  function createBackupsPane() {
    const root = document.createElement("div");
    root.className = "pane-backups";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Backups</h3>" +
      '<p class="muted" style="margin-top:0">session/backups/ · ZIP research-safe · rotación max 5 · GET /api/backups · POST /api/backups/run</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="bak-run">Backup ahora</button>' +
      '<button type="button" class="btn secondary" id="bak-refresh">Actualizar</button>' +
      '<span class="mono muted" id="bak-count">—</span>' +
      "</div>" +
      '<p class="mono muted" id="bak-meta">—</p>' +
      '<p class="mono muted" id="bak-status">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="bak-list" class="backup-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#bak-list");
    const countEl = root.querySelector("#bak-count");
    const metaEl = root.querySelector("#bak-meta");
    const statusEl = root.querySelector("#bak-status");
    const runBtn = root.querySelector("#bak-run");

    function render(data) {
      const backups = data.backups || [];
      countEl.textContent = backups.length + " / " + (data.max_keep || 5);
      const minutes = data.auto_backup_minutes != null ? data.auto_backup_minutes : 0;
      const enabled = data.auto_backup_enabled === true;
      metaEl.textContent =
        "auto=" +
        (enabled ? minutes + " min" : "off") +
        " · session=" +
        (data.session_id || "—") +
        " · LIVE_BLOCKED=" +
        String(data.live_blocked);
      metaEl.className = "mono muted";

      if (!backups.length) {
        listEl.innerHTML = '<p class="muted mono">sin backups</p>';
        return;
      }

      listEl.innerHTML = backups
        .map(function (b) {
          const ts =
            window.QLFmt && window.QLFmt.fmtDateTime
              ? window.QLFmt.fmtDateTime(b.mtime_utc)
              : (b.mtime_utc || "").slice(0, 19).replace("T", " ");
          const sha = b.sha256 ? String(b.sha256).slice(0, 12) + "…" : "—";
          return (
            '<div class="backup-item">' +
            '<div class="backup-head">' +
            '<span class="mono backup-name">' +
            escapeHtml(b.filename || "?") +
            "</span>" +
            '<span class="mono muted">' +
            escapeHtml(formatBytes(b.bytes)) +
            "</span>" +
            '<span class="mono muted">' +
            escapeHtml(ts) +
            "</span>" +
            "</div>" +
            '<div class="mono muted backup-sha">sha256 ' +
            escapeHtml(sha) +
            "</div>" +
            "</div>"
          );
        })
        .join("");
    }

    async function refresh() {
      const data = await QLApi.getBackups();
      render(data);
      statusEl.textContent = "ok";
      statusEl.className = "mono muted status-ok";
    }

    async function runBackup() {
      runBtn.disabled = true;
      statusEl.textContent = "backup…";
      statusEl.className = "mono muted";
      try {
        const data = await QLApi.runBackup();
        render(data);
        statusEl.textContent =
          "backup ok · " + (data.filename || "") + " · " + formatBytes(data.bytes);
        statusEl.className = "mono muted status-ok";
      } finally {
        runBtn.disabled = false;
      }
    }

    root.querySelector("#bak-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML =
          '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });

    runBtn.addEventListener("click", function () {
      runBackup().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
        runBtn.disabled = false;
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBackupsPane = createBackupsPane;
})(window);
