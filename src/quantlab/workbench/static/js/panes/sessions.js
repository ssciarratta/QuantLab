/** Panel Sessions — multi-session switcher (F46). */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createSessionsPane(onSwitched) {
    const root = document.createElement("div");
    root.className = "pane-sessions";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Sessions</h3>" +
      '<p class="muted" style="margin-top:0">Listar · cambiar · nueva · fail-closed validate_session_id · LIVE_BLOCKED</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="sess-refresh">Actualizar</button>' +
      '<button type="button" class="btn" id="sess-new">Nueva sesión</button>' +
      '<span class="mono muted" id="sess-meta">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="sess-list" class="sessions-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#sess-list");
    const metaEl = root.querySelector("#sess-meta");

    function notifySwitched(data) {
      if (typeof onSwitched === "function") {
        onSwitched(data);
      }
      if (global.QLToasts && QLToasts.success) {
        QLToasts.success("Sesión: " + (data.session_id || "?"));
      }
    }

    function render(payload) {
      const sessions = (payload && payload.sessions) || [];
      const current = (payload && payload.session_id) || "—";
      const parent = (payload && payload.session_parent) || "";
      metaEl.textContent =
        sessions.length + " · actual=" + current + (parent ? " · " + parent : "");
      if (!sessions.length) {
        listEl.innerHTML = '<p class="muted mono">sin sesiones</p>';
        return;
      }
      listEl.innerHTML = sessions
        .map(function (s) {
          const sid = s.session_id || "?";
          const isCurrent = !!s.current;
          const cls =
            "session-item" + (isCurrent ? " session-item--current" : "");
          const created = s.created_at
            ? String(s.created_at).slice(0, 19).replace("T", " ")
            : "—";
          const badge = isCurrent
            ? '<span class="session-badge">actual</span>'
            : "";
          const action = isCurrent
            ? ""
            : '<button type="button" class="btn secondary sess-switch" data-sid="' +
              escapeHtml(sid) +
              '">Cambiar</button>';
          return (
            '<div class="' +
            cls +
            '">' +
            '<div class="session-head">' +
            '<span class="mono session-id">' +
            escapeHtml(sid) +
            "</span>" +
            badge +
            "</div>" +
            '<div class="muted mono session-created">created ' +
            escapeHtml(created) +
            "</div>" +
            action +
            "</div>"
          );
        })
        .join("");

      listEl.querySelectorAll(".sess-switch").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const sid = btn.getAttribute("data-sid");
          if (!sid) return;
          QLApi.sessionsSwitch(sid)
            .then(function (data) {
              notifySwitched(data);
              return refresh();
            })
            .catch(function (err) {
              listEl.insertAdjacentHTML(
                "afterbegin",
                '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>"
              );
              if (global.QLToasts && QLToasts.error) {
                QLToasts.error(err.message);
              }
            });
        });
      });
    }

    async function refresh() {
      const data = await QLApi.sessionsList();
      render(data);
      return data;
    }

    root.querySelector("#sess-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        listEl.innerHTML =
          '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
      });
    });

    root.querySelector("#sess-new").addEventListener("click", function () {
      QLApi.sessionsNew({})
        .then(function (data) {
          notifySwitched(data);
          return refresh();
        })
        .catch(function (err) {
          listEl.insertAdjacentHTML(
            "afterbegin",
            '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>"
          );
          if (global.QLToasts && QLToasts.error) {
            QLToasts.error(err.message);
          }
        });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSessionsPane = createSessionsPane;
})(window);
