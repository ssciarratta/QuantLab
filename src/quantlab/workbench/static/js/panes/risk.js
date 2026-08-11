/** Panel Riesgo — límites paper + utilización + kill switch (F25 / F69 / F70). */
(function (global) {
  "use strict";

  function createRiskPane() {
    const root = document.createElement("div");
    root.className = "pane-risk";

    root.innerHTML =
      '<div class="pane-section pane-kill-switch">' +
      "<h3>Paper Kill Switch</h3>" +
      '<p class="muted" style="margin-top:0">Bloquea paper submit y session step. No afecta LIVE (ya bloqueado).</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn danger" id="risk-kill-btn">ENGAGE KILL</button>' +
      '<span class="mono muted" id="risk-kill-status">engaged=false</span>' +
      "</div>" +
      "</div>" +
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
      "<h3>Utilización</h3>" +
      '<p class="muted" style="margin-top:0">% usado de max_qty / max_notional vs book.</p>' +
      '<dl class="kv" id="risk-utilization"></dl>' +
      '<div id="risk-util-positions" class="mono muted" style="margin-top:0.5rem;font-size:1.14em"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Sesión</h3>" +
      '<dl class="kv" id="risk-session"></dl>' +
      "</div>";

    const limitsEl = root.querySelector("#risk-limits");
    const utilEl = root.querySelector("#risk-utilization");
    const utilPosEl = root.querySelector("#risk-util-positions");
    const sessionEl = root.querySelector("#risk-session");
    const statusEl = root.querySelector("#risk-status");
    const killBtn = root.querySelector("#risk-kill-btn");
    const killStatusEl = root.querySelector("#risk-kill-status");
    let killEngaged = false;

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function fmtPct(raw) {
      var n = Number(raw);
      if (!isFinite(n)) return esc(raw) + "%";
      return n.toFixed(2) + "%";
    }

    function renderKill(engaged) {
      killEngaged = !!engaged;
      killBtn.textContent = killEngaged ? "DISENGAGE KILL" : "ENGAGE KILL";
      killBtn.className = "btn danger" + (killEngaged ? " engaged" : "");
      killStatusEl.textContent = "engaged=" + String(killEngaged);
      killStatusEl.className = killEngaged ? "mono status-bad" : "mono muted";
    }

    function renderLimits(data) {
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
        "</dd>" +
        "<dt>paper_kill</dt><dd class=\"mono\">" +
        esc(String(data.paper_kill_engaged)) +
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
      if (typeof data.paper_kill_engaged === "boolean") {
        renderKill(data.paper_kill_engaged);
      }
    }

    function renderUtilization(data) {
      const used = data.used || {};
      const pct = data.pct || {};
      const lim = data.limits || {};
      utilEl.innerHTML =
        "<dt>used_qty (peak)</dt><dd class=\"mono num\">" +
        esc(used.qty) +
        " / " +
        esc(lim.max_qty) +
        "</dd>" +
        "<dt>pct_qty</dt><dd class=\"mono num\">" +
        esc(fmtPct(pct.qty)) +
        "</dd>" +
        "<dt>used_notional (gross)</dt><dd class=\"mono num\">" +
        esc(used.notional) +
        " / " +
        esc(lim.max_notional) +
        "</dd>" +
        "<dt>pct_notional</dt><dd class=\"mono num\">" +
        esc(fmtPct(pct.notional)) +
        "</dd>" +
        "<dt>symbols</dt><dd class=\"mono num\">" +
        esc(used.symbols) +
        "</dd>" +
        "<dt>marks_source</dt><dd class=\"mono\">" +
        esc(data.marks_source) +
        "</dd>";
      const rows = Array.isArray(data.positions) ? data.positions : [];
      if (!rows.length) {
        utilPosEl.textContent = "Sin posiciones abiertas.";
        return;
      }
      utilPosEl.innerHTML = rows
        .map(function (p) {
          return (
            esc(p.symbol) +
            ": qty=" +
            esc(p.qty) +
            " notional=" +
            esc(p.notional) +
            " (" +
            esc(fmtPct(p.pct_qty)) +
            " qty / " +
            esc(fmtPct(p.pct_notional)) +
            " notional)"
          );
        })
        .join("<br>");
    }

    async function refresh() {
      const data = await QLApi.risk();
      renderLimits(data);
      const util = await QLApi.riskUtilization();
      renderUtilization(util);
      const kill = await QLApi.paperKill();
      renderKill(kill.engaged);
      statusEl.textContent = "ok";
      statusEl.className = "mono muted status-ok";
    }

    root.querySelector("#risk-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });

    killBtn.addEventListener("click", function () {
      QLApi.setPaperKill(!killEngaged)
        .then(function (data) {
          renderKill(data.engaged);
          statusEl.textContent = data.engaged ? "kill ENGAGED" : "kill clear";
          statusEl.className = data.engaged ? "mono status-bad" : "mono muted status-ok";
        })
        .catch(function (err) {
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
