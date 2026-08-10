/** Panel Activity — activity.jsonl de sesión (F41). */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createActivityPane() {
    const root = document.createElement("div");
    root.className = "pane-activity";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Activity log</h3>" +
      '<p class="muted" style="margin-top:0">Append-only · GET /api/activity · eventos connect / submit / backtest / optimize / export / error</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="act-refresh">Actualizar</button>' +
      '<span class="mono muted" id="act-count">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="act-list" class="activity-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#act-list");
    const countEl = root.querySelector("#act-count");

    function render(events) {
      const rows = events || [];
      countEl.textContent = rows.length + " eventos";
      if (!rows.length) {
        listEl.innerHTML = '<p class="muted mono">sin actividad</p>';
        return;
      }
      // Más recientes arriba.
      const ordered = rows.slice().reverse();
      listEl.innerHTML = ordered
        .map(function (ev) {
          const ok = ev.ok !== false;
          const cls = ok ? "activity-item activity-item--ok" : "activity-item activity-item--err";
          const ts =
            window.QLFmt && window.QLFmt.fmtDateTime
              ? window.QLFmt.fmtDateTime(ev.ts)
              : (ev.ts || "").slice(0, 19).replace("T", " ");
          const detail = ev.detail
            ? '<div class="muted mono activity-detail">' +
              escapeHtml(JSON.stringify(ev.detail)) +
              "</div>"
            : "";
          const op = ev.op ? ' · op=' + escapeHtml(String(ev.op)) : "";
          return (
            '<div class="' +
            cls +
            '">' +
            '<div class="activity-head">' +
            '<span class="mono activity-event">' +
            escapeHtml(ev.event || "?") +
            "</span>" +
            '<span class="mono muted">' +
            escapeHtml(ts) +
            "</span>" +
            "</div>" +
            '<div class="activity-msg">' +
            escapeHtml(ev.message || "") +
            escapeHtml(op) +
            "</div>" +
            detail +
            "</div>"
          );
        })
        .join("");
    }

    async function refresh() {
      const data = await QLApi.getActivity(100);
      render(data.events || []);
    }

    root.querySelector("#act-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML = '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createActivityPane = createActivityPane;
})(window);
