/** Guided Lab — wizard amigable venue→scan→estrategia→simular (F99). PAPER only. */
(function (global) {
  "use strict";

  function createGuidedLabPane() {
    const root = document.createElement("div");
    root.className = "pane-guided-lab";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Guided Lab</h3>" +
      '<p class="muted" style="margin-top:0">Flujo amigable: venue → scan → estrategia → simular. ' +
      "<strong>Solo paper/simulación.</strong> LIVE está bloqueado.</p>" +
      '<div class="mono status-ok" id="gl-live">LIVE_BLOCKED = True</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>1. Venue</h3>" +
      '<select id="gl-venue">' +
      '<option value="paper">paper (simulado)</option>' +
      '<option value="binance">binance (MD fake / paper)</option>' +
      '<option value="a3">a3 (MD fake / paper)</option>' +
      "</select>" +
      '<p class="muted" style="margin-bottom:0">Conectar broker es opcional para simular. El backtest lab usa barras sintéticas.</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>2. Escanear universo</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="gl-scan">Escanear</button>' +
      '<span class="mono muted" id="gl-scan-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-scan-out">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>3. Estrategia</h3>" +
      '<select id="gl-strategy">' +
      '<option value="momentum">momentum</option>' +
      '<option value="buy_once">buy_once</option>' +
      "</select>" +
      '<label class="muted"> n_bars <input type="number" id="gl-bars" value="24" min="4" max="120" style="width:4em"></label>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>4. Simular (paper)</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="gl-run">Simular backtest</button>' +
      '<span class="mono muted" id="gl-run-status">—</span>' +
      "</div>" +
      '<dl class="kv" id="gl-result"></dl>' +
      '<p class="muted">Próximo paso de producto: Binance MD real → paper → LIVE gated (requiere aprobación).</p>' +
      "</div>";

    const scanOut = root.querySelector("#gl-scan-out");
    const scanStatus = root.querySelector("#gl-scan-status");
    const runStatus = root.querySelector("#gl-run-status");
    const resultEl = root.querySelector("#gl-result");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    root.querySelector("#gl-scan").addEventListener("click", function () {
      scanStatus.textContent = "escaneando…";
      QLApi.labScanner({ top_n: 3 })
        .then(function (data) {
          scanStatus.textContent = "ok";
          scanStatus.className = "mono status-ok";
          const selected = data.selected || [];
          const scores = data.scores || [];
          scanOut.innerHTML = selected
            .map(function (id, i) {
              const sc = scores[i] || {};
              return (
                esc(id) +
                ' <span class="muted">composite=' +
                esc(sc.composite) +
                "</span>"
              );
            })
            .join("<br>");
        })
        .catch(function (err) {
          scanStatus.textContent = "error: " + err.message;
          scanStatus.className = "mono status-bad";
        });
    });

    root.querySelector("#gl-run").addEventListener("click", function () {
      const strategy = root.querySelector("#gl-strategy").value;
      const nBars = Number(root.querySelector("#gl-bars").value) || 24;
      runStatus.textContent = "simulando…";
      resultEl.innerHTML = "";
      QLApi.labBacktest({ strategy_id: strategy, n_bars: nBars })
        .then(function (data) {
          runStatus.textContent = data.ok ? "simulación ok (paper)" : "falló";
          runStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          resultEl.innerHTML =
            "<dt>venue elegido</dt><dd class=\"mono\">" +
            esc(root.querySelector("#gl-venue").value) +
            "</dd>" +
            "<dt>strategy</dt><dd class=\"mono\">" +
            esc(data.strategy_id) +
            "</dd>" +
            "<dt>final_equity</dt><dd class=\"mono num\">" +
            esc(data.final_equity) +
            "</dd>" +
            "<dt>fills</dt><dd class=\"mono num\">" +
            esc(data.n_fills) +
            "</dd>" +
            "<dt>live_blocked</dt><dd class=\"mono\">" +
            esc(data.live_blocked) +
            "</dd>" +
            "<dt>live_routing</dt><dd class=\"mono\">" +
            esc(data.live_routing) +
            "</dd>";
        })
        .catch(function (err) {
          runStatus.textContent = "error: " + err.message;
          runStatus.className = "mono status-bad";
        });
    });

    root.refresh = function () {
      return Promise.resolve();
    };
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createGuidedLabPane = createGuidedLabPane;
})(window);
