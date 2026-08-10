/** Panel Access Log — access.jsonl HTTP (F62). */
(function (global) {
  "use strict";

  var AUTO_MS = 5000;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function statusClass(status) {
    var code = Number(status) || 0;
    if (code >= 500) return "access-status access-status--5xx";
    if (code >= 400) return "access-status access-status--4xx";
    if (code >= 300) return "access-status access-status--3xx";
    if (code >= 200) return "access-status access-status--2xx";
    return "access-status";
  }

  function createAccessLogPane() {
    const root = document.createElement("div");
    root.className = "pane-access-log";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Access log</h3>" +
      '<p class="muted" style="margin-top:0">HTTP append-only · GET /api/access-log · method / path / status / ms · sin bodies</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="acc-refresh">Actualizar</button>' +
      '<label class="access-auto-label muted">' +
      '<input type="checkbox" id="acc-auto" /> Auto-refresh (5s)' +
      "</label>" +
      '<span class="mono muted" id="acc-count">—</span>' +
      "</div>" +
      '<p class="mono muted" id="acc-meta">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="acc-list" class="access-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#acc-list");
    const countEl = root.querySelector("#acc-count");
    const metaEl = root.querySelector("#acc-meta");
    const autoEl = root.querySelector("#acc-auto");
    let timer = null;

    function stopAuto() {
      if (timer != null) {
        clearInterval(timer);
        timer = null;
      }
    }

    function startAuto() {
      stopAuto();
      timer = setInterval(function () {
        if (!root.isConnected) {
          stopAuto();
          return;
        }
        refresh().catch(function () {});
      }, AUTO_MS);
    }

    function render(data) {
      const events = data.events || [];
      const enabled = data.access_log_enabled !== false;
      countEl.textContent = events.length + " requests";
      metaEl.textContent =
        "enabled=" +
        String(enabled) +
        " · session=" +
        (data.session_id || "—") +
        " · LIVE_BLOCKED=" +
        String(data.live_blocked);
      if (!enabled) {
        metaEl.className = "mono status-bad";
      } else {
        metaEl.className = "mono muted";
      }

      if (!events.length) {
        listEl.innerHTML = '<p class="muted mono">sin requests registrados</p>';
        return;
      }

      const ordered = events.slice().reverse();
      listEl.innerHTML = ordered
        .map(function (ev) {
          const ts =
            window.QLFmt && window.QLFmt.fmtDateTime
              ? window.QLFmt.fmtDateTime(ev.ts)
              : (ev.ts || "").slice(0, 19).replace("T", " ");
          const status = ev.status != null ? String(ev.status) : "?";
          const ms = ev.ms != null ? String(ev.ms) + " ms" : "—";
          return (
            '<div class="access-item">' +
            '<div class="access-head">' +
            '<span class="mono access-method">' +
            escapeHtml(ev.method || "?") +
            "</span>" +
            '<span class="' +
            statusClass(ev.status) +
            ' mono">' +
            escapeHtml(status) +
            "</span>" +
            '<span class="mono muted">' +
            escapeHtml(ms) +
            "</span>" +
            '<span class="mono muted">' +
            escapeHtml(ts) +
            "</span>" +
            "</div>" +
            '<div class="mono access-path">' +
            escapeHtml(ev.path || "") +
            "</div>" +
            "</div>"
          );
        })
        .join("");
    }

    async function refresh() {
      const data = await QLApi.getAccessLog(100);
      render(data);
    }

    root.querySelector("#acc-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML =
          '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
      });
    });

    autoEl.addEventListener("change", function () {
      if (autoEl.checked) {
        startAuto();
        refresh().catch(function () {});
      } else {
        stopAuto();
      }
    });

    root.refresh = refresh;
    root.dispose = stopAuto;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createAccessLogPane = createAccessLogPane;
})(window);
