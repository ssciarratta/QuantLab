/** Panel Salud / Modo. */
(function (global) {
  "use strict";

  function createHealthPane(onModeChange) {
    const root = document.createElement("div");
    root.className = "pane-health";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Modo de sesión</h3>" +
      '<div class="pane-row">' +
      '<label class="field">Modo<select id="hp-mode">' +
      '<option value="tester">TESTER</option>' +
      '<option value="paper">PAPER</option>' +
      '<option value="real">REAL (= paper)</option>' +
      "</select></label>" +
      '<button type="button" class="btn" id="hp-apply">Aplicar</button>' +
      "</div>" +
      '<p class="muted mono" id="hp-mode-info">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Health checks</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="hp-refresh">Actualizar</button>' +
      '<span class="mono" id="hp-status">—</span>' +
      "</div>" +
      '<div id="hp-checks"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Broker reconnect / disconnect</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="hp-reconnect">Reconectar</button>' +
      '<button type="button" class="btn secondary" id="hp-disconnect">Desconectar</button>' +
      '<span class="mono muted" id="hp-reconnect-info">last connect de sesión</span>' +
      "</div>" +
      '<p class="muted mono" id="hp-reconnect-status">—</p>' +
      "</div>";

    const modeSel = root.querySelector("#hp-mode");
    const modeInfo = root.querySelector("#hp-mode-info");
    const statusEl = root.querySelector("#hp-status");
    const checksEl = root.querySelector("#hp-checks");

    async function refreshMode() {
      const m = await QLApi.getMode();
      const display = m.mode === "paper" ? "paper (REAL alias)" : m.mode;
      modeSel.value = m.mode === "paper" ? "paper" : m.mode;
      modeInfo.textContent =
        "mode=" +
        display +
        " · LIVE_BLOCKED=" +
        String(m.live_blocked) +
        " · real_alias=" +
        m.real_alias;
      if (onModeChange) onModeChange(m);
    }

    async function refreshHealth() {
      const h = await QLApi.health();
      statusEl.textContent = h.ok ? "OK" : "FAIL";
      statusEl.className = "mono " + (h.ok ? "status-ok" : "status-bad");
      const rows = (h.checks || [])
        .map(function (c) {
          const cls = c.ok ? "status-ok" : "status-bad";
          return (
            "<tr><td class=\"" +
            cls +
            "\">" +
            (c.ok ? "✓" : "✗") +
            "</td><td>" +
            c.name +
            '</td><td class="muted">' +
            (c.detail || "") +
            "</td></tr>"
          );
        })
        .join("");
      const flags =
        "kill=" +
        String(h.paper_kill_engaged === true) +
        " · backup_min=" +
        String(h.auto_backup_minutes != null ? h.auto_backup_minutes : 0) +
        " · access_log=" +
        String(h.access_log !== false);
      checksEl.innerHTML =
        '<table class="data-table"><thead><tr><th></th><th>Check</th><th>Detalle</th></tr></thead><tbody>' +
        rows +
        "</tbody></table>" +
        '<p class="muted mono" style="margin-top:0.5rem">v' +
        (h.version || "?") +
        " · " +
        (h.checked_at || "") +
        "</p>" +
        '<p class="muted mono" id="hp-ops-flags">' +
        flags +
        "</p>";
    }

    root.querySelector("#hp-apply").addEventListener("click", async function () {
      try {
        await QLApi.setMode(modeSel.value);
        await refreshMode();
        await refreshHealth();
      } catch (err) {
        modeInfo.textContent = "Error: " + err.message;
        modeInfo.classList.add("status-bad");
      }
    });

    root.querySelector("#hp-refresh").addEventListener("click", function () {
      refreshHealth().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });

    const reconnectStatus = root.querySelector("#hp-reconnect-status");
    root.querySelector("#hp-reconnect").addEventListener("click", async function () {
      try {
        const res = await QLApi.reconnect();
        reconnectStatus.textContent =
          "ok · venue=" +
          res.venue +
          " · mode=" +
          res.mode +
          " · md_source=" +
          (res.md_source || "—");
        reconnectStatus.classList.remove("status-bad");
        await refreshHealth();
      } catch (err) {
        reconnectStatus.textContent = "Error: " + err.message;
        reconnectStatus.classList.add("status-bad");
      }
    });

    root.querySelector("#hp-disconnect").addEventListener("click", async function () {
      try {
        const res = await QLApi.disconnect();
        reconnectStatus.textContent =
          "disconnected" +
          (res.previous_venue ? " · was=" + res.previous_venue : "") +
          (res.has_last_connect ? " · last_connect=ok" : " · last_connect=none");
        reconnectStatus.classList.remove("status-bad");
        await refreshHealth();
      } catch (err) {
        reconnectStatus.textContent = "Error disconnect: " + err.message;
        reconnectStatus.classList.add("status-bad");
      }
    });

    root.refresh = async function () {
      await refreshMode();
      await refreshHealth();
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createHealthPane = createHealthPane;
})(window);
