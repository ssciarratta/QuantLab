/** Panel Optimizer grid mini. */
(function (global) {
  "use strict";

  function createOptimizePane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Optimizer grid</h3>" +
      '<p class="muted" style="margin-top:0">Grid lookback×quantity → sharpe (máx 12 trials).</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="op-run">Optimizar</button>' +
      '<span class="mono" id="op-status">—</span>' +
      "</div>" +
      '<div id="op-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#op-run", "#op-status", "#op-out", function () {
      return QLApi.labOptimize({ lookbacks: [2, 3], quantities: ["1"], n_bars: 20 });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createOptimizePane = createOptimizePane;
})(window);
