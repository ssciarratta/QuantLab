/** Panel Monte Carlo — historial + intervalos CI (F34). */
(function (global) {
  "use strict";

  function createMonteCarloPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-montecarlo";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Monte Carlo</h3>" +
      '<p class="muted" style="margin-top:0">N escenarios pequeños · CI 95% · persiste en <span class="mono">session/montecarlo</span>.</p>' +
      '<div class="pane-row">' +
      '<label class="field">N<input id="mc-n" type="number" value="5" min="2" max="20" /></label>' +
      '<label class="field">bars<input id="mc-bars" type="number" value="16" min="8" max="60" /></label>' +
      '<button type="button" class="btn" id="mc-run">Simular</button>' +
      '<button type="button" class="btn secondary" id="mc-refresh">Actualizar</button>' +
      '<span class="mono" id="mc-status">—</span>' +
      "</div>" +
      '<p class="muted mono" id="mc-meta">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Intervalos</h3>" +
      '<p class="mono" id="mc-ci">—</p>' +
      '<div id="mc-ci-bar"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Historial sesión</h3>" +
      '<div id="mc-runs"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Raw</h3>" +
      '<div id="mc-out"></div>' +
      "</div>";

    const status = root.querySelector("#mc-status");
    const meta = root.querySelector("#mc-meta");
    const ciEl = root.querySelector("#mc-ci");
    const ciBar = root.querySelector("#mc-ci-bar");
    const runsEl = root.querySelector("#mc-runs");
    const out = root.querySelector("#mc-out");

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function renderCiBar(data) {
      const low = data && data.ci_low != null ? Number(data.ci_low) : null;
      const high = data && data.ci_high != null ? Number(data.ci_high) : null;
      const mean = data && data.mean_equity != null ? Number(data.mean_equity) : null;
      if (low == null || high == null || mean == null || !(high > low)) {
        ciBar.innerHTML = "";
        return;
      }
      const pad = high - low || 1;
      const pct = Math.max(0, Math.min(100, ((mean - low) / pad) * 100));
      ciBar.innerHTML =
        '<div class="mc-ci-track" style="position:relative;height:10px;background:rgba(127,127,127,0.2);margin-top:0.35rem">' +
        '<div style="position:absolute;left:0;top:0;bottom:0;width:100%;opacity:0.35;background:var(--accent,#2a6)"></div>' +
        '<div style="position:absolute;left:' +
        pct.toFixed(1) +
        '%;top:-2px;width:2px;height:14px;background:currentColor" title="mean"></div>' +
        "</div>";
    }

    function renderResult(data) {
      if (!data) {
        ciEl.textContent = "sin corridas — corré simular";
        ciBar.innerHTML = "";
        out.innerHTML = "";
        return;
      }
      const ok = data.ok !== false;
      QLLabUI.setStatus(
        status,
        ok,
        ok
          ? "OK · n=" +
              (data.n_scenarios != null ? data.n_scenarios : "?") +
              " · CI95"
          : "FAIL"
      );
      meta.textContent =
        "seed=" +
        (data.seed != null ? data.seed : "?") +
        " · n_bars=" +
        (data.n_bars != null ? data.n_bars : "?") +
        (data.run_id ? " · " + data.run_id : "") +
        (data.persisted ? " · persisted" : " · preview") +
        (data.path ? " · " + data.path : "");

      ciEl.textContent =
        "mean=" +
        (data.mean_equity != null ? Number(data.mean_equity).toFixed(4) : "?") +
        " · std=" +
        (data.std_equity != null ? Number(data.std_equity).toFixed(4) : "?") +
        " · CI95=[" +
        (data.ci_low != null ? Number(data.ci_low).toFixed(4) : "?") +
        ", " +
        (data.ci_high != null ? Number(data.ci_high).toFixed(4) : "?") +
        "]";
      renderCiBar(data);
      out.innerHTML = QLLabUI.preJson(data);
    }

    function renderRuns(listPayload) {
      const runs = (listPayload && listPayload.runs) || [];
      if (!runs.length) {
        runsEl.innerHTML =
          '<p class="muted mono">sin corridas — corré simular</p>';
        return;
      }
      runsEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>run_id</th><th>n</th><th>mean</th><th>CI low</th><th>CI high</th>" +
        "</tr></thead><tbody>" +
        runs
          .map(function (r) {
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(r.run_id) +
              "</td>" +
              '<td class="num">' +
              esc(r.n_scenarios != null ? r.n_scenarios : "—") +
              "</td>" +
              '<td class="num">' +
              esc(
                r.mean_equity != null ? Number(r.mean_equity).toFixed(2) : "—"
              ) +
              "</td>" +
              '<td class="num">' +
              esc(r.ci_low != null ? Number(r.ci_low).toFixed(2) : "—") +
              "</td>" +
              '<td class="num">' +
              esc(r.ci_high != null ? Number(r.ci_high).toFixed(2) : "—") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    async function refresh() {
      const data = await QLApi.labMonteCarloHistory();
      const source = data.latest || null;
      renderResult(source);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    root.querySelector("#mc-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    QLLabUI.bindRun(root, "#mc-run", "#mc-status", "#mc-out", function () {
      const n = parseInt(root.querySelector("#mc-n").value, 10) || 5;
      const bars = parseInt(root.querySelector("#mc-bars").value, 10) || 16;
      return QLApi.labMonteCarlo({ n_scenarios: n, n_bars: bars }).then(
        function (data) {
          renderResult(data);
          refresh().catch(function () {});
          return data;
        }
      );
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonteCarloPane = createMonteCarloPane;
})(window);
