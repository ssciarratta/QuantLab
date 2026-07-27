/** Guided Lab — wizard venue→scan→estrategia→simular + LIVE unlock (F99/F100/F109). */
(function (global) {
  "use strict";

  function t(key, fallback) {
    if (global.QLi18n && typeof global.QLi18n.t === "function") {
      return global.QLi18n.t(key, fallback);
    }
    return fallback != null ? fallback : key;
  }

  function createGuidedLabPane() {
    const root = document.createElement("div");
    root.className = "pane-guided-lab";

    root.innerHTML =
      '<div class="pane-section">' +
      '<h3 data-i18n="pane.guided_lab">Guided Lab</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.intro">' +
      "Flujo: venue → scan → estrategia → simular. " +
      "LIVE solo tras usuario/contraseña (corte humano). Sin unlock = bloqueado.</p>" +
      '<div class="mono" id="gl-live">LIVE_BLOCKED = True</div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.unlock.title">0. Unlock LIVE (opcional)</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.unlock.hint">' +
      "Definí QUANTLAB_LIVE_USER / QUANTLAB_LIVE_PASSWORD en tu PC. " +
      "Nunca se guardan en git ni en disco de sesión.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-user" placeholder="usuario" autocomplete="username">' +
      '<input type="password" id="gl-pass" placeholder="contraseña" autocomplete="current-password">' +
      '<button type="button" class="btn secondary" id="gl-unlock" data-i18n="guided_lab.unlock.btn">Unlock</button>' +
      '<button type="button" class="btn secondary" id="gl-lock" data-i18n="guided_lab.lock.btn">Lock</button>' +
      "</div>" +
      '<span class="mono muted" id="gl-unlock-status">—</span>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.venue">1. Venue</h3>' +
      '<select id="gl-venue">' +
      '<option value="binance" data-i18n="guided_lab.venue.binance">binance (MD público / demo)</option>' +
      '<option value="paper" data-i18n="guided_lab.venue.paper">paper (simulado)</option>' +
      '<option value="a3" data-i18n="guided_lab.venue.a3">a3 (MD fake|env / paper)</option>' +
      "</select>" +
      '<div id="gl-section-a3" style="display:none">' +
      '<div class="pane-row" style="margin-top:0.5em">' +
      '<label class="muted"><span data-i18n="guided_lab.a3.md_source">A3 md_source</span> ' +
      '<select id="gl-a3-md">' +
      '<option value="fake" data-i18n="guided_lab.a3.md_fake">fake (CI)</option>' +
      '<option value="env" data-i18n="guided_lab.a3.md_env">env (read-only)</option>' +
      "</select></label>" +
      '<button type="button" class="btn secondary" id="gl-a3-status-btn" data-i18n="guided_lab.a3.status_btn">Estado MD A3</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-connect" data-i18n="guided_lab.a3.connect">Conectar paper A3</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-instr" data-i18n="guided_lab.a3.instruments">Listar instrumentos</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-snap" data-i18n="guided_lab.a3.snapshot">Snapshot</button>' +
      '<input type="text" id="gl-a3-sym" placeholder="símbolo" style="width:7em">' +
      '<span class="mono muted" id="gl-a3-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-a3-out">—</div>' +
      '<div class="pane-row" style="margin-top:0.5em">' +
      '<select id="gl-a3-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="gl-a3-qty" value="1" style="width:5em" placeholder="qty">' +
      '<button type="button" class="btn" id="gl-a3-paper" data-i18n="guided_lab.a3.paper_submit">Enviar paper (A3)</button>' +
      '<span class="mono muted" id="gl-a3-paper-status">—</span>' +
      "</div>" +
      '<p class="muted" data-i18n="guided_lab.a3.footer">A3 = PaperBroker (sin routing venue). MD env: QUANTLAB_A3_MD_READONLY=1 + creds.</p>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.scan">2. Escanear</h3>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="gl-scan" data-i18n="guided_lab.scan.lab">Scan lab sintético</button>' +
      '<button type="button" class="btn secondary" id="gl-scan-bn" data-i18n="guided_lab.scan.binance" style="display:none">Scan Binance USDT</button>' +
      '<span class="mono muted" id="gl-scan-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-scan-out">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.strategy">3. Estrategia</h3>' +
      '<select id="gl-strategy">' +
      '<option value="momentum">momentum</option>' +
      '<option value="buy_once">buy_once</option>' +
      "</select>" +
      '<label class="muted"> n_bars <input type="number" id="gl-bars" value="24" min="4" max="120" style="width:4em"></label>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.simulate">4. Simular (paper)</h3>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="gl-run" data-i18n="guided_lab.simulate.run">Simular backtest</button>' +
      '<span class="mono muted" id="gl-run-status">—</span>' +
      "</div>" +
      '<dl class="kv" id="gl-result"></dl>' +
      "</div>" +
      '<div class="pane-section" id="gl-section-demo" style="display:none">' +
      '<h3 data-i18n="guided_lab.section.demo">5. Demo order (post-unlock)</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.demo.hint">' +
      "Fill demo Binance. Requiere unlock. " +
      "Default: sim local. Testnet remoto solo con QUANTLAB_DEMO_USE_TESTNET=1 + keys.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-demo-sym" value="BTCUSDT" style="width:7em">' +
      '<select id="gl-demo-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="gl-demo-qty" value="0.001" style="width:5em">' +
      '<input type="text" id="gl-demo-price" placeholder="price (LIMIT)" style="width:7em">' +
      '<label class="muted" style="display:flex;align-items:center;gap:0.35rem">' +
      '<input type="checkbox" id="gl-demo-mirror">' +
      '<span data-i18n="guided_lab.demo.mirror">Mirror a paper journal</span></label>' +
      '<button type="button" class="btn" id="gl-demo-submit" data-i18n="guided_lab.demo.submit">Enviar demo</button>' +
      '<span class="mono muted" id="gl-demo-status">—</span>' +
      "</div>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-demo-cancel-id" placeholder="order_id" style="width:8em">' +
      '<button type="button" class="btn secondary" id="gl-demo-cancel" data-i18n="guided_lab.demo.cancel">Cancelar orden</button>' +
      '<button type="button" class="btn secondary" id="gl-demo-open" data-i18n="guided_lab.demo.open_orders">Ver abiertas</button>' +
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

    function statusErr(el, err) {
      el.textContent = t("guided_lab.status.error", "error") + ": " + err.message;
      el.className = "mono status-bad";
    }

    function applyVenueUi() {
      const venue = root.querySelector("#gl-venue").value;
      const a3Section = root.querySelector("#gl-section-a3");
      const demoSection = root.querySelector("#gl-section-demo");
      const scanBn = root.querySelector("#gl-scan-bn");
      if (a3Section) {
        a3Section.style.display = venue === "a3" ? "" : "none";
      }
      if (demoSection) {
        demoSection.style.display = venue === "binance" ? "" : "none";
      }
      if (scanBn) {
        scanBn.style.display = venue === "binance" ? "" : "none";
      }
    }

    function refreshLive() {
      return QLApi.liveStatus()
        .then(function (data) {
          const unlocked = data.unlocked === true;
          const demo = data.demo || {};
          const transport = demo.transport || (unlocked ? "—" : "blocked");
          liveEl.textContent =
            "LIVE_BLOCKED=" +
            data.live_blocked +
            " · unlocked=" +
            unlocked +
            " · configured=" +
            data.credentials_configured +
            " · transport=" +
            transport +
            (demo.n_fills != null ? " · fills=" + demo.n_fills : "");
          liveEl.className = unlocked ? "mono status-ok" : "mono status-bad";
          unlockStatus.textContent = unlocked
            ? t("guided_lab.status.unlock_active", "unlock activo") +
                " (" +
                esc(data.venue_scope) +
                ")"
            : data.credentials_configured
              ? t("guided_lab.status.blocked_creds", "bloqueado — ingresá user/pass")
              : t(
                  "guided_lab.status.blocked_env",
                  "bloqueado — configurá env QUANTLAB_LIVE_USER/PASSWORD"
                );
        })
        .catch(function (err) {
          liveEl.textContent =
            t("guided_lab.status.error", "error") + ": " + err.message;
        });
    }

    root.querySelector("#gl-unlock").addEventListener("click", function () {
      const user = root.querySelector("#gl-user").value;
      const pass = root.querySelector("#gl-pass").value;
      unlockStatus.textContent = t("guided_lab.status.validating", "validando…");
      QLApi.liveUnlock(user, pass, "binance_demo")
        .then(function () {
          root.querySelector("#gl-pass").value = "";
          return refreshLive();
        })
        .catch(function (err) {
          statusErr(unlockStatus, err);
        });
    });

    root.querySelector("#gl-lock").addEventListener("click", function () {
      QLApi.liveLock()
        .then(function () {
          return refreshLive();
        })
        .catch(function (err) {
          statusErr(unlockStatus, err);
        });
    });

    root.querySelector("#gl-venue").addEventListener("change", applyVenueUi);

    const a3Status = root.querySelector("#gl-a3-status");
    const a3Out = root.querySelector("#gl-a3-out");
    function a3MdSource() {
      return root.querySelector("#gl-a3-md").value || "fake";
    }
    root.querySelector("#gl-a3-status-btn").addEventListener("click", function () {
      a3Status.textContent = t("guided_lab.status.querying", "consultando…");
      QLApi.a3MdStatus()
        .then(function (data) {
          a3Status.textContent = data.env_ready
            ? t("guided_lab.status.env_ready", "env listo")
            : t("guided_lab.status.env_not_ready", "env no listo") +
                " (" +
                esc(data.reason) +
                ")";
          a3Status.className = data.env_ready ? "mono status-ok" : "mono muted";
          a3Out.textContent =
            "flag=" +
            data.md_readonly_flag +
            " creds=" +
            data.credentials_configured +
            " env=" +
            esc(data.environment) +
            " · " +
            esc(data.note);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-connect").addEventListener("click", function () {
      const md = a3MdSource();
      a3Status.textContent =
        t("guided_lab.status.a3_connecting", "conectando A3 paper…") + " md=" + md;
      root.querySelector("#gl-venue").value = "a3";
      applyVenueUi();
      QLApi.connect("a3", "paper", { md_source: md })
        .then(function (data) {
          a3Status.textContent = data.ok
            ? t("guided_lab.status.a3_connected", "A3 paper conectado") + " (" + md + ")"
            : t("guided_lab.status.failed", "falló");
          a3Status.className = data.ok ? "mono status-ok" : "mono status-bad";
          a3Out.textContent = esc(JSON.stringify(data.health || data, null, 0)).slice(0, 280);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-instr").addEventListener("click", function () {
      a3Status.textContent = t("guided_lab.status.listing", "listando…");
      QLApi.instruments()
        .then(function (data) {
          const items = data.instruments || data.items || [];
          a3Status.textContent = "ok (" + items.length + ")";
          a3Status.className = "mono status-ok";
          if (items.length && !root.querySelector("#gl-a3-sym").value) {
            root.querySelector("#gl-a3-sym").value = items[0].symbol || "";
          }
          a3Out.innerHTML = items
            .slice(0, 12)
            .map(function (it) {
              return esc(it.symbol || it.instrument_id || JSON.stringify(it));
            })
            .join("<br>") || "—";
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-snap").addEventListener("click", function () {
      const sym = root.querySelector("#gl-a3-sym").value.trim();
      if (!sym) {
        a3Status.textContent = t(
          "guided_lab.status.symbol_required",
          "ingresá símbolo o listá instrumentos"
        );
        a3Status.className = "mono status-bad";
        return;
      }
      a3Status.textContent = t("guided_lab.status.snapshot", "snapshot…");
      QLApi.snapshot(sym)
        .then(function (data) {
          a3Status.textContent = t("guided_lab.status.snapshot_ok", "snapshot ok");
          a3Status.className = "mono status-ok";
          const s = data.snapshot || data;
          a3Out.textContent =
            esc(s.symbol || sym) +
            " bid=" +
            esc(s.bid) +
            " ask=" +
            esc(s.ask) +
            " last=" +
            esc(s.last);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-paper").addEventListener("click", function () {
      const sym = root.querySelector("#gl-a3-sym").value.trim();
      const side = root.querySelector("#gl-a3-side").value;
      const qty = root.querySelector("#gl-a3-qty").value.trim();
      const paperStatus = root.querySelector("#gl-a3-paper-status");
      if (!sym || !qty) {
        paperStatus.textContent = t(
          "guided_lab.status.symbol_qty_required",
          "símbolo y qty requeridos"
        );
        paperStatus.className = "mono status-bad";
        return;
      }
      paperStatus.textContent = t("guided_lab.status.sending_paper", "enviando paper…");
      QLApi.paperSubmit({
        intent_type: "place_order",
        instrument_id: sym,
        side: side,
        quantity: qty,
        order_type: "market",
      })
        .then(function (res) {
          const ack = res.ack || {};
          paperStatus.textContent =
            (ack.status || "?") + " · " + (ack.order_id || "") + " · " + (ack.message || "");
          paperStatus.className = "mono status-ok";
          const acct = res.account || {};
          a3Out.textContent =
            t("guided_lab.status.paper_ok", "paper ok") +
            " · cash=" +
            esc(acct.cash) +
            " · equity=" +
            esc(acct.equity);
        })
        .catch(function (err) {
          statusErr(paperStatus, err);
        });
    });

    root.querySelector("#gl-scan").addEventListener("click", function () {
      scanStatus.textContent = t("guided_lab.status.scanning_lab", "escaneando lab…");
      QLApi.labScanner({ top_n: 3 })
        .then(function (data) {
          scanStatus.textContent = t("guided_lab.status.scan_lab_ok", "ok (lab)");
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
          statusErr(scanStatus, err);
        });
    });

    root.querySelector("#gl-scan-bn").addEventListener("click", function () {
      scanStatus.textContent = t("guided_lab.status.scanning_binance", "escaneando Binance…");
      QLApi.binanceScan(20)
        .then(function (data) {
          scanStatus.textContent = t("guided_lab.status.scan_binance_ok", "ok (binance MD)");
          scanStatus.className = "mono status-ok";
          const symbols = data.symbols || [];
          const tickers = data.tickers || [];
          scanOut.innerHTML =
            "símbolos=" +
            esc(data.n_symbols) +
            "<br>" +
            tickers
              .map(function (tk) {
                return esc(tk.symbol) + " bid=" + esc(tk.bid) + " ask=" + esc(tk.ask);
              })
              .join("<br>") +
            (symbols.length
              ? "<br><span class=\"muted\">…" + esc(symbols.slice(0, 5).join(", ")) + "</span>"
              : "");
        })
        .catch(function (err) {
          statusErr(scanStatus, err);
        });
    });

    root.querySelector("#gl-run").addEventListener("click", function () {
      const strategy = root.querySelector("#gl-strategy").value;
      const nBars = Number(root.querySelector("#gl-bars").value) || 24;
      runStatus.textContent = t("guided_lab.status.simulating", "simulando…");
      resultEl.innerHTML = "";
      QLApi.labBacktest({ strategy_id: strategy, n_bars: nBars })
        .then(function (data) {
          runStatus.textContent = data.ok
            ? t("guided_lab.status.simulation_ok", "simulación ok (paper)")
            : t("guided_lab.status.failed", "falló");
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
          statusErr(runStatus, err);
        });
    });

    const demoStatus = root.querySelector("#gl-demo-status");
    const demoOut = root.querySelector("#gl-demo-out");
    root.querySelector("#gl-demo-submit").addEventListener("click", function () {
      demoStatus.textContent = t("guided_lab.status.sending_demo", "enviando demo…");
      const payload = {
        symbol: root.querySelector("#gl-demo-sym").value,
        side: root.querySelector("#gl-demo-side").value,
        quantity: root.querySelector("#gl-demo-qty").value,
      };
      const priceVal = root.querySelector("#gl-demo-price").value.trim();
      if (priceVal) {
        payload.price = priceVal;
      }
      if (root.querySelector("#gl-demo-mirror").checked) {
        payload.mirror_to_paper = true;
      }
      QLApi.liveDemoSubmit(payload)
        .then(function (data) {
          demoStatus.textContent = data.ok
            ? t("guided_lab.status.demo_ok", "demo ok")
            : t("guided_lab.status.failed", "falló");
          demoStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          demoOut.textContent =
            esc(data.order_id) +
            " " +
            esc(data.status) +
            " @ " +
            esc(data.message) +
            " [" +
            esc(data.transport) +
            "]" +
            (data.mirrored_to_paper ? " · mirrored" : "");
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    root.querySelector("#gl-demo-cancel").addEventListener("click", function () {
      const orderId = root.querySelector("#gl-demo-cancel-id").value.trim();
      if (!orderId) {
        demoStatus.textContent =
          t("guided_lab.status.error", "error") + ": order_id requerido";
        demoStatus.className = "mono status-bad";
        return;
      }
      demoStatus.textContent = t("guided_lab.status.cancelling", "cancelando…");
      QLApi.liveDemoCancel(orderId)
        .then(function (data) {
          demoStatus.textContent = data.ok
            ? t("guided_lab.status.cancel_ok", "cancel ok")
            : t("guided_lab.status.failed", "falló");
          demoStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          demoOut.textContent =
            esc(data.order_id) +
            " " +
            esc(data.status) +
            " @ " +
            esc(data.message);
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    root.querySelector("#gl-demo-open").addEventListener("click", function () {
      demoStatus.textContent = t("guided_lab.status.querying", "consultando…");
      QLApi.liveDemoOpenOrders()
        .then(function (data) {
          const orders = data.orders || [];
          demoStatus.textContent = "ok (" + orders.length + ")";
          demoStatus.className = "mono status-ok";
          if (!orders.length) {
            demoOut.textContent = "—";
            return;
          }
          demoOut.innerHTML = orders
            .map(function (ord) {
              return (
                esc(ord.order_id || ord.client_order_id || "?") +
                " " +
                esc(ord.symbol || ord.instrument_id || "") +
                " " +
                esc(ord.side || "") +
                " qty=" +
                esc(ord.quantity || ord.orig_qty) +
                (ord.price != null ? " @ " + esc(ord.price) : "") +
                " [" +
                esc(ord.status || "") +
                "]"
              );
            })
            .join("<br>");
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    root.refresh = function () {
      return refreshLive();
    };

    applyVenueUi();
    refreshLive();
    QLi18n.applyDom(root);
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createGuidedLabPane = createGuidedLabPane;
})(window);
