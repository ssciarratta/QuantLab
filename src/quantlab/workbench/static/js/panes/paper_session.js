/** Panel Sesión Paper — strategy catalog + start/step/stop (F26/F27). */
(function (global) {
  "use strict";

  function createPaperSessionPane() {
    const root = document.createElement("div");
    root.className = "pane-paper-session";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Sesión Paper</h3>" +
      '<p class="muted" style="margin-top:0">Estrategia → risk → PaperBroker. Nunca place_order LIVE.</p>' +
      '<div class="pane-row">' +
      '<label class="field">Estrategia<select id="ps-strategy"></select></label>' +
      '<label class="field">Símbolo<input id="ps-symbol" type="text" placeholder="símbolo MD" /></label>' +
      "</div>" +
      '<div class="pane-row" id="ps-params-row"></div>' +
      '<div class="pane-row">' +
      '<label class="field">Max steps<input id="ps-max" type="number" min="1" max="10000" value="20" /></label>' +
      '<label class="field">Interval ms (opc)<input id="ps-interval" type="number" min="0" placeholder="manual" /></label>' +
      "</div>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="ps-start">Start</button>' +
      '<button type="button" class="btn secondary" id="ps-step">Step</button>' +
      '<button type="button" class="btn secondary" id="ps-stop">Stop</button>' +
      '<button type="button" class="btn secondary" id="ps-refresh">Status</button>' +
      "</div>" +
      '<p class="mono" id="ps-status">running=false · steps=0</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Log</h3>" +
      '<pre class="mono" id="ps-log" style="max-height:220px;overflow:auto;white-space:pre-wrap;margin:0"></pre>' +
      "</div>";

    const statusEl = root.querySelector("#ps-status");
    const logEl = root.querySelector("#ps-log");
    const selectEl = root.querySelector("#ps-strategy");
    const paramsRow = root.querySelector("#ps-params-row");
    const lines = [];
    let catalog = [];

    function appendLog(msg) {
      const ts = new Date().toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      lines.push("[" + ts + "] " + msg);
      if (lines.length > 80) lines.shift();
      logEl.textContent = lines.join("\n");
      logEl.scrollTop = logEl.scrollHeight;
    }

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
      const keys = Object.keys(meta.default_params);
      keys.forEach(function (key) {
        const val = meta.default_params[key];
        const label = document.createElement("label");
        label.className = "field";
        label.textContent = key;
        const input = document.createElement("input");
        input.id = "ps-param-" + key;
        input.dataset.paramKey = key;
        input.type = typeof val === "number" ? "number" : "text";
        input.value = val == null ? "" : String(val);
        label.appendChild(input);
        paramsRow.appendChild(label);
      });
    }

    function collectParams() {
      const params = {};
      const inputs = paramsRow.querySelectorAll("input[data-param-key]");
      inputs.forEach(function (input) {
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

    function fillStrategySelect(strategies) {
      catalog = strategies || [];
      selectEl.innerHTML = "";
      if (!catalog.length) {
        ["dummy", "buy_once", "momentum", "inventory_mm", "avellaneda_stoikov"].forEach(
          function (id) {
            const opt = document.createElement("option");
            opt.value = id;
            opt.textContent = id;
            selectEl.appendChild(opt);
          }
        );
        return;
      }
      catalog.forEach(function (s) {
        const opt = document.createElement("option");
        opt.value = s.id;
        const tags = (s.tags || []).join(",");
        opt.textContent = s.name ? s.name + " (" + s.id + ")" + (tags ? " [" + tags + "]" : "") : s.id;
        selectEl.appendChild(opt);
      });
      renderParams();
    }

    selectEl.addEventListener("change", renderParams);

    function renderStatus(st) {
      if (!st) {
        statusEl.textContent = "running=false · steps=0";
        return;
      }
      statusEl.textContent =
        "running=" +
        !!st.running +
        " · steps=" +
        (st.steps != null ? st.steps : 0) +
        " · strategy=" +
        (st.strategy_id || "—") +
        " · err=" +
        (st.last_error || "—");
    }

    async function refreshStatus() {
      const st = await QLApi.paperSessionStatus();
      renderStatus(st);
      return st;
    }

    async function loadCatalog() {
      try {
        const res = await QLApi.labStrategies();
        fillStrategySelect(res.strategies || []);
      } catch (err) {
        fillStrategySelect([]);
        appendLog("CATALOG fallback: " + err.message);
      }
    }

    root.querySelector("#ps-start").addEventListener("click", async function () {
      const strategy_id = selectEl.value;
      const symbol = root.querySelector("#ps-symbol").value.trim();
      const maxRaw = root.querySelector("#ps-max").value;
      const intervalRaw = root.querySelector("#ps-interval").value.trim();
      if (!symbol) {
        appendLog("ERROR: símbolo requerido");
        return;
      }
      const body = {
        strategy_id: strategy_id,
        symbol: symbol,
        max_steps: parseInt(maxRaw, 10) || 20,
        params: collectParams(),
      };
      if (intervalRaw) {
        const iv = parseInt(intervalRaw, 10);
        if (iv > 0) body.interval_ms = iv;
      }
      try {
        const res = await QLApi.paperSessionStart(body);
        renderStatus(res.status || res);
        appendLog("START " + strategy_id + " @ " + symbol);
      } catch (err) {
        appendLog("START ERROR: " + err.message);
      }
    });

    root.querySelector("#ps-step").addEventListener("click", async function () {
      try {
        const res = await QLApi.paperSessionStep();
        renderStatus({
          running: res.running,
          steps: res.step,
          strategy_id: res.strategy_id,
          last_error: res.last_error,
        });
        const actions = res.actions || [];
        const summary = actions
          .map(function (a) {
            return (a.intent_type || "?") + "→" + (a.status || "?");
          })
          .join(", ");
        appendLog("STEP #" + res.step + " " + (summary || "sin intents"));
      } catch (err) {
        appendLog("STEP ERROR: " + err.message);
      }
    });

    root.querySelector("#ps-stop").addEventListener("click", async function () {
      try {
        const res = await QLApi.paperSessionStop();
        renderStatus(res.status || res);
        appendLog("STOP");
      } catch (err) {
        appendLog("STOP ERROR: " + err.message);
      }
    });

    root.querySelector("#ps-refresh").addEventListener("click", function () {
      refreshStatus()
        .then(function (st) {
          appendLog("STATUS running=" + !!st.running + " steps=" + (st.steps || 0));
        })
        .catch(function (err) {
          appendLog("STATUS ERROR: " + err.message);
        });
    });

    root.refresh = async function () {
      await loadCatalog();
      try {
        await refreshStatus();
        const instruments = await QLApi.instruments();
        const list = instruments.instruments || [];
        const input = root.querySelector("#ps-symbol");
        if (input && !input.value && list.length) {
          input.value = list[0].symbol || "";
        }
      } catch (err) {
        /* broker puede no estar conectado aún */
      }
    };

    loadCatalog();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createPaperSessionPane = createPaperSessionPane;
})(window);
