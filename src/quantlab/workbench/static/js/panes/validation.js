/** Panel Validation splits info. */
(function (global) {
  "use strict";

  function createValidationPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Validation splits</h3>" +
      '<p class="muted" style="margin-top:0">train/val/OOS + walk-forward sobre barras sintéticas.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="vl-run">Calcular</button>' +
      '<span class="mono" id="vl-status">—</span>' +
      "</div>" +
      '<div id="vl-out"></div>' +
      "</div>";

    const status = root.querySelector("#vl-status");
    const out = root.querySelector("#vl-out");

    async function refresh() {
      const data = await QLApi.labValidation();
      QLLabUI.setStatus(status, true, "OK");
      out.innerHTML = QLLabUI.preJson(data);
    }

    root.querySelector("#vl-run").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createValidationPane = createValidationPane;
})(window);
