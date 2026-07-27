/** Guided Lab — wizard venue→scan→estrategia→simular + LIVE unlock (F99/F100). */
(function (global) {
  "use strict";

  function createGuidedLabPane() {
    const root = document.createElement("div");
    root.className = "pane-guided-lab";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Guided Lab</h3>" +
      '<p class="muted" style="margin-top:0">Flujo: venue → scan → estrategia → simular. ' +
      "LIVE solo tras usuario/contraseña (corte humano). Sin unlock = bloqueado.</p>" +
      '<div class="mono" id="gl-live">LIVE_BLOCKED = True</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>0. Unlock LIVE (opcional)</h3>" +
      '<p class="muted" style="margin-top:0">Definí QUANTLAB_LIVE_USER / QUANTLAB_LIVE_PASSWORD en tu PC. ' +
      "Nunca se guardan en git ni en disco de sesión.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-user" placeholder="usuario" autocomplete="username">' +
      '<input type="password" id="gl-pass" placeholder="contraseña" autocomplete="current-password">' +
      '<button type="button" class="btn secondary" id="gl-unlock">Unlock</button>' +
      '<button type="button" class="btn secondary" id="gl-lock">Lock</button>' +
      "</div>" +
      '<span class="mono muted" id="gl-unlock-status">—</span>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>1. Venue</h3>" +
      '<select id="gl-venue">' +
      '<option value="binance">binance (MD público / demo)</option>' +
      '<option value="paper">paper (simulado)</option>' +
      '<option value="a3">a3 (MD fake / paper)</option>' +
      "</select>" +
      '<div class="pane-row" style="margin-top:0.5em">' +
      '<button type="button" class="btn secondary" id="gl-a3-connect">Conectar paper A3</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-instr">Listar instrumentos A3</button>' +
      '<span class="mono muted" id="gl-a3-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-a3-out">—</div>' +
      '<p class="muted">A3 en Guided Lab = PAPER (fills simulados). Sin routing venue A3.</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>2. Escanear</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="gl-scan">Scan lab sintético</button>' +
      '<button type="button" class="btn secondary" id="gl-scan-bn">Scan Binance USDT</button>' +
      '<span class="mono muted" id="gl-scan-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-scan-out">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>3. Estrategia</h3>" +
      '<select id="gl-strategy">' +
      '<option value="momentum">momentum</option>' +
      '<option value="buy_once">buy_once</option>' +
      "</select>" +
      '<label class="muted"> n_bars <input type="number" id="gl-bars" value="24" min="4" max="120" style="width:4em"></label>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>4. Simular (paper)</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="gl-run">Simular backtest</button>' +
      '<span class="mono muted" id="gl-run-status">—</span>' +
      "</div>" +
      '<dl class="kv" id="gl-result"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>5. Demo order (post-unlock)</h3>" +
      '<p class="muted" style="margin-top:0">Fill demo Binance. Requiere unlock. ' +
      "Default: sim local. Testnet remoto solo con QUANTLAB_DEMO_USE_TESTNET=1 + keys.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-demo-sym" value="BTCUSDT" style="width:7em">' +
      '<select id="gl-demo-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="gl-demo-qty" value="0.001" style="width:5em">' +
      '<button type="button" class="btn" id="gl-demo-submit">Enviar demo</button>' +
      '<span class="mono muted" id="gl-demo-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-demo-out">—</div>' +
      "</div>";

    const liveEl = root.querySelector("#gl-live");
    const scanOut = root.querySelector("#gl-scan-out");
    const scanStatus = root.querySelector("#gl-scan-status");
    const runStatus = root.querySelector("#gl-run-status");
    const resultEl = root.querySelector("#gl-result");
    const unlockStatus = root.querySelector("#gl-unlock-status");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function refreshLive() {
      return QLApi.liveStatus()
        .then(function (data) {
          const unlocked = data.unlocked === true;
          liveEl.textContent =
            "LIVE_BLOCKED=" +
            data.live_blocked +
            " · unlocked=" +
            unlocked +
            " · configured=" +
            data.credentials_configured;
          liveEl.className = unlocked ? "mono status-ok" : "mono status-bad";
          unlockStatus.textContent = unlocked
            ? "unlock activo (" + esc(data.venue_scope) + ")"
            : data.credentials_configured
              ? "bloqueado — ingresá user/pass"
              : "bloqueado — configurá env QUANTLAB_LIVE_USER/PASSWORD";
        })
        .catch(function (err) {
          liveEl.textContent = "live status error: " + err.message;
        });
    }

    root.querySelector("#gl-unlock").addEventListener("click", function () {
      const user = root.querySelector("#gl-user").value;
      const pass = root.querySelector("#gl-pass").value;
      unlockStatus.textContent = "validando…";
      QLApi.liveUnlock(user, pass, "binance_demo")
        .then(function () {
          root.querySelector("#gl-pass").value = "";
          return refreshLive();
        })
        .catch(function (err) {
          unlockStatus.textContent = "error: " + err.message;
          unlockStatus.className = "mono status-bad";
        });
    });

    root.querySelector("#gl-lock").addEventListener("click", function () {
      QLApi.liveLock()
        .then(function () {
          return refreshLive();
        })
        .catch(function (err) {
          unlockStatus.textContent = "error: " + err.message;
        });
    });

    const a3Status = root.querySelector("#gl-a3-status");
    const a3Out = root.querySelector("#gl-a3-out");
    root.querySelector("#gl-a3-connect").addEventListener("click", function () {
      a3Status.textContent = "conectando A3 paper…";
      root.querySelector("#gl-venue").value = "a3";
      QLApi.connect("a3", "paper", { md_source: "fake" })
        .then(function (data) {
          a3Status.textContent = data.ok ? "A3 paper conectado" : "falló";
          a3Status.className = data.ok ? "mono status-ok" : "mono status-bad";
          a3Out.textContent = esc(JSON.stringify(data.health || data, null, 0)).slice(0, 240);
        })
        .catch(function (err) {
          a3Status.textContent = "error: " + err.message;
          a3Status.className = "mono status-bad";
        });
    });
    root.querySelector("#gl-a3-instr").addEventListener("click", function () {
      a3Status.textContent = "listando…";
      QLApi.instruments()
        .then(function (data) {
          const items = data.instruments || data.items || [];
          a3Status.textContent = "ok (" + items.length + ")";
          a3Status.className = "mono status-ok";
          a3Out.innerHTML = items
            .slice(0, 12)
            .map(function (it) {
              return esc(it.symbol || it.instrument_id || JSON.stringify(it));
            })
            .join("<br>") || "—";
        })
        .catch(function (err) {
          a3Status.textContent = "error: " + err.message;
          a3Status.className = "mono status-bad";
        });
    });

    root.querySelector("#gl-scan").addEventListener("click", function () {
      scanStatus.textContent = "escaneando lab…";
      QLApi.labScanner({ top_n: 3 })
        .then(function (data) {
          scanStatus.textContent = "ok (lab)";
          scanStatus.className = "mono status-ok";
          const selected = data.selected || [];
          const scores = data.scores || [];
          scanOut.innerHTML = selected
            .map(function (id, i) {
              const sc = scores[i] || {};
              return esc(id) + ' <span class="muted">composite=' + esc(sc.composite) + "</span>";
            })
            .join("<br>");
        })
        .catch(function (err) {
          scanStatus.textContent = "error: " + err.message;
          scanStatus.className = "mono status-bad";
        });
    });

    root.querySelector("#gl-scan-bn").addEventListener("click", function () {
      scanStatus.textContent = "escaneando Binance…";
      QLApi.binanceScan(20)
        .then(function (data) {
          scanStatus.textContent = "ok (binance MD)";
          scanStatus.className = "mono status-ok";
          const symbols = data.symbols || [];
          const tickers = data.tickers || [];
          scanOut.innerHTML =
            "símbolos=" +
            esc(data.n_symbols) +
            "<br>" +
            tickers
              .map(function (t) {
                return esc(t.symbol) + " bid=" + esc(t.bid) + " ask=" + esc(t.ask);
              })
              .join("<br>") +
            (symbols.length
              ? "<br><span class=\"muted\">…" + esc(symbols.slice(0, 5).join(", ")) + "</span>"
              : "");
        })
        .catch(function (err) {
          scanStatus.textContent = "error: " + err.message;
          scanStatus.className = "mono status-bad";
        });
    });

    root.querySelector("#gl-run").addEventListener("click", function () {
      const strategy = root.querySelector("#gl-strategy").value;
      const nBars = Number(root.querySelector("#gl-bars").value) || 24;
      runStatus.textContent = "simulando…";
      resultEl.innerHTML = "";
      QLApi.labBacktest({ strategy_id: strategy, n_bars: nBars })
        .then(function (data) {
          runStatus.textContent = data.ok ? "simulación ok (paper)" : "falló";
          runStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          resultEl.innerHTML =
            "<dt>venue</dt><dd class=\"mono\">" +
            esc(root.querySelector("#gl-venue").value) +
            "</dd>" +
            "<dt>strategy</dt><dd class=\"mono\">" +
            esc(data.strategy_id) +
            "</dd>" +
            "<dt>final_equity</dt><dd class=\"mono num\">" +
            esc(data.final_equity) +
            "</dd>" +
            "<dt>fills</dt><dd class=\"mono num\">" +
            esc(data.n_fills) +
            "</dd>" +
            "<dt>live_blocked</dt><dd class=\"mono\">" +
            esc(data.live_blocked) +
            "</dd>" +
            "<dt>live_routing</dt><dd class=\"mono\">" +
            esc(data.live_routing) +
            "</dd>";
        })
        .catch(function (err) {
          runStatus.textContent = "error: " + err.message;
          runStatus.className = "mono status-bad";
        });
    });

    const demoStatus = root.querySelector("#gl-demo-status");
    const demoOut = root.querySelector("#gl-demo-out");
    root.querySelector("#gl-demo-submit").addEventListener("click", function () {
      demoStatus.textContent = "enviando demo…";
      QLApi.liveDemoSubmit({
        symbol: root.querySelector("#gl-demo-sym").value,
        side: root.querySelector("#gl-demo-side").value,
        quantity: root.querySelector("#gl-demo-qty").value,
      })
        .then(function (data) {
          demoStatus.textContent = data.ok ? "demo fill ok" : "falló";
          demoStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          demoOut.textContent =
            esc(data.order_id) +
            " " +
            esc(data.status) +
            " @ " +
            esc(data.message) +
            " [" +
            esc(data.transport) +
            "]";
        })
        .catch(function (err) {
          demoStatus.textContent = "error: " + err.message;
          demoStatus.className = "mono status-bad";
        });
    });

    root.refresh = function () {
      return refreshLive();
    };
    refreshLive();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createGuidedLabPane = createGuidedLabPane;
})(window);
