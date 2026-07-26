/** Panel Experiment Registry. */
(function (global) {
  "use strict";

  function createExperimentsPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Experiment Registry</h3>" +
      '<p class="muted" style="margin-top:0">Lista SQLite de sesión (tmp) — demo draft si vacío.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="ex-refresh">Listar</button>' +
      '<span class="mono" id="ex-status">—</span>' +
      "</div>" +
      '<div id="ex-out"></div>' +
      "</div>";

    const status = root.querySelector("#ex-status");
    const out = root.querySelector("#ex-out");

    async function refresh() {
      const data = await QLApi.labExperiments();
      QLLabUI.setStatus(status, true, "n=" + data.count);
      out.innerHTML = QLLabUI.preJson(data);
    }

    root.querySelector("#ex-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createExperimentsPane = createExperimentsPane;
})(window);
