/** Panel Hummingbot export wizard — experiments + validate/build/export (F34). */
(function (global) {
  "use strict";

  function createExportHbPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-export-hb";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Hummingbot export</h3>' +
      '<p class="muted pane-sub">validate → build → export</p></div>' +
      '<p class="banner-warn mono" id="hb-banner" style="margin:0.2rem 0;padding:0.3rem 0.45rem;border:1px solid rgba(180,120,40,0.45);background:rgba(180,120,40,0.12);white-space:pre-wrap">live_routing:false — research-safe</p>' +
      '<div class="pane-toolbar">' +
      '<label>experiment <select id="hb-exp" class="mono"></select></label>' +
      '<label>strategy_ver <input type="text" id="hb-ver" class="mono" value="demo-1"></label>' +
      "</div>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn" id="hb-run">Validate · Build · Export</button>' +
      '<button type="button" class="btn secondary" id="hb-refresh">Actualizar</button>' +
      '<span class="mono" id="hb-status">—</span>' +
      "</div>" +
      '<p class="muted mono" id="hb-meta">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Pasos</h3>" +
      '<pre class="mono" id="hb-steps" style="white-space:pre-wrap;font-size:0.78rem;margin:0">—</pre>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Exports previos</h3>" +
      '<div id="hb-exports"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Raw</h3>" +
      '<div id="hb-out"></div>' +
      "</div>";

    const status = root.querySelector("#hb-status");
    const meta = root.querySelector("#hb-meta");
    const stepsEl = root.querySelector("#hb-steps");
    const exportsEl = root.querySelector("#hb-exports");
    const out = root.querySelector("#hb-out");
    const expSel = root.querySelector("#hb-exp");

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function fillExperiments(listPayload) {
      const rows = (listPayload && listPayload.experiments) || [];
      const prev = expSel.value;
      expSel.innerHTML = "";
      if (!rows.length) {
        const opt = document.createElement("option");
        opt.value = "wb-hb-export";
        opt.textContent = "wb-hb-export (fallback)";
        expSel.appendChild(opt);
        return;
      }
      rows.forEach(function (r) {
        const opt = document.createElement("option");
        opt.value = r.experiment_id;
        opt.textContent =
          r.experiment_id +
          (r.strategy_version ? " · " + r.strategy_version : "") +
          (r.status ? " [" + r.status + "]" : "");
        if (r.strategy_version) {
          opt.dataset.strategyVersion = r.strategy_version;
        }
        expSel.appendChild(opt);
      });
      if (prev) {
        expSel.value = prev;
      }
    }

    function renderExports(listPayload) {
      const rows = (listPayload && listPayload.exports) || [];
      if (listPayload && listPayload.banner) {
        root.querySelector("#hb-banner").textContent = listPayload.banner;
      }
      if (!rows.length) {
        exportsEl.innerHTML =
          '<p class="muted mono">sin exports — corré validate/build/export</p>';
        return;
      }
      exportsEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>export_id</th><th>experiment</th><th>live_routing</th><th>created</th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (r) {
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(r.export_id) +
              "</td>" +
              '<td class="mono">' +
              esc(r.experiment_id) +
              "</td>" +
              '<td class="mono">' +
              esc(r.live_routing === true ? "true" : "false") +
              "</td>" +
              '<td class="mono">' +
              esc(r.created_at || "—") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    function renderResult(data) {
      if (!data) {
        stepsEl.textContent = "—";
        out.innerHTML = "";
        return;
      }
      const ok = data.ok !== false;
      QLLabUI.setStatus(
        status,
        ok,
        ok ? "OK · live_routing:false" : "FAIL"
      );
      meta.textContent =
        (data.experiment_id || "?") +
        (data.export_id ? " · " + data.export_id : "") +
        (data.path ? " · " + data.path : "");
      const steps = data.steps || {};
      stepsEl.textContent = JSON.stringify(
        {
          banner: data.banner || "live_routing:false",
          live_routing: data.live_routing,
          blocked: data.blocked,
          steps: steps,
        },
        null,
        2
      );
      out.innerHTML = QLLabUI.preJson(data);
    }

    async function refresh() {
      const [exps, exportsList] = await Promise.all([
        QLApi.labExperiments(),
        QLApi.labExports(),
      ]);
      fillExperiments(exps);
      renderExports(exportsList);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(
          status,
          true,
          "exports " + (exportsList.count || 0)
        );
      }
    }

    expSel.addEventListener("change", function () {
      const opt = expSel.options[expSel.selectedIndex];
      if (opt && opt.dataset.strategyVersion) {
        root.querySelector("#hb-ver").value = opt.dataset.strategyVersion;
      }
    });

    root.querySelector("#hb-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    QLLabUI.bindRun(root, "#hb-run", "#hb-status", "#hb-out", function () {
      const experimentId = expSel.value || "wb-hb-export";
      const strategyVersion =
        root.querySelector("#hb-ver").value.trim() || "demo-1";
      return QLApi.labExportHb({
        experiment_id: experimentId,
        strategy_version: strategyVersion,
      }).then(function (data) {
        renderResult(data);
        refresh().catch(function () {});
        return data;
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createExportHbPane = createExportHbPane;
})(window);
