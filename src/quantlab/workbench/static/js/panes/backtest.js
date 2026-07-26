/** Panel Backtest bar-based (datos sintéticos). */
(function (global) {
  "use strict";

  function createBacktestPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Backtest 5A</h3>" +
      '<p class="muted" style="margin-top:0">Estrategia sobre barras sintéticas — research-safe, sin LIVE.</p>' +
      '<div class="pane-row">' +
      '<label class="field">Estrategia<select id="bt-strategy">' +
      '<option value="momentum">momentum</option>' +
      '<option value="dummy">dummy</option>' +
      '<option value="buy_once">buy_once</option>' +
      "</select></label>" +
      '<label class="field">n_bars<input id="bt-nbars" type="number" value="24" min="4" max="120" /></label>' +
      "</div>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="bt-run">Correr</button>' +
      '<span class="mono" id="bt-status">—</span>' +
      "</div>" +
      '<div id="bt-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#bt-run", "#bt-status", "#bt-out", function () {
      const strategy = root.querySelector("#bt-strategy").value;
      const nBars = parseInt(root.querySelector("#bt-nbars").value, 10) || 24;
      return QLApi.labBacktest({ strategy_id: strategy, n_bars: nBars });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBacktestPane = createBacktestPane;
})(window);
