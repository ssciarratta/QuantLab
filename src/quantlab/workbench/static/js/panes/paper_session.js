/** Panel Sesión Paper — strategy start/step/stop + log (F26). */
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
      '<label class="field">Estrategia<select id="ps-strategy">' +
      '<option value="dummy">dummy</option>' +
      '<option value="buy_once">buy_once</option>' +
      '<option value="momentum">momentum</option>' +
      "</select></label>" +
      '<label class="field">Símbolo<input id="ps-symbol" type="text" placeholder="símbolo MD" /></label>' +
      "</div>" +
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
    const lines = [];

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

    root.querySelector("#ps-start").addEventListener("click", async function () {
      const strategy_id = root.querySelector("#ps-strategy").value;
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

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createPaperSessionPane = createPaperSessionPane;
})(window);
