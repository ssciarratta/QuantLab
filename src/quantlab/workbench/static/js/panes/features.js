/** Panel Features pipeline demo. */
(function (global) {
  "use strict";

  function createFeaturesPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Features pipeline</h3>" +
      '<p class="muted" style="margin-top:0">close_price + simple_return sobre sintéticos.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="ft-run">Correr pipeline</button>' +
      '<span class="mono" id="ft-status">—</span>' +
      "</div>" +
      '<div id="ft-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#ft-run", "#ft-status", "#ft-out", function () {
      return QLApi.labFeatures({ n_bars: 20 });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createFeaturesPane = createFeaturesPane;
})(window);
