/** Corrida en vivo — ventana unificada (handoffs Scanner/Sim/MC, estrategias por familia). */
(function (global) {
  "use strict";

  var PARAM_LABELS = {
    quantity: "Monto / cantidad por orden",
    price: "Precio límite",
    qty: "Cantidad",
    order_size: "Tamaño de orden (USD)",
    fast: "Ventana rápida (barras)",
    slow: "Ventana lenta (barras)",
    lookback: "Lookback (barras)",
    period: "Período (barras)",
    window: "Ventana (barras)",
    threshold: "Umbral señal",
    spread_bps: "Spread (bps)",
    levels: "Niveles en book",
    n_levels: "Cantidad de niveles",
    inventory_target: "Inventario objetivo",
    gamma: "Aversión inventario (γ)",
    kappa: "Intensidad de fills (κ)",
    sigma: "Volatilidad estimada (σ)",
    skew: "Sesgo inventario",
    min_spread: "Spread mínimo",
    max_spread: "Spread máximo",
    refresh_ms: "Refresh cotización (ms)",
    tick_size: "Tick size",
    lot_size: "Lote mínimo",
    stop_loss: "Stop loss (%)",
    take_profit: "Take profit (%)",
    leverage: "Apalancamiento",
    capital: "Capital",
  };

  var FAMILY_ORDER = [
    "demo",
    "trend",
    "momentum",
    "mean_reversion",
    "market_making",
    "stats",
    "ml",
    "multi_asset",
    "microstructure",
    "arbitrage",
    "options",
  ];

  var FIELD_TIPS = {
    strategy:
      "Estrategia del catálogo · ★ = corre en paper (39 del catálogo) · [solo catálogo] = stub research (11) — no corre",
    symbol:
      "Par del exchange (ej. UNIUSDT) · Se infiere del Sim/Scanner · No opera LIVE real",
    dest:
      "PAPER = motor local, MD real, fills simulados (39 estrategias ★) · Spot Testnet = órdenes reales en testnet Binance spot (solo buy_once hoy) · Futures Testnet = pendiente (0 estrategias conectadas)",
    steps:
      "Ticks del motor paper · Cada step lee mercado y puede simular fills · No es duración en minutos",
    market:
      "Spot o Futures · Debe coincidir con el handoff · Afecta reglas y resolución del símbolo",
    interval:
      "Timeframe de contexto (1h, 4h…) · Viene del Sim/Scanner · No cambia la cadencia de steps",
    venue:
      "Exchange fuente de MD (binance, hl…) · Solo lectura de mercado en paper",
    period:
      "Días de historial de referencia · Metadata del experimento · No limita la corrida en vivo",
    capital:
      "Capital simulado paper · No mueve dinero real · Base para sizing y PnL",
    leverage:
      "Apalancamiento simulado · Solo futures · No aplica en spot",
    per_trade:
      "Tamaño nominal por operación en USD · Paper · No es orden real en exchange",
    interval_ms:
      "Milisegundos entre steps del motor · Más bajo = más ticks · Default 800 ms",
    start:
      "Promueve la estrategia y arranca corrida paper automática · Requiere estrategia ★ runnable",
    stop: "Detiene la corrida paper activa · No cierra posiciones reales (no hay LIVE)",
  };

  var PARAM_TIPS = {
    quantity: "Cantidad base por orden simulada · Paper · No envía orden real",
    half_spread: "Mitad del spread entre bid y ask · Market making simulado",
    level_step: "Separación entre niveles del book simulado",
    levels: "Cuántos niveles bid/ask mantiene la estrategia",
    n_levels: "Cantidad de niveles en el book simulado",
    max_pos: "Posición máxima permitida · Límite de riesgo paper",
    order_size: "Notional por orden en USD · Paper simulado",
  };

  function tipAttr(text) {
    if (!text) return "";
    return ' data-tip="' + esc(text) + '"';
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fmtDt(iso) {
    if (global.QLFmt && global.QLFmt.fmtDateTime) return global.QLFmt.fmtDateTime(iso);
    return iso == null || iso === "" ? "—" : String(iso);
  }

  function fmtNum(v) {
    if (v == null || v === "") return "—";
    var n = Number(v);
    return isFinite(n) ? n.toLocaleString("es-AR", { maximumFractionDigits: 6 }) : String(v);
  }

  function createStrategyLiveTestPane() {
    var root = document.createElement("div");
    root.className = "pane-strategy-live-test slt-v2";
    root.innerHTML =
      '<div class="slt-head">' +
      "<h3>Corrida en vivo</h3>" +
      '<p class="slt-lead muted"' +
      tipAttr(
        "Prueba una estrategia ★ con MD real y fills paper · No opera dinero real · LIVE siempre bloqueado"
      ) +
      ">MD reales · motor paper + espejo testnet · producción bloqueada</p>" +
      '<p id="slt-catalog-line" class="slt-catalog-line muted">Catálogo: cargando…</p>' +
      '<div class="slt-dest-guide muted"' +
      tipAttr(
        "PAPER o Testnet: mismo motor para las 39 ★. Testnet espeja órdenes al exchange de prueba si hay unlock + keys."
      ) +
      "><b>Destinos:</b> <b>PAPER</b> = simulación local · " +
      "<b>Spot Testnet</b> = motor + órdenes reales testnet spot (39 ★) · " +
      "<b>Futures Testnet</b> = motor + órdenes reales testnet futures (39 ★)</div>" +
      "</div>" +
      '<div id="slt-source-ctx" class="slt-source-ctx" hidden></div>' +
      '<div class="pane-row slt-action-row">' +
      '<button type="button" class="btn slt-btn-start slt-btn-hero" id="slt-start"' +
      tipAttr(FIELD_TIPS.start) +
      ">▶ INICIAR CORRIDA</button>" +
      '<button type="button" class="btn danger" id="slt-stop" disabled' +
      tipAttr(FIELD_TIPS.stop) +
      ">■ DETENER</button>" +
      "</div>" +
      '<div class="pane-section slt-config">' +
      '<div class="slt-form-grid slt-config-grid">' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.strategy) +
      '><span>Estrategia</span><select id="slt-strategy"></select></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.symbol) +
      '><span>Símbolo</span><input id="slt-symbol" value="BTCUSDT"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.dest) +
      '><span>Destino</span><select id="slt-dest">' +
      '<option value="PAPER" selected>PAPER</option>' +
      '<option value="BINANCE_SPOT_TESTNET">Spot Testnet</option>' +
      '<option value="BINANCE_FUTURES_TESTNET">Futures Testnet</option>' +
      "</select></label>" +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.steps) +
      '><span>Steps</span><input id="slt-steps" type="number" value="25" min="1" max="500"></label>' +
      "</div>" +
      '<div id="slt-strat-hint" class="muted slt-hint">—</div>' +
      "</div>" +
      '<div class="pane-section slt-operational">' +
      "<h4>Mercado, periodicidad y capital</h4>" +
      '<div class="slt-form-grid slt-op-grid">' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.market) +
      '><span>Mercado</span><select id="slt-market"><option value="spot">Spot</option><option value="futures">Futures</option></select></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.interval) +
      '><span>Timeframe</span><input id="slt-interval" placeholder="1h, 4h, 1d" value="1h"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.venue) +
      '><span>Venue</span><input id="slt-venue" placeholder="binance, hl, …"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.period) +
      '><span>Histórico (días)</span><input id="slt-period" type="number" min="1" placeholder="90"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.capital) +
      '><span>Capital inicial</span><input id="slt-capital" type="text" placeholder="10000"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.leverage) +
      '><span>Apalancamiento</span><input id="slt-leverage" type="text" placeholder="1"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.per_trade) +
      '><span>USD / trade</span><input id="slt-per-trade" type="text" placeholder="—"></label>' +
      '<label class="slt-field"' +
      tipAttr(FIELD_TIPS.interval_ms) +
      '><span>Cadencia (ms)</span><input id="slt-interval-ms" type="number" min="100" value="800"></label>' +
      "</div>" +
      "<h4>Cómo opera la estrategia</h4>" +
      '<p id="slt-strat-desc" class="slt-strat-desc muted">—</p>' +
      '<div id="slt-strat-params" class="slt-form-grid slt-params-grid"></div>' +
      "</div>" +
      '<div class="pane-section slt-live" id="slt-live-box">' +
      '<div class="slt-phase" id="slt-phase">● Listo</div>' +
      '<div class="slt-err-detail muted" id="slt-err-detail" hidden></div>' +
      '<div class="slt-metrics" id="slt-metrics">Sin corrida activa — elegí estrategia ★ y pulsá INICIAR</div>' +
      '<div class="slt-progress-wrap"><div class="slt-progress-bar" id="slt-progress"></div></div>' +
      '<div class="slt-last-action mono" id="slt-last-action">—</div>' +
      "</div>" +
      '<div class="pane-section slt-closure" id="slt-closure-box" hidden>' +
      '<h4 id="slt-closure-head">Resumen final</h4>' +
      '<div class="slt-closure-cols">' +
      '<div class="slt-closure-col slt-closure-done-col">' +
      "<h5>✓ Qué se hizo</h5>" +
      '<ul id="slt-closure-done"></ul></div>' +
      '<div class="slt-closure-col slt-closure-not-col">' +
      "<h5>✗ Qué no se hizo / pendiente</h5>" +
      '<ul id="slt-closure-not"></ul></div></div>' +
      '<div class="slt-closure-metrics mono" id="slt-closure-metrics"></div>' +
      "</div>" +
      '<div class="pane-section slt-tabs-wrap">' +
      '<div class="slt-tab-bar">' +
      '<button type="button" class="slt-tab active" data-tab="resumen"' +
      tipAttr("Estado general · sesión · PnL · pasos") +
      ">Resumen</button>" +
      '<button type="button" class="slt-tab" data-tab="ordenes"' +
      tipAttr("Fills simulados paper · no exchange real") +
      ">Órdenes / Fills</button>" +
      '<button type="button" class="slt-tab" data-tab="posiciones"' +
      tipAttr("Posiciones y caja paper simuladas") +
      ">Posiciones / Caja</button>" +
      '<button type="button" class="slt-tab" data-tab="mercado"' +
      tipAttr("Snapshot MD read-only del par") +
      ">Mercado</button>" +
      '<button type="button" class="slt-tab" data-tab="eventos"' +
      tipAttr("Log de eventos de esta ventana") +
      ">Eventos</button>" +
      '<button type="button" class="slt-tab" data-tab="tecnico"' +
      tipAttr("JSON crudo · debug · no operar desde acá") +
      ">Técnico</button>" +
      "</div>" +
      '<div class="slt-tab-panel active" data-panel="resumen" id="slt-panel-resumen"></div>' +
      '<div class="slt-tab-panel" data-panel="ordenes" id="slt-panel-ordenes"></div>' +
      '<div class="slt-tab-panel" data-panel="posiciones" id="slt-panel-posiciones"></div>' +
      '<div class="slt-tab-panel" data-panel="mercado" id="slt-panel-mercado"></div>' +
      '<div class="slt-tab-panel" data-panel="eventos" id="slt-panel-eventos"></div>' +
      '<div class="slt-tab-panel" data-panel="tecnico" id="slt-panel-tecnico"></div>' +
      "</div>" +
      '<div class="pane-section slt-hist">' +
      "<h4 style=\"margin:0 0 0.35rem\">Historial reciente</h4>" +
      '<div id="slt-hist-list" class="mono slt-hist-list">—</div>' +
      "</div>";

    var strategies = [];
    var familyLabels = {};
    var familyOrder = FAMILY_ORDER.slice();
    var sessionId = null;
    var pollTimer = null;
    var lastLive = null;
    var eventLog = [];
    var pendingPrefill = null;
    var sourcePrefill = null;
    var runStartedAt = null;
    var lastPaperRunning = false;
    var lastRunStages = [];
    var lastPaperStarted = false;
    var closureShown = false;

    var stratSel = root.querySelector("#slt-strategy");
    var symIn = root.querySelector("#slt-symbol");
    var destSel = root.querySelector("#slt-dest");
    var stepsIn = root.querySelector("#slt-steps");
    var hintEl = root.querySelector("#slt-strat-hint");
    var sourceCtxEl = root.querySelector("#slt-source-ctx");
    var phaseEl = root.querySelector("#slt-phase");
    var errDetailEl = root.querySelector("#slt-err-detail");
    var metricsEl = root.querySelector("#slt-metrics");
    var progressEl = root.querySelector("#slt-progress");
    var lastActEl = root.querySelector("#slt-last-action");
    var startBtn = root.querySelector("#slt-start");
    var stopBtn = root.querySelector("#slt-stop");

    function logEvent(msg) {
      var ts =
        global.QLFmt && global.QLFmt.fmtDateTime
          ? global.QLFmt.fmtDateTime(new Date())
          : new Date().toLocaleTimeString("es-AR");
      eventLog.unshift("[" + ts + "] " + msg);
      if (eventLog.length > 120) eventLog.pop();
      renderEvents();
    }

    function currentCaps() {
      var sid = stratSel && stratSel.value;
      for (var i = 0; i < strategies.length; i++) {
        if (strategies[i].strategy_id === sid) return strategies[i];
      }
      return null;
    }

    function paramLabel(key) {
      return PARAM_LABELS[key] || String(key).replace(/_/g, " ");
    }

    function renderStrategyParams(override) {
      var el = root.querySelector("#slt-strat-params");
      var descEl = root.querySelector("#slt-strat-desc");
      if (!el) return;
      var caps = currentCaps();
      if (!caps) {
        el.innerHTML = '<p class="muted">—</p>';
        if (descEl) descEl.textContent = "—";
        return;
      }
      if (descEl) {
        descEl.textContent =
          caps.description ||
          "Parámetros editables de la estrategia seleccionada (se envían en la promoción).";
      }
      var defaults = Object.assign({}, caps.default_parameters || {});
      var schema =
        (caps.parameter_schema && caps.parameter_schema.properties) || {};
      var keys = Object.keys(defaults);
      if (!keys.length) keys = Object.keys(schema);
      if (!keys.length) {
        el.innerHTML =
          '<p class="muted">Sin parámetros declarados — la estrategia usa defaults internos.</p>';
        return;
      }
      var ov =
        override ||
        (pendingPrefill && pendingPrefill.strategy_parameters) ||
        {};
      el.innerHTML = keys
        .map(function (key) {
          var spec = schema[key] || {};
          var val = ov[key] != null ? ov[key] : defaults[key];
          var t = spec.type || typeof val;
          var id = "slt-param-" + key.replace(/[^a-zA-Z0-9_-]/g, "_");
          var pTip =
            PARAM_TIPS[key] ||
            (spec.description ? String(spec.description) : "") ||
            "Parámetro de la estrategia · se envía en la promoción paper";
          if (t === "boolean" || typeof val === "boolean") {
            return (
              '<label class="slt-field slt-field-check"' +
              tipAttr(pTip) +
              ">" +
              '<span>' +
              esc(paramLabel(key)) +
              "</span>" +
              '<input type="checkbox" id="' +
              id +
              '" data-param-key="' +
              esc(key) +
              '"' +
              (val ? " checked" : "") +
              "></label>"
            );
          }
          var inputType =
            t === "integer" || t === "number" || typeof val === "number"
              ? "number"
              : "text";
          var step = t === "integer" ? ' step="1"' : "";
          return (
            '<label class="slt-field"' +
            tipAttr(pTip) +
            ">" +
            "<span>" +
            esc(paramLabel(key)) +
            "</span>" +
            '<input type="' +
            inputType +
            '" id="' +
            id +
            '" data-param-key="' +
            esc(key) +
            '"' +
            step +
            ' value="' +
            esc(String(val != null ? val : "")) +
            '"></label>'
          );
        })
        .join("");
    }

    function collectStrategyParams() {
      var box = root.querySelector("#slt-strat-params");
      var params = {};
      if (!box) return params;
      box.querySelectorAll("[data-param-key]").forEach(function (input) {
        var key = input.getAttribute("data-param-key");
        if (!key) return;
        if (input.type === "checkbox") {
          params[key] = input.checked;
          return;
        }
        var raw = String(input.value || "").trim();
        if (!raw) return;
        if (input.type === "number") {
          var n = Number(raw);
          params[key] = Number.isFinite(n) ? n : raw;
        } else {
          params[key] = raw;
        }
      });
      return params;
    }

    function applyOperationalPrefill(prefill) {
      if (!prefill) return;
      var ctx = prefill.sim_context || {};
      function setVal(sel, v) {
        var el = root.querySelector(sel);
        if (el && v != null && v !== "") el.value = String(v);
      }
      setVal("#slt-market", prefill.market_type || ctx.market_type);
      setVal("#slt-interval", prefill.interval || ctx.interval);
      setVal("#slt-venue", prefill.venue || (ctx.venues && ctx.venues[0]));
      setVal("#slt-period", prefill.period_days || ctx.period_days);
      setVal(
        "#slt-capital",
        prefill.capital || ctx.initial_capital || ctx.capital
      );
      setVal("#slt-leverage", prefill.leverage || ctx.leverage);
      setVal("#slt-per-trade", prefill.per_trade_usd || ctx.per_trade_usd);
      if (prefill.interval_ms != null) setVal("#slt-interval-ms", prefill.interval_ms);
    }

    function collectOperationalConfig() {
      var marketEl = root.querySelector("#slt-market");
      var intervalEl = root.querySelector("#slt-interval");
      var venueEl = root.querySelector("#slt-venue");
      var periodEl = root.querySelector("#slt-period");
      var capEl = root.querySelector("#slt-capital");
      var levEl = root.querySelector("#slt-leverage");
      var ptEl = root.querySelector("#slt-per-trade");
      var msEl = root.querySelector("#slt-interval-ms");
      return {
        market_type: marketEl ? marketEl.value : "spot",
        interval: intervalEl ? intervalEl.value.trim() : "",
        venue: venueEl ? venueEl.value.trim() : "",
        period_days: periodEl ? periodEl.value.trim() : "",
        capital: capEl ? capEl.value.trim() : "",
        leverage: levEl ? levEl.value.trim() : "",
        per_trade_usd: ptEl ? ptEl.value.trim() : "",
        interval_ms: msEl ? parseInt(msEl.value, 10) || 800 : 800,
      };
    }

    function isPaperRunnable(caps) {
      if (!caps) return false;
      if (caps.paper_run_certified === true || caps.paper_run_certified === "true") {
        return true;
      }
      if (caps.runnable === true || caps.runnable === "true") {
        return caps.research_only !== true && caps.research_only !== "true";
      }
      return false;
    }

    function destRunStatus(caps) {
      if (!caps || !destSel) {
        return { canStart: false, kind: "unknown", message: "Sin estrategia cargada." };
      }
      if (!isPaperRunnable(caps)) {
        return {
          canStart: false,
          kind: "stub",
          message:
            "Esta estrategia es [solo catálogo] — stub research (1 de 11). No corre en ningún destino. Elegí otra con ★.",
        };
      }
      var dest = destSel.value;
      if (dest === "PAPER") {
        return {
          canStart: true,
          kind: "paper",
          message:
            "Listo: " +
            (caps.strategy_name || caps.strategy_id) +
            " ★ corre en PAPER (MD real + fills simulados). Pulsá INICIAR CORRIDA.",
        };
      }
      if (dest === "BINANCE_SPOT_TESTNET") {
        if (caps.spot_testnet_supported) {
          return {
            canStart: true,
            kind: "spot",
            message:
              (caps.strategy_name || caps.strategy_id) +
              " ★ — motor + espejo Spot Testnet. Seguimiento en vivo abajo. " +
              "Órdenes reales de prueba si unlock demo + QUANTLAB_DEMO_USE_TESTNET=1 + keys.",
          };
        }
      }
      if (dest === "BINANCE_FUTURES_TESTNET") {
        if (caps.futures_testnet_supported) {
          return {
            canStart: true,
            kind: "futures",
            message:
              (caps.strategy_name || caps.strategy_id) +
              " ★ — motor + espejo Futures Testnet. Seguimiento en vivo abajo. " +
              "Órdenes reales si unlock + QUANTLAB_DEMO_USE_FUTURES_TESTNET=1 + keys.",
          };
        }
      }
      return { canStart: false, kind: "unknown", message: "Destino desconocido." };
    }

    function strategyTag(s) {
      if (isPaperRunnable(s)) {
        return s.requires_adapter ? " ★·adapter" : " ★";
      }
      return " [solo catálogo]";
    }

    function canRunPaper() {
      var st = destRunStatus(currentCaps());
      return st.canStart && destSel && destSel.value === "PAPER";
    }

    function refreshHint() {
      var caps = currentCaps();
      if (!hintEl) return;
      if (!caps) {
        hintEl.textContent = "Cargando catálogo de estrategias…";
        hintEl.style.color = "";
        if (startBtn) startBtn.disabled = true;
        return;
      }
      var st = destRunStatus(caps);
      hintEl.textContent = st.message;
      if (st.kind === "stub") {
        hintEl.style.color = "var(--danger,#f66)";
      } else if (st.canStart) {
        hintEl.style.color = "var(--ok,#6f6)";
      } else if (st.kind === "spot_block" || st.kind === "futures_block") {
        hintEl.style.color = "var(--amber,#e8a838)";
      } else {
        hintEl.style.color = "";
      }
      if (startBtn) {
        startBtn.disabled = !st.canStart;
        startBtn.title = st.canStart
          ? "Arrancar corrida en " + (destSel ? destSel.value : "PAPER")
          : st.message;
      }
    }

    function updateCatalogLine() {
      var el = root.querySelector("#slt-catalog-line");
      if (!el) return;
      var nRun = 0;
      var nStub = 0;
      strategies.forEach(function (s) {
        if (isPaperRunnable(s)) nRun += 1;
        else nStub += 1;
      });
      if (!strategies.length) {
        el.textContent = "Catálogo: no cargó — reiniciá workbench y Ctrl+F5";
        return;
      }
      var cur = currentCaps();
      var curTag = cur ? strategyTag(cur).trim() : "";
      el.textContent =
        "Catálogo: " +
        nRun +
        " probables (★) · " +
        nStub +
        " solo catálogo · seleccionada: " +
        (cur ? cur.strategy_name || cur.strategy_id : "?") +
        " " +
        curTag;
    }

    function setErrDetail(msg) {
      if (!errDetailEl) return;
      if (msg) {
        errDetailEl.textContent = msg;
        errDetailEl.hidden = false;
      } else {
        errDetailEl.textContent = "";
        errDetailEl.hidden = true;
      }
    }

    function shortErr(msg) {
      if (!msg) return "";
      var s = String(msg);
      return s.length > 140 ? s.slice(0, 137) + "…" : s;
    }

    function renderSourceContext(prefill) {
      if (!sourceCtxEl) return;
      if (!prefill || !prefill.source_module) {
        sourceCtxEl.hidden = true;
        sourceCtxEl.innerHTML = "";
        return;
      }
      var mod = prefill.source_module;
      var modLabel =
        mod === "alpha_scanner"
          ? "Alpha Scanner"
          : mod === "simulator"
            ? "Simulador"
            : mod === "montecarlo"
              ? "Monte Carlo"
              : mod;
      var lines = [];
      if (prefill.message) lines.push(prefill.message);
      if (prefill.sim_context && prefill.sim_context.summary_line) {
        lines.push(prefill.sim_context.summary_line);
      }
      if (prefill.scan_id) lines.push("scan_id: " + prefill.scan_id);
      if (prefill.monte_carlo_id) lines.push("monte_carlo_id: " + prefill.monte_carlo_id);
      if (prefill.score != null) lines.push("score: " + prefill.score);
      if (prefill.interval) lines.push("TF: " + prefill.interval);
      if (prefill.venue) lines.push("venue: " + prefill.venue);
      if (prefill.market_type) lines.push("mercado: " + prefill.market_type);
      if (prefill.sim_context && prefill.sim_context.pairs && prefill.sim_context.pairs.length) {
        lines.push(
          "pares: " +
            prefill.sim_context.pairs
              .map(function (p) {
                return (p.venue || "?") + "/" + (p.ticker || p.underlying || "?");
              })
              .join(", ")
        );
      }
      sourceCtxEl.hidden = false;
      sourceCtxEl.innerHTML =
        '<div class="slt-source-title">Origen: <b>' +
        esc(modLabel) +
        "</b></div>" +
        '<div class="slt-source-body mono">' +
        esc(lines.filter(Boolean).join(" · ") || "Contexto cargado") +
        '</div><p class="muted slt-source-foot">Revisá la config · pasá el mouse sobre cada campo · luego <b>▶ INICIAR CORRIDA</b></p>';
    }

    function setTab(name) {
      root.querySelectorAll(".slt-tab").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === name);
      });
      root.querySelectorAll(".slt-tab-panel").forEach(function (p) {
        p.classList.toggle("active", p.getAttribute("data-panel") === name);
      });
    }

    root.querySelectorAll(".slt-tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setTab(btn.getAttribute("data-tab"));
      });
    });

    function renderPhase(summary, paperStatus) {
      if (!phaseEl) return;
      var running = summary && summary.paper_running;
      var blocker = summary && summary.paper_blocker;
      var errRaw = (summary && summary.error) || (paperStatus && paperStatus.last_error);
      var steps =
        summary && summary.steps != null
          ? summary.steps
          : paperStatus && paperStatus.steps;
      var maxS =
        summary && summary.max_steps != null
          ? summary.max_steps
          : paperStatus && paperStatus.max_steps;

      /* last_error del paper session persiste en idle — no mostrar Error fantasma */
      var err = running ? errRaw : null;

      if (running && errRaw) {
        phaseEl.textContent = "● Error en corrida";
        phaseEl.className = "slt-phase slt-phase-err";
        setErrDetail(shortErr(errRaw));
        return;
      }
      setErrDetail(null);

      if (running) {
        phaseEl.textContent = "● Corriendo";
        phaseEl.className = "slt-phase slt-phase-run";
        return;
      }
      if (maxS && steps != null && steps >= maxS) {
        phaseEl.textContent = "● Terminada";
        phaseEl.className = "slt-phase slt-phase-stop";
        return;
      }
      if (summary && summary.phase === "STOPPED") {
        phaseEl.textContent = "● Terminada";
        phaseEl.className = "slt-phase slt-phase-stop";
        return;
      }
      if (sessionId && steps != null && steps > 0) {
        phaseEl.textContent = "● Terminada";
        phaseEl.className = "slt-phase slt-phase-stop";
        return;
      }
      if (blocker && sessionId) {
        phaseEl.textContent = "● Sin motor paper";
        phaseEl.className = "slt-phase slt-phase-warn";
        setErrDetail(blocker);
        return;
      }
      if (sessionId) {
        phaseEl.textContent = "● Registrada";
        phaseEl.className = "slt-phase slt-phase-idle";
        return;
      }
      phaseEl.textContent = "● Listo";
      phaseEl.className = "slt-phase slt-phase-off";
    }

    function hideClosure() {
      var box = root.querySelector("#slt-closure-box");
      if (box) box.hidden = true;
      closureShown = false;
    }

    function renderClosureSummary(closure) {
      if (!closure) return;
      var box = root.querySelector("#slt-closure-box");
      var head = root.querySelector("#slt-closure-head");
      var doneEl = root.querySelector("#slt-closure-done");
      var notEl = root.querySelector("#slt-closure-not");
      var metEl = root.querySelector("#slt-closure-metrics");
      if (!box || !doneEl || !notEl) return;
      if (head) head.textContent = closure.headline || "Resumen final";
      var done = closure.done || [];
      var notDone = closure.not_done || [];
      doneEl.innerHTML = done.length
        ? done.map(function (line) {
            return "<li>" + esc(line) + "</li>";
          }).join("")
        : "<li class=\"muted\">—</li>";
      notEl.innerHTML = notDone.length
        ? notDone.map(function (line) {
            return "<li>" + esc(line) + "</li>";
          }).join("")
        : "<li class=\"muted\">Nada pendiente adicional</li>";
      if (metEl) {
        var m = closure.metrics || {};
        var elapsed =
          runStartedAt != null
            ? Math.round((Date.now() - runStartedAt) / 1000) + "s"
            : "—";
        metEl.innerHTML =
          "<strong>" +
          esc(m.strategy_name || m.strategy_id || "—") +
          "</strong> · " +
          esc(m.symbol || "—") +
          " · " +
          esc(m.destination || "PAPER") +
          " · estado <b>" +
          esc(String(m.session_state || "—")) +
          "</b> · steps " +
          esc(String(m.steps != null ? m.steps : "—")) +
          "/" +
          esc(String(m.max_steps != null ? m.max_steps : "—")) +
          " · fills " +
          esc(String(m.fills != null ? m.fills : 0)) +
          " · equity " +
          fmtNum(m.equity) +
          " · PnL " +
          fmtNum(m.realized_pnl != null ? m.realized_pnl : m.unrealized_pnl) +
          " · t " +
          elapsed +
          (m.error ? " · <span style=\"color:var(--danger,#f66)\">" + esc(m.error) + "</span>" : "");
      }
      box.hidden = false;
      closureShown = true;
      logEvent("RESUMEN: " + (closure.headline || closure.outcome));
      box.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function renderLive(live) {
      lastLive = live;
      if (!live) return;
      var summary = live.live_summary || {};
      var ps = live.paper_status || {};
      var running = !!summary.paper_running;
      if (lastPaperRunning && !running && sessionId && lastPaperStarted && !closureShown) {
        renderClosureSummary({
          outcome: "completed",
          headline: "Corrida paper terminada — resumen",
          done: lastRunStages
            .filter(function (s) {
              return s.ok;
            })
            .map(function (s) {
              return s.name + (s.detail ? " · " + s.detail : "");
            })
            .concat([
              "Steps " +
                (summary.steps != null ? summary.steps : ps.steps || 0) +
                "/" +
                (summary.max_steps || ps.max_steps || "?"),
              (live.fills_count || 0) + " fill(s)",
            ]),
          not_done: [
            "Órdenes Spot/Futures testnet remotas (bloqueado MVP)",
            "Producción LIVE (bloqueada)",
          ],
          metrics: {
            fills: live.fills_count,
            steps: summary.steps || ps.steps,
            max_steps: summary.max_steps || ps.max_steps,
            equity: live.pnl && live.pnl.equity,
            realized_pnl: live.pnl && live.pnl.realized_pnl,
            session_state: summary.phase,
            strategy_id: summary.strategy_id,
            strategy_name: summary.strategy_name,
            symbol: summary.symbol_resolved || summary.symbol,
            destination: summary.destination,
            error: summary.error || ps.last_error,
          },
        });
        stopPoll();
        runStartedAt = null;
      }
      lastPaperRunning = running;
      var pnl = live.pnl || {};
      var mkt = live.market || {};
      renderPhase(summary, ps);

      if (metricsEl) {
        var elapsed = runStartedAt ? Math.round((Date.now() - runStartedAt) / 1000) + "s" : "—";
        metricsEl.innerHTML =
          "<span><b>" +
          esc(summary.strategy_name || summary.strategy_id || "—") +
          "</b></span> · " +
          "<span class=\"mono\">" +
          esc(summary.symbol_resolved || summary.symbol || "—") +
          "</span> · " +
          "<span>step " +
          esc(String(summary.steps != null ? summary.steps : ps.steps || 0)) +
          "/" +
          esc(String(summary.max_steps || ps.max_steps || "?")) +
          "</span> · " +
          "<span>equity " +
          fmtNum(pnl.equity) +
          "</span> · " +
          "<span>PnL " +
          fmtNum(pnl.total_pnl != null ? pnl.total_pnl : pnl.unrealized) +
          "</span> · " +
          "<span>fills " +
          esc(String(live.fills_count || 0)) +
          "</span> · " +
          "<span>t " +
          elapsed +
          "</span>";
      }

      if (progressEl) {
        var pct = summary.progress_pct || 0;
        progressEl.style.width = Math.min(100, Math.max(0, pct)) + "%";
      }

      if (lastActEl) {
        var lf = live.last_fill;
        if (lf) {
          lastActEl.textContent =
            "Último fill: " +
            (lf.side || "?") +
            " " +
            (lf.quantity || lf.qty || "?") +
            " @ " +
            (lf.price || "?") +
            " · " +
            (lf.symbol || lf.instrument_id || "");
        } else if (mkt && (mkt.bid || mkt.last)) {
          lastActEl.textContent =
            "MD: bid=" +
            fmtNum(mkt.bid) +
            " ask=" +
            fmtNum(mkt.ask) +
            " last=" +
            fmtNum(mkt.last);
        } else if (summary.paper_running) {
          lastActEl.textContent = "Estrategia activa — esperando señal / próximo step…";
        } else {
          lastActEl.textContent =
            summary.paper_blocker || live.paper_blocker || "Sin actividad paper";
        }
      }

      renderResumen(live);
      renderOrdenes(live);
      renderPosiciones(live);
      renderMercado(live);
      renderTecnico(live);
    }

    function renderResumen(live) {
      var el = root.querySelector("#slt-panel-resumen");
      if (!el) return;
      var s = live.live_summary || {};
      var sess = live.execution_session || {};
      var man = sess.manifest || {};
      var ps = live.paper_status || {};
      var pnl = live.pnl || {};
      var caps = live.capabilities || {};
      var eq = live.equity_curve || [];
      var eqRows = eq.length
        ? eq
            .slice(-12)
            .reverse()
            .map(function (p) {
              return (
                "<tr><td>" +
                esc(fmtDt(p.ts || p.timestamp || p.step || "")) +
                "</td><td>" +
                fmtNum(p.equity) +
                "</td><td>" +
                fmtNum(p.cash) +
                "</td><td>" +
                esc(String(p.step != null ? p.step : "")) +
                "</td></tr>"
              );
            })
            .join("")
        : "<tr><td colspan=\"4\" class=\"muted\">Sin puntos equity aún</td></tr>";
      el.innerHTML =
        "<table class=\"sim-summary-table mono\" style=\"width:100%;font-size:1.08em\">" +
        "<tr><th>Estrategia</th><td>" +
        esc(man.strategy_name || man.strategy_id || s.strategy_name) +
        "</td></tr>" +
        "<tr><th>Símbolo</th><td>" +
        esc(s.symbol_resolved || man.symbol || s.symbol) +
        (s.symbol_resolved &&
        man.symbol &&
        s.symbol_resolved.toUpperCase() !== String(man.symbol).toUpperCase()
          ? ' <span class="muted">(manifest ' + esc(man.symbol) + " → MD " + esc(s.symbol_resolved) + ")</span>"
          : "") +
        "</td></tr>" +
        "<tr><th>Destino</th><td>" +
        esc(man.execution_destination || s.destination) +
        "</td></tr>" +
        "<tr><th>Estado sesión</th><td>" +
        esc(sess.state || s.phase) +
        (s.paper_running ? " · <b>PAPER ON</b>" : "") +
        "</td></tr>" +
        "<tr><th>Session / Promo</th><td class=\"mono\">" +
        esc(s.session_id || sess.session_id || "—") +
        " · " +
        esc(s.promotion_id || man.promotion_id || "—") +
        "</td></tr>" +
        "<tr><th>PnL</th><td>realized " +
        fmtNum(pnl.realized_pnl) +
        " · unrealized " +
        fmtNum(pnl.unrealized_pnl) +
        " · equity " +
        fmtNum(pnl.equity) +
        " · cash " +
        fmtNum(pnl.cash) +
        "</td></tr>" +
        "<tr><th>Paper status</th><td>running=" +
        esc(String(ps.running)) +
        " · steps " +
        esc(String(ps.steps || 0)) +
        "/" +
        esc(String(ps.max_steps || "?")) +
        (ps.last_error ? " · <span style=\"color:var(--err,#f66)\">" + esc(ps.last_error) + "</span>" : "") +
        "</td></tr>" +
        (s.paper_blocker
          ? "<tr><th>Aviso</th><td style=\"color:var(--warn,#c90)\">" + esc(s.paper_blocker) + "</td></tr>"
          : "") +
        (sourcePrefill && sourcePrefill.source_module
          ? "<tr><th>Origen UI</th><td>" +
            esc(sourcePrefill.source_module) +
            (sourcePrefill.message ? " · " + esc(sourcePrefill.message) : "") +
            "</td></tr>"
          : "") +
        (man.historical_metrics && Object.keys(man.historical_metrics).length
          ? "<tr><th>Métricas origen</th><td><pre style=\"margin:0;white-space:pre-wrap;max-height:5rem;overflow:auto\">" +
            esc(JSON.stringify(man.historical_metrics, null, 2)) +
            "</pre></td></tr>"
          : "") +
        "<tr><th>Certificación</th><td>paper_run=" +
        esc(String(caps.paper_run_certified)) +
        " · spot_testnet=" +
        esc(String(caps.spot_testnet_supported)) +
        " · " +
        esc(caps.certification_status || "") +
        "</td></tr>" +
        "<tr><th>Parámetros</th><td><pre style=\"margin:0;white-space:pre-wrap;max-height:6rem;overflow:auto\">" +
        esc(JSON.stringify(man.strategy_parameters || {}, null, 2)) +
        "</pre></td></tr>" +
        "<tr><th>Broker</th><td>" +
        (live.broker_connected ? "Paper conectado · " + esc(live.venue || "") : "desconectado") +
        "</td></tr></table>" +
        "<h4 style=\"margin:0.65rem 0 0.25rem;font-size:1.12em\">Curva equity (últimos puntos)</h4>" +
        '<table class="sim-summary-table mono" style="width:100%;font-size:1.04em">' +
        "<thead><tr><th>TS</th><th>Equity</th><th>Cash</th><th>Step</th></tr></thead>" +
        "<tbody>" +
        eqRows +
        "</tbody></table>";
    }

    function renderOrdenes(live) {
      var el = root.querySelector("#slt-panel-ordenes");
      if (!el) return;
      var fills = live.fills || [];
      if (!fills.length) {
        el.innerHTML = '<p class="muted">Sin fills aún.</p>';
        return;
      }
      var rows = fills
        .slice()
        .reverse()
        .map(function (f) {
          return (
            "<tr><td>" +
            esc(fmtDt(f.ts || f.timestamp || "")) +
            "</td><td>" +
            esc(f.side) +
            "</td><td>" +
            esc(f.symbol || f.instrument_id) +
            "</td><td>" +
            fmtNum(f.quantity || f.qty) +
            "</td><td>" +
            fmtNum(f.price) +
            "</td><td>" +
            esc(f.order_id || "") +
            "</td></tr>"
          );
        })
        .join("");
      el.innerHTML =
        '<table class="sim-summary-table mono" style="width:100%;font-size:1.04em">' +
        "<thead><tr><th>Hora</th><th>Side</th><th>Sym</th><th>Qty</th><th>Px</th><th>Order</th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table>";
    }

    function renderPosiciones(live) {
      var el = root.querySelector("#slt-panel-posiciones");
      if (!el) return;
      var pos = live.positions || [];
      var book = live.book || {};
      var acc = book.account || {};
      var posRows = pos.length
        ? pos
            .map(function (p) {
              return (
                "<tr><td>" +
                esc(p.symbol || p.instrument_id) +
                "</td><td>" +
                fmtNum(p.quantity || p.qty) +
                "</td><td>" +
                fmtNum(p.avg_price || p.average_price) +
                "</td><td>" +
                fmtNum(p.unrealized_pnl) +
                "</td></tr>"
              );
            })
            .join("")
        : "<tr><td colspan=\"4\" class=\"muted\">Sin posiciones</td></tr>";
      el.innerHTML =
        "<p class=\"mono\" style=\"margin:0 0 0.35rem\">Cash: " +
        fmtNum(acc.cash || acc.balance) +
        " · Equity: " +
        fmtNum((live.pnl && live.pnl.equity) || acc.equity) +
        "</p>" +
        '<table class="sim-summary-table mono" style="width:100%;font-size:1.04em">' +
        "<thead><tr><th>Símbolo</th><th>Qty</th><th>Avg</th><th>uPnL</th></tr></thead>" +
        "<tbody>" +
        posRows +
        "</tbody></table>";
    }

    function renderMercado(live) {
      var el = root.querySelector("#slt-panel-mercado");
      if (!el) return;
      var m = live.market;
      if (!m) {
        el.innerHTML = '<p class="muted">Sin snapshot (conectá broker con INICIAR).</p>';
        return;
      }
      el.innerHTML =
        "<pre class=\"mono\" style=\"white-space:pre-wrap;margin:0;font-size:1.06em\">" +
        esc(JSON.stringify(m, null, 2)) +
        "</pre>";
    }

    function renderEvents() {
      var el = root.querySelector("#slt-panel-eventos");
      if (!el) return;
      el.innerHTML =
        "<pre class=\"mono\" style=\"white-space:pre-wrap;margin:0;font-size:1.04em;max-height:14rem;overflow:auto\">" +
        esc(eventLog.join("\n")) +
        "</pre>";
    }

    function renderTecnico(live) {
      var el = root.querySelector("#slt-panel-tecnico");
      if (!el) return;
      el.innerHTML =
        "<pre class=\"mono\" style=\"white-space:pre-wrap;margin:0;font-size:1.00em;max-height:16rem;overflow:auto\">" +
        esc(JSON.stringify(live || lastLive || {}, null, 2)) +
        "</pre>";
    }

    function buildRunBody() {
      var pf = pendingPrefill ? Object.assign({}, pendingPrefill) : {};
      var op = collectOperationalConfig();
      var stratParams = collectStrategyParams();
      pf.strategy_parameters = stratParams;
      pf.market_type = op.market_type;
      pf.interval = op.interval;
      pf.venue = op.venue;
      pf.interval_ms = op.interval_ms;
      if (op.capital) pf.capital = op.capital;
      if (op.leverage) pf.leverage = op.leverage;
      if (op.period_days) pf.period_days = op.period_days;
      if (op.per_trade_usd) pf.per_trade_usd = op.per_trade_usd;
      if (pf.sim_context) {
        pf.sim_context = Object.assign({}, pf.sim_context, {
          market_type: op.market_type,
          interval: op.interval,
          initial_capital: op.capital || pf.sim_context.initial_capital,
          leverage: op.leverage || pf.sim_context.leverage,
          per_trade_usd: op.per_trade_usd || pf.sim_context.per_trade_usd,
          period_days: op.period_days || pf.sim_context.period_days,
          params: stratParams,
        });
      }
      var body = {
        source_module: pf.source_module || "manual",
        strategy_id: stratSel ? stratSel.value : "buy_once",
        symbol: symIn ? symIn.value : "BTCUSDT",
        execution_destination: destSel ? destSel.value : "PAPER",
        market_type: op.market_type || "spot",
        max_steps: stepsIn ? parseInt(stepsIn.value, 10) || 25 : 25,
        interval_ms: op.interval_ms,
        strategy_parameters: stratParams,
      };
      if (op.interval) body.interval = op.interval;
      if (op.venue) body.venue = op.venue;
      if (op.capital) body.capital = op.capital;
      if (op.leverage) body.leverage = op.leverage;
      if (pf.scan_id) body.scan_id = pf.scan_id;
      if (pf.monte_carlo_id) body.monte_carlo_id = pf.monte_carlo_id;
      if (pf.backtest_id) body.backtest_id = pf.backtest_id;
      if (pf.simulation_id) body.simulation_id = pf.simulation_id;
      if (pf.sim_context) body.sim_context = pf.sim_context;
      if (pf.underlying) body.underlying = pf.underlying;
      if (pf.score != null) body.score = pf.score;
      if (pf.profile) body.profile = pf.profile;
      if (pf.strategies) body.strategies = pf.strategies;
      if (pf.monte_carlo_metrics) body.monte_carlo_metrics = pf.monte_carlo_metrics;
      pendingPrefill = pf;
      return body;
    }

    function stopPoll() {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }

    function startPoll() {
      stopPoll();
      pollTimer = setInterval(function () {
        if (!sessionId && !lastLive) return;
        QLApi.executionLive(sessionId)
          .then(function (res) {
            if (res && res.live) renderLive(res.live);
          })
          .catch(function () {});
      }, 1200);
    }

    function loadHistory() {
      if (!QLApi.executionSessions) return;
      QLApi.executionSessions().then(function (res) {
        var list = (res && res.sessions) || [];
        var el = root.querySelector("#slt-hist-list");
        if (!el) return;
        if (!list.length) {
          el.textContent = "Sin corridas previas.";
          return;
        }
        el.innerHTML = list
          .slice(0, 8)
          .map(function (s) {
            var m = s.manifest || {};
            var when = fmtDt(s.updated_at || s.created_at);
            return (
              '<div class="slt-hist-row" data-sid="' +
              esc(s.session_id) +
              '" style="cursor:pointer;padding:0.15rem 0;border-bottom:1px solid var(--border,#333)">' +
              '<span class="muted">' +
              esc(when) +
              "</span> · " +
              esc(s.session_id.slice(0, 8)) +
              " · " +
              esc(m.strategy_id) +
              " · " +
              esc(m.symbol) +
              " · " +
              esc(s.state) +
              (s.paper_session_running ? " <b>ON</b>" : "") +
              ' <span class="muted">↺ reabrir</span></div>'
            );
          })
          .join("");
        el.querySelectorAll(".slt-hist-row").forEach(function (row) {
          row.addEventListener("click", function () {
            var sid = row.getAttribute("data-sid");
            var s = list.find(function (x) {
              return x.session_id === sid;
            });
            if (!s || !s.manifest) return;
            stratSel.value = s.manifest.strategy_id || "buy_once";
            symIn.value = s.manifest.symbol || "BTCUSDT";
            destSel.value = s.manifest.execution_destination || "PAPER";
            refreshHint();
            logEvent("Reabierto config de " + sid);
          });
        });
      });
    }

    function loadStrategies() {
      return QLApi.executionStrategies().then(function (res) {
        strategies = (res && res.strategies) || [];
        familyLabels = (res && res.family_labels_es) || {};
        if (res && res.family_order && res.family_order.length) {
          familyOrder = res.family_order;
        }
        if (!stratSel) return res;
        var byFam = {};
        strategies.forEach(function (s) {
          var f = s.family || "other";
          if (!byFam[f]) byFam[f] = [];
          byFam[f].push(s);
        });
        var famKeys = familyOrder.filter(function (f) {
          return byFam[f] && byFam[f].length;
        }).concat(
          Object.keys(byFam)
            .filter(function (f) {
              return familyOrder.indexOf(f) < 0;
            })
            .sort()
        );
        stratSel.innerHTML = famKeys
          .map(function (fam) {
            var label = familyLabels[fam] || fam;
            var inner = (byFam[fam] || [])
              .slice()
              .sort(function (a, b) {
                var na = String(a.strategy_name || a.strategy_id).toLowerCase();
                var nb = String(b.strategy_name || b.strategy_id).toLowerCase();
                if (na < nb) return -1;
                if (na > nb) return 1;
                return 0;
              })
              .map(function (s) {
                var certified = isPaperRunnable(s);
                var tag = strategyTag(s);
                var dis = certified ? "" : " disabled";
                return (
                  '<option value="' +
                  esc(s.strategy_id) +
                  '"' +
                  dis +
                  ">" +
                  esc(s.strategy_name || s.strategy_id) +
                  tag +
                  "</option>"
                );
              })
              .join("");
            return "<optgroup label=\"" + esc(label) + "\">" + inner + "</optgroup>";
          })
          .join("");
        if (stratSel.querySelector('[value="buy_once"]')) stratSel.value = "buy_once";
        renderStrategyParams(
          pendingPrefill && pendingPrefill.strategy_parameters
        );
        updateCatalogLine();
        refreshHint();
        if (pendingPrefill) applyPrefillInner(pendingPrefill);
        return res;
      }).catch(function (err) {
        if (hintEl) {
          hintEl.textContent =
            "No cargó /api/execution/strategies — reiniciá este.bat y Ctrl+F5. " +
            (err && err.message ? err.message : "");
          hintEl.style.color = "var(--danger,#f66)";
        }
        throw err;
      });
    }

    function applyPrefillInner(prefill) {
      if (!prefill) return;
      sourcePrefill = prefill;
      pendingPrefill = prefill;
      renderSourceContext(prefill);
      if (prefill.message) logEvent("Handoff: " + prefill.message);
      if (prefill.strategy_id && stratSel) {
        if (stratSel.querySelector('[value="' + prefill.strategy_id + '"]')) {
          stratSel.value = prefill.strategy_id;
        }
      }
      if (prefill.symbol && symIn) symIn.value = prefill.symbol;
      if (prefill.underlying && symIn && !prefill.symbol) {
        var u = String(prefill.underlying).toUpperCase();
        symIn.value = u.indexOf("USDT") >= 0 ? u : u + "USDT";
      }
      if (prefill.sim_context) {
        var ctx = prefill.sim_context;
        if (!prefill.strategy_id && ctx.strategy_id && stratSel) {
          if (stratSel.querySelector('[value="' + ctx.strategy_id + '"]')) {
            stratSel.value = ctx.strategy_id;
          }
        }
        if (!prefill.symbol && ctx.coin && symIn) {
          var c = String(ctx.coin).toUpperCase();
          symIn.value = c.indexOf("USDT") >= 0 ? c.split(",")[0].trim() : c.split(",")[0].trim() + "USDT";
        }
        if (ctx.market_type && !prefill.market_type) prefill.market_type = ctx.market_type;
      }
      if (prefill.execution_destination && destSel) {
        destSel.value = prefill.execution_destination;
      }
      if (prefill.max_steps != null && stepsIn) {
        stepsIn.value = String(prefill.max_steps);
      }
      applyOperationalPrefill(prefill);
      renderStrategyParams(
        prefill.strategy_parameters ||
          (prefill.sim_context && prefill.sim_context.params)
      );
      updateCatalogLine();
      refreshHint();
    }

    root.applyPrefill = function (prefill) {
      pendingPrefill = prefill || null;
      renderSourceContext(prefill);
      if (strategies.length) applyPrefillInner(prefill);
    };

    if (stratSel) {
      stratSel.addEventListener("change", function () {
        renderStrategyParams();
        updateCatalogLine();
        refreshHint();
      });
    }
    if (destSel) {
      destSel.addEventListener("change", function () {
        updateCatalogLine();
        refreshHint();
      });
    }

    startBtn.addEventListener("click", function () {
      startBtn.disabled = true;
      hideClosure();
      lastPaperRunning = false;
      lastPaperStarted = false;
      logEvent("INICIAR — pipeline automático…");
      QLApi.executionRun(buildRunBody())
        .then(function (res) {
          sessionId = res.session_id;
          runStartedAt = Date.now();
          lastRunStages = res.stages || [];
          lastPaperStarted = !!res.paper_started;
          stopBtn.disabled = !sessionId;
          if (res.stages) {
            res.stages.forEach(function (st) {
              logEvent(st.name + ": " + (st.ok ? "OK" : "FAIL") + (st.detail ? " · " + JSON.stringify(st.detail) : ""));
            });
          }
          if (res.paper_started) {
            logEvent("Corrida PAPER iniciada · session " + sessionId);
            lastPaperRunning = true;
          } else if (res.paper_blocker) {
            logEvent("Aviso: " + res.paper_blocker);
          }
          if (sessionId) startPoll();
          renderLive(res.live || {});
          if (res.closure_summary) {
            renderClosureSummary(res.closure_summary);
          }
          loadHistory();
        })
        .catch(function (err) {
          logEvent("ERROR: " + (err.message || err));
          setErrDetail(shortErr(err.message || err));
          if (phaseEl) {
            phaseEl.textContent = "● Falló al iniciar";
            phaseEl.className = "slt-phase slt-phase-err";
          }
        })
        .finally(function () {
          startBtn.disabled = false;
          refreshHint();
        });
    });

    stopBtn.addEventListener("click", function () {
      if (!sessionId) return;
      stopBtn.disabled = true;
      QLApi.executionStopSession(sessionId)
        .then(function (res) {
          logEvent("DETENIDA session " + sessionId);
          stopPoll();
          lastPaperRunning = false;
          if (res.live) renderLive(res.live);
          if (res.closure_summary) {
            renderClosureSummary(res.closure_summary);
          }
          runStartedAt = null;
          loadHistory();
        })
        .catch(function (err) {
          logEvent("Stop error: " + (err.message || err));
        })
        .finally(function () {
          stopBtn.disabled = false;
        });
    });

    loadStrategies()
      .then(function () {
        loadHistory();
        return QLApi.executionLive(null);
      })
      .then(function (res) {
        if (res && res.live && res.live.execution_session) {
          sessionId = res.live.execution_session.session_id;
          stopBtn.disabled = !sessionId;
          if (res.live.live_summary && res.live.live_summary.paper_running) {
            runStartedAt = Date.now();
            startPoll();
          }
          renderLive(res.live);
        }
      })
      .catch(function () {});

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createStrategyLiveTestPane = createStrategyLiveTestPane;
})(typeof window