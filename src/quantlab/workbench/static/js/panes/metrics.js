/** Panel Metrics / último resultado lab. */
(function (global) {
  "use strict";

  function createMetricsPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Último resultado</h3>" +
      '<p class="muted" style="margin-top:0">Métricas / payload del último run lab en esta sesión.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="mt-refresh">Actualizar</button>' +
      '<span class="mono" id="mt-status">—</span>' +
      "</div>" +
      '<div id="mt-out"></div>' +
      "</div>";

    const status = root.querySelector("#mt-status");
    const out = root.querySelector("#mt-out");

    async function refresh() {
      const data = await QLApi.labMetrics();
      QLLabUI.setStatus(status, true, data.has_result ? "con resultado" : "vacío");
      out.innerHTML = QLLabUI.preJson(data);
    }

    root.querySelector("#mt-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMetricsPane = createMetricsPane;
})(window);
