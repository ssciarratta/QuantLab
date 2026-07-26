/** Panel Hummingbot export (path-safe, live_routing false). */
(function (global) {
  "use strict";

  function createExportHbPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Hummingbot export</h3>" +
      '<p class="muted" style="margin-top:0">validate → build → export a sandbox tmp. LIVE routing bloqueado.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="hb-run">Exportar</button>' +
      '<span class="mono" id="hb-status">—</span>' +
      "</div>" +
      '<div id="hb-out"></div>' +
      "</div>";

    QLLabUI.bindRun(root, "#hb-run", "#hb-status", "#hb-out", function () {
      return QLApi.labExportHb({ experiment_id: "wb-hb-export", strategy_version: "demo-1" });
    });

    root.refresh = async function () {};
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createExportHbPane = createExportHbPane;
})(window);
