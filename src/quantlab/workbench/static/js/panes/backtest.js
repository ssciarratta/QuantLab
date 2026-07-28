/** Panel Backtest bar-based — catálogo estrategias F27. */
(function (global) {
  "use strict";

  function createBacktestPane() {
    const root = document.createElement("div");
    root.className = "pane-lab";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Backtest 5A</h3>" +
      '<p class="muted" style="margin-top:0">' +
      '<span class="data-badge data-badge-synth">SINTÉTICO lab</span> ' +
      "Barras inventadas del laboratorio — no son klines de Binance. Research-safe, sin LIVE.</p>" +
      '<div class="pane-row">' +
      '<label class="field">Estrategia<select id="bt-strategy"></select></label>' +
      '<label class="field">n_bars<input id="bt-nbars" type="number" value="120" min="4" max="2000" /></label>' +
      "</div>" +
      '<div class="pane-row" id="bt-params-row"></div>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="bt-run">Correr</button>' +
      '<button type="button" class="btn secondary" id="bt-to-mc" disabled title="Requiere un backtest corrido con report_id">→ Monte Carlo</button>' +
      '<span class="mono" id="bt-status">—</span>' +
      "</div>" +
      '<div id="bt-out"></div>' +
      "</div>";

    const selectEl = root.querySelector("#bt-strategy");
    const paramsRow = root.querySelector("#bt-params-row");
    const btnMc = root.querySelector("#bt-to-mc");
    let catalog = [];
    let lastResult = null;

    function currentMeta() {
      const id = selectEl.value;
      for (let i = 0; i < catalog.length; i++) {
        if (catalog[i].id === id) return catalog[i];
      }
      return null;
    }

    function renderParams() {
      const meta = currentMeta();
      paramsRow.innerHTML = "";
      if (!meta || !meta.default_params) return;
      Object.keys(meta.default_params).forEach(function (key) {
        const val = meta.default_params[key];
        const label = document.createElement("label");
        label.className = "field";
        label.textContent = key;
        const input = document.createElement("input");
        input.dataset.paramKey = key;
        input.type = typeof val === "number" ? "number" : "text";
        input.value = val == null ? "" : String(val);
        label.appendChild(input);
        paramsRow.appendChild(label);
      });
    }

    function collectParams() {
      const params = {};
      paramsRow.querySelectorAll("input[data-param-key]").forEach(function (input) {
        const key = input.dataset.paramKey;
        const raw = input.value.trim();
        if (!raw) return;
        if (input.type === "number") {
          const n = Number(raw);
          params[key] = Number.isFinite(n) ? n : raw;
        } else {
          params[key] = raw;
        }
      });
      return params;
    }

    function fillSelect(strategies) {
      catalog = strategies || [];
      selectEl.innerHTML = "";
      const list = catalog.length
        ? catalog
        : [
            { id: "momentum", name: "momentum", family: "momentum", runnable: true },
            { id: "buy_once", name: "buy_once", family: "demo", runnable: true },
            { id: "inventory_mm", name: "inventory_mm", family: "market_making", runnable: true },
          ];
      const byFamily = {};
      list.forEach(function (s) {
        const fam = s.family || "other";
        if (!byFamily[fam]) byFamily[fam] = [];
        byFamily[fam].push(s);
      });
      Object.keys(byFamily)
        .sort()
        .forEach(function (fam) {
          const group = document.createElement("optgroup");
          group.label = fam;
          byFamily[fam].forEach(function (s) {
            const opt = document.createElement("option");
            opt.value = s.id;
            const stub = s.runnable === false ? " [stub]" : "";
            const bn = s.runnable !== false ? " · binance-ready" : "";
            opt.textContent = (s.name || s.id) + stub + bn;
            opt.disabled = s.runnable === false;
            if (s.description) opt.title = s.description;
            group.appendChild(opt);
          });
          selectEl.appendChild(group);
        });
      if (!catalog.length) catalog = list;
      renderParams();
    }

    selectEl.addEventListener("change", renderParams);

    root.querySelector("#bt-run").addEventListener("click", function () {
      const status = root.querySelector("#bt-status");
      const out = root.querySelector("#bt-out");
      const strategy = selectEl.value;
      const nBars = parseInt(root.querySelector("#bt-nbars").value, 10) || 24;
      status.textContent = "ejecutando…";
      status.className = "mono muted";
      btnMc.disabled = true;
      QLApi.labBacktest({
        strategy_id: strategy,
        n_bars: nBars,
        params: collectParams(),
      })
        .then(function (data) {
          lastResult = data;
          QLLabUI.setStatus(status, true, "OK");
          out.innerHTML = QLLabUI.preJson(data);
          const rid = data.report_id || null;
          btnMc.disabled = !rid;
          if (rid) {
            out.innerHTML +=
              '<p class="muted">report_id=<span class="mono">' +
              QLLabUI.escapeHtml(rid) +
              "</span> — usá → Monte Carlo para robustez.</p>";
          }
        })
        .catch(function (err) {
          lastResult = null;
          QLLabUI.setStatus(status, false, err.message || String(err));
          out.innerHTML = "";
          btnMc.disabled = true;
        });
    });

    btnMc.addEventListener("click", function () {
      if (!lastResult || !lastResult.report_id) return;
      const prefill = {
        backtest_id: lastResult.report_id,
        strategy_id: lastResult.strategy_id || selectEl.value,
        n_bars: lastResult.n_bars || null,
        mode: "normal",
      };
      if (global.QLNav) {
        global.QLNav.open("montecarlo", {
          prefill: prefill,
          message: "Desde Backtest " + lastResult.report_id,
        });
      } else if (global.QLShell) {
        global.QLShell.open("montecarlo", { prefill: prefill });
      }
    });

    root.applyNavFocus = function () {
      /* reservado: prefill estrategia desde MC */
    };

    root.refresh = async function () {
      try {
        const res = await QLApi.labStrategies();
        fillSelect(res.strategies || []);
      } catch (err) {
        fillSelect([]);
      }
    };

    root.refresh();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBacktestPane = createBacktestPane;
})(window);
