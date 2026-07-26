/** Panel Alpha Scanner. */
(function (global) {
  "use strict";

  function createScannerPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Alpha Scanner</h3>" +
      '<p class="muted" style="margin-top:0">Ranking sobre universo sintético WB:A/B/C.</p>' +
      '<div class="pane-row">' +
      '<label class="field">top_n<input id="sc-top" type="number" value="3" min="1" max="10" /></label>' +
      '<button type="button" class="btn" id="sc-run">Escanear</button>' +
      '<span class="mono" id="sc-status">—</span>' +
      "</div>" +
      '<div id="sc-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#sc-run", "#sc-status", "#sc-out", function () {
      const topN = parseInt(root.querySelector("#sc-top").value, 10) || 3;
      return QLApi.labScanner({ top_n: topN });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createScannerPane = createScannerPane;
})(window);
