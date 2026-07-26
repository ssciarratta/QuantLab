/** Panel Monte Carlo mini. */
(function (global) {
  "use strict";

  function createMonteCarloPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Monte Carlo</h3>" +
      '<p class="muted" style="margin-top:0">N escenarios pequeños sobre barras sintéticas.</p>' +
      '<div class="pane-row">' +
      '<label class="field">N<input id="mc-n" type="number" value="5" min="2" max="20" /></label>' +
      '<button type="button" class="btn" id="mc-run">Simular</button>' +
      '<span class="mono" id="mc-status">—</span>' +
      "</div>" +
      '<div id="mc-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#mc-run", "#mc-status", "#mc-out", function () {
      const n = parseInt(root.querySelector("#mc-n").value, 10) || 5;
      return QLApi.labMonteCarlo({ n_scenarios: n, n_bars: 16 });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonteCarloPane = createMonteCarloPane;
})(window);
