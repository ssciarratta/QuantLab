/** Panel Riesgo — límites paper + path de sesión (F25). */
(function (global) {
  "use strict";

  function createRiskPane() {
    const root = document.createElement("div");
    root.className = "pane-risk";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Límites paper</h3>" +
      '<p class="muted" style="margin-top:0">Fail-closed en submit paper (qty / notional / símbolos).</p>' +
      '<dl class="kv" id="risk-limits"></dl>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="risk-refresh">Actualizar</button>' +
      '<span class="mono muted" id="risk-status">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Sesión</h3>" +
      '<dl class="kv" id="risk-session"></dl>' +
      "</div>";

    const limitsEl = root.querySelector("#risk-limits");
    const sessionEl = root.querySelector("#risk-session");
    const statusEl = root.querySelector("#risk-status");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function render(data) {
      const lim = data.limits || {};
      const symbols =
        lim.allowed_symbols == null
          ? "(todos)"
          : Array.isArray(lim.allowed_symbols)
            ? lim.allowed_symbols.join(", ") || "(vacío)"
            : String(lim.allowed_symbols);
      limitsEl.innerHTML =
        "<dt>max_qty</dt><dd class=\"mono num\">" +
        esc(lim.max_qty) +
        "</dd>" +
        "<dt>max_notional</dt><dd class=\"mono num\">" +
        esc(lim.max_notional) +
        "</dd>" +
        "<dt>allowed_symbols</dt><dd class=\"mono\">" +
        esc(symbols) +
        "</dd>" +
        "<dt>slippage_bps</dt><dd class=\"mono num\">" +
        esc(data.slippage_bps) +
        "</dd>" +
        "<dt>LIVE_BLOCKED</dt><dd class=\"mono\">" +
        esc(String(data.live_blocked)) +
        "</dd>";
      sessionEl.innerHTML =
        "<dt>session_id</dt><dd class=\"mono\">" +
        esc(data.session_id) +
        "</dd>" +
        "<dt>session path</dt><dd class=\"mono\" style=\"word-break:break-all\">" +
        esc(data.session_root) +
        "</dd>" +
        "<dt>mode</dt><dd class=\"mono\">" +
        esc(data.mode) +
        "</dd>";
      statusEl.textContent = "ok";
      statusEl.className = "mono muted status-ok";
    }

    async function refresh() {
      const data = await QLApi.risk();
      render(data);
    }

    root.querySelector("#risk-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createRiskPane = createRiskPane;
})(window);
