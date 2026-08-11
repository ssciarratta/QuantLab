/** Paneles Binance Spot Testnet + Futures Testnet (demo post-unlock). */
(function (global) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createTestnetPane(cfg) {
    var root = document.createElement("div");
    root.className = "pane-binance-testnet";
    root.innerHTML =
      "<h3>" +
      esc(cfg.title) +
      "</h3>" +
      '<p class="muted" style="margin-top:0">' +
      esc(cfg.blurb) +
      "</p>" +
      '<div class="pane-section">' +
      "<h3>Estado</h3>" +
      '<div class="mono" id="bn-status">Cargando…</div>' +
      '<button type="button" class="btn secondary" id="bn-refresh">Actualizar</button>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Unlock LIVE</h3>" +
      '<p class="muted" style="margin-top:0">Usuario/clave locales (QUANTLAB_LIVE_*). No son keys de Binance.</p>' +
      '<input type="text" id="bn-user" placeholder="usuario" autocomplete="username" style="width:8em">' +
      '<input type="password" id="bn-pass" placeholder="password" autocomplete="current-password" style="width:8em">' +
      '<button type="button" class="btn" id="bn-unlock">Unlock</button>' +
      '<button type="button" class="btn secondary" id="bn-lock">Lock</button>' +
      '<span class="mono muted" id="bn-unlock-st">—</span>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Balances testnet</h3>" +
      '<div class="mono" id="bn-balances">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Demo order (post-unlock)</h3>" +
      '<p class="muted" style="margin-top:0">Cantidad chica. Transport según .env (Spot XOR Futures).</p>' +
      '<input type="text" id="bn-sym" value="BTCUSDT" style="width:7em">' +
      '<select id="bn-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="bn-qty" value="0.001" style="width:5em">' +
      '<button type="button" class="btn" id="bn-submit">Enviar demo</button>' +
      '<div class="mono" id="bn-demo-out">—</div>' +
      "</div>";

    var statusEl = root.querySelector("#bn-status");
    var unlockSt = root.querySelector("#bn-unlock-st");
    var balEl = root.querySelector("#bn-balances");
    var demoOut = root.querySelector("#bn-demo-out");

    function setStatus(obj) {
      if (!statusEl) return;
      var lines = [];
      lines.push("Market: " + cfg.market);
      lines.push("LIVE_BLOCKED: " + (obj.live_blocked === true ? "True" : String(obj.live_blocked)));
      lines.push("Unlock: " + (obj.unlocked ? "YES" : "NO"));
      var demo = obj.demo || {};
      lines.push("Transport: " + (demo.transport || obj.transport || "—"));
      lines.push("Remote market: " + (demo.remote_market || "—"));
      if (obj.conflict || (demo && demo.conflict)) {
        lines.push("CONFLICTO: Spot y Futures flags activos a la vez");
      }
      var tn = (demo && (cfg.market === "futures" ? demo.futures_testnet : demo.testnet)) ||
        obj[cfg.market === "futures" ? "futures" : "spot"] ||
        {};
      lines.push("Keys: " + (tn.keys_configured ? "sí" : "no"));
      lines.push("Flag remoto: " + (tn.remote_enabled ? "ON" : "OFF"));
      lines.push("Base: " + (tn.base_url || cfg.baseUrl));
      if (demo.error) lines.push("Error: " + demo.error);
      statusEl.textContent = lines.join("\n");
      if (unlockSt) unlockSt.textContent = obj.unlocked ? "unlocked" : "locked";
    }

    function refresh() {
      return Promise.all([
        QLApi.liveStatus(),
        QLApi.testnetStatus ? QLApi.testnetStatus() : Promise.resolve(null),
      ])
        .then(function (pair) {
          var live = pair[0] || {};
          var tn = pair[1] || {};
          setStatus(Object.assign({}, tn, live));
          return QLApi.testnetBalances
            ? QLApi.testnetBalances(cfg.market)
            : Promise.resolve(null);
        })
        .then(function (bals) {
          if (!balEl) return;
          if (!bals || !bals.ok) {
            balEl.textContent =
              (bals && bals.error) ||
              "Sin balances (keys o red). Revisá .env.";
            return;
          }
          var rows = (bals.balances || []).slice(0, 20).map(function (r) {
            if (cfg.market === "futures") {
              return (
                r.asset +
                " avail=" +
                r.available +
                " wallet=" +
                r.wallet
              );
            }
            return r.asset + " free=" + r.free + " total=" + r.total;
          });
          balEl.textContent = rows.length ? rows.join("\n") : "(sin no-cero)";
        })
        .catch(function (err) {
          if (statusEl) statusEl.textContent = "Error: " + (err.message || err);
        });
    }

    root.querySelector("#bn-refresh").addEventListener("click", refresh);
    root.querySelector("#bn-unlock").addEventListener("click", function () {
      var u = root.querySelector("#bn-user").value;
      var p = root.querySelector("#bn-pass").value;
      QLApi.liveUnlock(u, p)
        .then(function () {
          if (window.QLToasts) QLToasts.show("Unlock OK", "ok");
          return refresh();
        })
        .catch(function (err) {
          if (window.QLToasts) QLToasts.show(String(err.message || err), "error");
        });
    });
    root.querySelector("#bn-lock").addEventListener("click", function () {
      QLApi.liveLock()
        .then(function () {
          return refresh();
        })
        .catch(function () {});
    });
    root.querySelector("#bn-submit").addEventListener("click", function () {
      var payload = {
        symbol: root.querySelector("#bn-sym").value,
        side: root.querySelector("#bn-side").value,
        quantity: root.querySelector("#bn-qty").value,
      };
      QLApi.liveDemoSubmit(payload)
        .then(function (out) {
          demoOut.textContent = JSON.stringify(out, null, 2);
          if (window.QLToasts) {
            QLToasts.show(
              "Demo " + (out.transport || "") + " · " + (out.order_id || ""),
              "ok"
            );
          }
        })
        .catch(function (err) {
          demoOut.textContent = String(err.message || err);
        });
    });

    root.refresh = refresh;
    refresh();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBinanceSpotPane = function () {
    return createTestnetPane({
      market: "spot",
      title: "Binance Spot Testnet",
      baseUrl: "https://testnet.binance.vision",
      blurb:
        "Órdenes demo a Spot Testnet. Keys: BINANCE_DEMO_* + QUANTLAB_DEMO_USE_TESTNET=1. " +
        "No uses a la vez el flag Futures.",
    });
  };
  global.QLPanes.createBinanceFuturesPane = function () {
    return createTestnetPane({
      market: "futures",
      title: "Binance Futures Testnet",
      baseUrl: "https://testnet.binancefuture.com",
      blurb:
        "Órdenes demo a Futures USD-M Testnet. Keys: BINANCE_FUTURES_DEMO_* + " +
        "QUANTLAB_DEMO_USE_FUTURES_TESTNET=1. Producción bloqueada.",
    });
  };
})(window);
