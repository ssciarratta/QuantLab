/** Simulador multi-venue — Comparar + Estrategias (sin duplicar Guided/MC). */
(function (global) {
  "use strict";

  var INTERVALS = [
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M",
  ];
  var PERIODS = [
    { id: "1", label: "1 día", days: 1 },
    { id: "7", label: "1 semana", days: 7 },
    { id: "30", label: "1 mes", days: 30 },
    { id: "90", label: "3 meses", days: 90 },
    { id: "180", label: "6 meses", days: 180 },
    { id: "365", label: "1 año", days: 365 },
  ];
  var VENUES = ["binance", "okx", "bybit", "hyperliquid", "a3"];
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
  // Sinónimos ES → tokens de búsqueda (petróleo → oil/cl/brent…)
  var SEARCH_ALIASES = {
    petroleo: ["oil", "cl", "brent", "wti", "usoil", "brentoil"],
    petroleum: ["oil", "cl", "brent", "wti", "usoil"],
    crudo: ["oil", "cl", "wti", "brent", "usoil"],
    oro: ["gold", "gldmine", "goldjm"],
    plata: ["silver", "silverjm"],
    cobre: ["copper"],
    trigo: ["wheat"],
    maiz: ["corn"],
    soja: ["soy"],
    gas: ["natgas", "gas", "ttf"],
    aluminio: ["aluminium", "aluminum"],
    platino: ["platinum"],
    paladio: ["palladium"],
    uranio: ["uranium"],
    euro: ["eur"],
    libra: ["gbp"],
    yen: ["jpy"],
    nasdaq: ["usa100", "ustech"],
    sp500: ["sp500", "usa500", "us500"],
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function foldText(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function alphaKey(s) {
    return foldText(s);
  }

  function sortByLabel(list) {
    return (list || []).slice().sort(function (a, b) {
      var ka = alphaKey(a.label || a.name || a.id || "");
      var kb = alphaKey(b.label || b.name || b.id || "");
      if (ka < kb) return -1;
      if (ka > kb) return 1;
      return 0;
    });
  }

  function expandSearchQuery(q) {
    var raw = foldText(q).trim();
    if (!raw) return [];
    var tokens = [raw];
    Object.keys(SEARCH_ALIASES).forEach(function (k) {
      if (raw === k || raw.indexOf(k) >= 0 || k.indexOf(raw) >= 0) {
        SEARCH_ALIASES[k].forEach(function (t) {
          if (tokens.indexOf(t) < 0) tokens.push(t);
        });
      }
    });
    return tokens;
  }

  function productMatchesSearch(p, tokens) {
    if (!tokens.length) return true;
    var hay = foldText(
      [p.id, p.name, p.label, p.symbol, p.asset_kind, p.dex, p.dex_full_name, p.expiry_label]
        .filter(Boolean)
        .join(" ")
    );
    return tokens.some(function (t) {
      return hay.indexOf(t) >= 0;
    });
  }

  function optHtml(list, selected) {
    return list
      .map(function (v) {
        var val = typeof v === "object" ? v.id : v;
        var lab = typeof v === "object" ? v.label : v;
        var sel = String(val) === String(selected) ? " selected" : "";
        return "<option value=\"" + esc(val) + "\"" + sel + ">" + esc(lab) + "</option>";
      })
      .join("");
  }

  function createSimulatorPane() {
    var root = document.createElement("div");
    root.className = "pane-simulator";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Simulador</h3>" +
      '<p class="muted" style="margin-top:0">' +
      "<strong>No es lo mismo que Guided Lab ni Backtest.</strong> " +
      "Guided Lab = aprender/practicar (Binance/A3). " +
      "Backtest = velas sintéticas. " +
      "Simulador = comparar Binance/OKX/Bybit/HL/<strong>A3</strong> × productos × leverage. " +
      "TradingView = solo gráfico (link TV en cada chip). " +
      "Futuros A3: margen + diferencias diarias (alerta al agregar). LIVE bloqueado." +
      "</p>" +
      '<div class="sim-tabs" role="tablist">' +
      '<button type="button" class="sim-tab active" data-tab="comparar">Comparar</button>' +
      '<button type="button" class="sim-tab" data-tab="estrategias">Estrategias</button>' +
      "</div></div>" +
      '<div class="pane-section sim-common">' +
      "<h4>Controles de comparación</h4>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.45rem">' +
      '<label class="muted">Modo <select id="sim-market">' +
      '<option value="spot">Spot</option><option value="futures" selected>Futuros</option></select></label>' +
      '<label class="muted">Leverage <input type="range" id="sim-lev" min="1" max="125" value="1" style="vertical-align:middle"> ' +
      '<input type="number" id="sim-lev-num" min="1" max="125" step="1" value="1" style="width:3.6em" data-tip="Apalancamiento.\nPodés usar el deslizador o escribir el número a mano (1–125).\nEn spot suele ir 1x; en futuros podés subir la x."> <span class="muted">x</span></label>' +
      '<label class="muted"><input type="checkbox" id="sim-multi-x"> multi-x (1,2,5,10)</label>' +
      '<label class="muted">Período <select id="sim-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label class="muted">Intervalo <select id="sim-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<span class="mono" id="sim-nbars">≈ — velas</span>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.45rem;margin-top:0.4rem">' +
      '<fieldset class="sim-capital-mode" style="border:1px solid var(--border,#333);border-radius:6px;padding:0.35rem 0.55rem;margin:0">' +
      '<legend class="muted" style="padding:0 0.25rem">Capital</legend>' +
      '<label class="muted"><input type="radio" name="sim-cap-mode" id="sim-cap-fixed" value="fixed" checked> Monto fijo</label> ' +
      '<label class="muted"><input type="radio" name="sim-cap-mode" id="sim-cap-free" value="unconstrained"> Sin monto</label>' +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.45rem;align-items:center;margin-top:0.25rem">' +
      '<label class="muted" id="sim-capital-wrap">Capital USDT <input type="number" id="sim-capital" value="10000" min="1" style="width:6em"></label>' +
      '<label class="muted">Por trade (margen) USDT <input type="number" id="sim-per-trade" value="500" min="1" style="width:5em"></label>' +
      '<span class="mono muted" id="sim-size-hint">—</span>' +
      "</div>" +
      '<p class="muted" id="sim-cap-help" style="font-size:0.72em;margin:0.2rem 0 0;max-width:42rem">' +
      "Siempre se calcula el margen pico aparte del capital. En fijo: ves si te faltó plata. En sin monto: el pico es el capital mínimo sugerido." +
      "</p>" +
      "</fieldset>" +
      '<label class="muted">Bench anual % <input type="number" id="sim-bench" value="5" min="0" step="0.1" style="width:4em"></label>' +
      '<label class="muted"><input type="checkbox" id="sim-liq" checked> liquidación</label>' +
      '<label class="muted"><input type="checkbox" id="sim-funding" checked> funding</label>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.4rem;margin-top:0.35rem;align-items:center">' +
      '<span class="muted">Fees</span> ' +
      '<span class="mono" id="sim-fee-preset" data-tip="Comisiones VIP0 del schedule del lab (por exchange).\nPor defecto cada mercado usa las suyas.\nAbrí el link oficial para corroborar a mano.">—</span>' +
      ' <a id="sim-fee-source" class="sim-fee-link" href="#" target="_blank" rel="noopener noreferrer" hidden>Ver tarifas oficiales</a>' +
      '<label class="muted">maker bps <input id="sim-maker" type="number" step="0.1" style="width:4em"></label>' +
      '<label class="muted">taker bps <input id="sim-taker" type="number" step="0.1" style="width:4em"></label>' +
      '<button type="button" class="btn secondary" id="sim-fee-reset" data-tip="Vuelve a cargar maker/taker del schedule del mercado seleccionado.\nDesactiva el override manual.">Fees del mercado</button>' +
      '<span class="mono muted" id="sim-fee-mode" style="font-size:0.75em">modo: por mercado</span>' +
      '<button type="button" class="btn secondary" id="sim-add-cost">+ Gasto extra</button>' +
      "</div>" +
      '<div id="sim-extra-costs" class="mono muted" style="font-size:0.8em"></div>' +
      "</div>" +
      '<div class="pane-section sim-panel" data-panel="comparar">' +
      "<h4>Comparar mercados (histórico)</h4>" +
      '<div class="pane-row sim-step-first" style="flex-wrap:wrap;gap:0.45rem;align-items:center">' +
      "<strong>1.</strong> " +
      '<label class="muted">Estrategia <select id="sim-strat-hist"></select></label>' +
      '<button type="button" class="btn secondary" id="sim-strat-info" data-tip="Abre una ventana del escritorio (mover, redimensionar, minimizar, cerrar ×) con el detalle de la estrategia.">¿Cómo opera?</button>' +
      '<button type="button" class="btn" id="sim-run-hist">Correr y comparar</button>' +
      "</div>" +
      '<p class="muted" style="font-size:0.8em;margin:0.55rem 0 0.35rem"><strong>2.</strong> Mercados y monedas (uno al lado del otro):</p>' +
      '<div id="sim-venue-picks" class="sim-venue-picks">cargando monedas…</div>' +
      '<p class="muted" style="font-size:0.8em;margin:0.45rem 0 0">' +
      'Atajos: <button type="button" class="btn secondary" id="sim-open-gl">Guided Lab</button> ' +
      '<button type="button" class="btn secondary" id="sim-open-mc">Monte Carlo</button> ' +
      '<button type="button" class="btn secondary" id="sim-open-blotter">Paper Blotter</button>' +
      "</p>" +
      '<div class="mono" id="sim-out-hist">—</div></div>' +
      '<div class="pane-section sim-panel" data-panel="estrategias" style="display:none">' +
      "<h4>Catálogo por familia</h4>" +
      '<p class="muted" style="margin-top:0">Desplegá una familia · «Cómo opera» abre una ventana del escritorio · Usar la pone en Comparar.</p>' +
      '<div id="sim-strat-list">cargando…</div></div>';

    var extraCosts = [];
    var feeSchedules = [];
    /** Si true, maker/taker editados se envían como override a todos los venues. */
    var feesManualOverride = false;
    var strategiesCache = [];
    var familyLabels = {};
    var guideStrategyId = null;
    var coinsCache = [];
    /** @type {Object.<string, Array>} */
    var productsByVenue = {};
    var venueMeta = [];
    /** @type {Object.<string, string[]>} */
    var selectedByVenue = {};
    /** @type {Object.<string, boolean>} */
    var venueEnabled = {
      binance: true,
      okx: false,
      bybit: false,
      hyperliquid: false,
      a3: false,
    };
    /** Texto de búsqueda por venue (se conserva al re-render). */
    var searchByVenue = {};
    var STRAT_GUIDE_WIN = "sim_strategy_guide";

    function showTab(name) {
      root.querySelectorAll(".sim-tab").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === name);
      });
      root.querySelectorAll(".sim-panel").forEach(function (p) {
        p.style.display = p.getAttribute("data-panel") === name ? "" : "none";
      });
    }

    function productFor(venue, id) {
      var list = productsByVenue[venue] || coinsCache || [];
      return (
        list.find(function (x) {
          return x.id === id;
        }) || null
      );
    }

    function coinLabel(venue, id) {
      var c = productFor(venue, id);
      if (!c) return id;
      var base = c.label || c.name + " (" + c.id + ")";
      var kind = c.expiry_label || "";
      if (kind && base.indexOf(kind) < 0) {
        return base + " · " + kind;
      }
      return base;
    }

    function maybeWarnMargin(venue, id) {
      var p = productFor(venue, id);
      if (!p) return;
      if (p.is_delisted || p.tradable === false) {
        window.alert(
          "Este mercado está marcado delisted en Hyperliquid ahora.\n" +
            "Podés verlo en el catálogo, pero las velas/simulación pueden fallar.\n\n" +
            "Producto: " +
            (p.label || id)
        );
        return;
      }
      if (!p.has_daily_variation && p.contract_kind !== "dated") return;
      var msg =
        (p.margin_note ||
          "Este contrato puede requerir margen y diferencias diarias.") +
        "\n\nProducto: " +
        (p.label || id) +
        "\nTipo: " +
        (p.expiry_label || p.contract_kind || "—");
      window.alert(msg);
    }

    function filteredProducts(vid) {
      var plist = sortByLabel(productsByVenue[vid] || coinsCache || []);
      var tokens = expandSearchQuery(searchByVenue[vid] || "");
      if (!tokens.length) return plist;
      return plist.filter(function (p) {
        return productMatchesSearch(p, tokens);
      });
    }

    function optionsHtmlForVenue(vid, plist) {
      return plist
        .map(function (c) {
          return (
            '<option value="' +
            esc(c.id) +
            '">' +
            esc(c.label || c.name + " (" + c.id + ")") +
            "</option>"
          );
        })
        .join("");
    }

    function renderVenuePicks() {
      var box = root.querySelector("#sim-venue-picks");
      if (!venueMeta.length) {
        venueMeta = VENUES.map(function (v) {
          return { id: v, name: v, label: v };
        });
      }
      var anyProducts = Object.keys(productsByVenue).some(function (k) {
        return (productsByVenue[k] || []).length > 0;
      });
      if (!anyProducts && !coinsCache.length) {
        box.textContent = "sin catálogo de productos";
        return;
      }
      box.innerHTML = venueMeta
        .map(function (vm) {
          var vid = vm.id;
          var allList = sortByLabel(productsByVenue[vid] || coinsCache || []);
          var q = searchByVenue[vid] || "";
          var plist = filteredProducts(vid);
          if (!selectedByVenue[vid]) {
            selectedByVenue[vid] =
              vid === "binance" ? ["BTC", "ETH"] : [];
          }
          if (venueEnabled[vid] == null) {
            venueEnabled[vid] = selectedByVenue[vid].length > 0;
          }
          var checked = !!venueEnabled[vid];
          var chips = (selectedByVenue[vid] || [])
            .map(function (cid) {
              var p = productFor(vid, cid);
              var tv =
                p && p.tradingview_url
                  ? ' <a class="sim-tv-link" href="' +
                    esc(p.tradingview_url) +
                    '" target="_blank" rel="noopener noreferrer" title="Abrir en TradingView (solo gráfico)">TV</a>'
                  : "";
              var tag =
                p && p.expiry_label
                  ? ' <span class="sim-expiry-tag">' +
                    esc(p.expiry_label) +
                    "</span>"
                  : "";
              return (
                '<span class="sim-coin-chip">' +
                esc(coinLabel(vid, cid)) +
                tag +
                tv +
                ' <button type="button" class="sim-coin-rm" data-venue="' +
                esc(vid) +
                '" data-coin="' +
                esc(cid) +
                '" title="Quitar">×</button></span>'
              );
            })
            .join(" ");
          var searchPh =
            vid === "hyperliquid"
              ? "Buscar: petróleo, oro, GOLD, trigo…"
              : vid === "a3"
                ? "Buscar: soja, maíz, trigo…"
                : "Buscar moneda / ticker…";
          var countTxt =
            (q
              ? plist.length + " / " + allList.length
              : String(allList.length)) + " productos";
          var kindHint = "";
          if (vid === "hyperliquid" && allList.length) {
            var kinds = {};
            allList.forEach(function (p) {
              var k = p.asset_kind || "otro";
              kinds[k] = (kinds[k] || 0) + 1;
            });
            kindHint =
              " · " +
              ["commodity", "equity", "fx", "index", "crypto"]
                .filter(function (k) {
                  return kinds[k];
                })
                .map(function (k) {
                  return k + " " + kinds[k];
                })
                .join(" · ");
          }
          return (
            '<div class="sim-venue-row' +
            (vid === "hyperliquid" ? " sim-venue-row-wide" : "") +
            '" data-venue="' +
            esc(vid) +
            '">' +
            '<label class="muted"><input type="checkbox" class="sim-venue-on" value="' +
            esc(vid) +
            '"' +
            (checked ? " checked" : "") +
            "> <strong>" +
            esc(vm.label || vm.name || vid) +
            "</strong></label>" +
            '<div class="sim-venue-pick-row">' +
            '<input type="search" class="sim-coin-search" data-venue="' +
            esc(vid) +
            '" placeholder="' +
            esc(searchPh) +
            '" value="' +
            esc(q) +
            '"' +
            (checked ? "" : " disabled") +
            ">" +
            '<select class="sim-coin-select" data-venue="' +
            esc(vid) +
            '" size="7"' +
            (checked ? "" : " disabled") +
            ">" +
            (plist.length
              ? optionsHtmlForVenue(vid, plist)
              : '<option value="">(sin coincidencias)</option>') +
            "</select>" +
            '<div class="sim-coin-meta muted">' +
            esc(countTxt + kindHint) +
            "</div>" +
            '<button type="button" class="btn secondary sim-coin-add" data-venue="' +
            esc(vid) +
            '"' +
            (checked ? "" : " disabled") +
            ">Agregar</button>" +
            "</div>" +
            '<div class="sim-coin-chips" data-venue="' +
            esc(vid) +
            '">' +
            (chips || '<span class="muted">ningún producto</span>') +
            "</div></div>"
          );
        })
        .join("");

      box.querySelectorAll(".sim-coin-search").forEach(function (inp) {
        inp.addEventListener("input", function () {
          var vid = inp.getAttribute("data-venue");
          searchByVenue[vid] = inp.value || "";
          var sel = box.querySelector('.sim-coin-select[data-venue="' + vid + '"]');
          var meta = box.querySelector(
            '.sim-venue-row[data-venue="' + vid + '"] .sim-coin-meta'
          );
          var allList = sortByLabel(productsByVenue[vid] || coinsCache || []);
          var plist = filteredProducts(vid);
          if (sel) {
            sel.innerHTML = plist.length
              ? optionsHtmlForVenue(vid, plist)
              : '<option value="">(sin coincidencias)</option>';
          }
          if (meta) {
            meta.textContent =
              (searchByVenue[vid]
                ? plist.length + " / " + allList.length
                : String(allList.length)) + " productos";
          }
        });
        inp.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter") {
            ev.preventDefault();
            var vid = inp.getAttribute("data-venue");
            var add = box.querySelector('.sim-coin-add[data-venue="' + vid + '"]');
            if (add) add.click();
          }
        });
      });

      box.querySelectorAll(".sim-coin-select").forEach(function (sel) {
        sel.addEventListener("dblclick", function () {
          var vid = sel.getAttribute("data-venue");
          var add = box.querySelector('.sim-coin-add[data-venue="' + vid + '"]');
          if (add) add.click();
        });
      });

      box.querySelectorAll(".sim-coin-add").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var vid = btn.getAttribute("data-venue");
          var sel = box.querySelector('.sim-coin-select[data-venue="' + vid + '"]');
          var cid = sel && sel.value;
          if (!cid) return;
          if (!selectedByVenue[vid]) selectedByVenue[vid] = [];
          if (selectedByVenue[vid].indexOf(cid) < 0) {
            selectedByVenue[vid].push(cid);
            maybeWarnMargin(vid, cid);
          }
          venueEnabled[vid] = true;
          renderVenuePicks();
          applyFeePreset();
        });
      });
      box.querySelectorAll(".sim-coin-rm").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var vid = btn.getAttribute("data-venue");
          var cid = btn.getAttribute("data-coin");
          selectedByVenue[vid] = (selectedByVenue[vid] || []).filter(function (x) {
            return x !== cid;
          });
          renderVenuePicks();
          applyFeePreset();
        });
      });
      box.querySelectorAll(".sim-venue-on").forEach(function (c) {
        c.addEventListener("change", function () {
          venueEnabled[c.value] = !!c.checked;
          renderVenuePicks();
          applyFeePreset();
        });
      });
    }

    function collectPairs() {
      var pairs = [];
      root.querySelectorAll(".sim-venue-on:checked").forEach(function (c) {
        var vid = c.value;
        (selectedByVenue[vid] || []).forEach(function (cid) {
          pairs.push({ venue: vid, underlying: cid });
        });
      });
      return pairs;
    }

    function periodDays() {
      return Number(root.querySelector("#sim-period").value) || 30;
    }

    function refreshNBars() {
      var iv = root.querySelector("#sim-interval").value;
      var days = periodDays();
      var el = root.querySelector("#sim-nbars");
      if (!QLApi.simPeriod) {
        el.textContent = "≈ —";
        return;
      }
      QLApi.simPeriod(days, iv)
        .then(function (d) {
          el.textContent = d.n_bars_display || "≈ " + d.n_bars + " velas";
          el.title =
            d.exceeds_lab_cap || d.heavy_run
              ? d.note ||
                "tope lab " + (d.lab_kline_limit_max || 525600)
              : "";
          el.style.color =
            d.exceeds_lab_cap
              ? "#d4544a"
              : d.heavy_run
                ? "#d48c32"
                : "";
        })
        .catch(function () {
          el.textContent = "≈ —";
        });
    }

    function capitalMode() {
      var free = root.querySelector("#sim-cap-free");
      return free && free.checked ? "unconstrained" : "fixed";
    }

    function syncCapitalModeUI() {
      var mode = capitalMode();
      var wrap = root.querySelector("#sim-capital-wrap");
      var help = root.querySelector("#sim-cap-help");
      var cap = root.querySelector("#sim-capital");
      if (wrap) wrap.style.opacity = mode === "fixed" ? "1" : "0.45";
      if (cap) {
        cap.disabled = mode !== "fixed";
      }
      if (help) {
        help.textContent =
          mode === "fixed"
            ? "Capital fijo + margen por trade. El resumen muestra margen pico y si te faltó plata (shortfall)."
            : "Sin monto: no hay tope de caja. El resumen marca margen/trade y margen pico = capital mínimo sugerido.";
      }
      refreshSizing();
    }

    function refreshSizing() {
      var hint = root.querySelector("#sim-size-hint");
      if (!QLApi.simSizing) return;
      QLApi.simSizing({
        capital_mode: capitalMode(),
        initial_capital: root.querySelector("#sim-capital").value,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        leverage: root.querySelector("#sim-lev").value,
        market_type: root.querySelector("#sim-market").value,
      })
        .then(function (d) {
          if (d.ok) {
            hint.textContent =
              "margen/trade " + d.margin + " · notional " + d.notional + " ✓";
            hint.style.color = "";
          } else {
            hint.textContent = (d.errors || []).join("; ") || "inválido";
            hint.style.color = "#d4544a";
          }
        })
        .catch(function (e) {
          hint.textContent = e.message || "error";
        });
    }

    function loadFees() {
      if (!QLApi.simFees) return;
      QLApi.simFees().then(function (d) {
        feeSchedules = d.schedules || [];
        applyFeePreset();
      });
    }

    function primaryVenue() {
      var checked = root.querySelector(".sim-venue-on:checked");
      return checked ? checked.value : "binance";
    }

    function updateFeeModeLabel() {
      var el = root.querySelector("#sim-fee-mode");
      if (!el) return;
      el.textContent = feesManualOverride
        ? "modo: editado a mano (mismo bps en todos)"
        : "modo: por mercado (schedule VIP0 de cada exchange)";
      el.style.color = feesManualOverride ? "var(--amber)" : "";
    }

    function applyFeePreset(force) {
      var venue = primaryVenue();
      var mt = root.querySelector("#sim-market").value;
      var hit = feeSchedules.find(function (s) {
        return s.venue === venue && s.market_type === mt;
      });
      var presetEl = root.querySelector("#sim-fee-preset");
      var linkEl = root.querySelector("#sim-fee-source");
      if (hit) {
        presetEl.textContent =
          venue +
          "/" +
          mt +
          " maker=" +
          hit.maker_bps +
          " taker=" +
          hit.taker_bps +
          (hit.notes ? " · " + hit.notes : "");
        if (force || !feesManualOverride) {
          root.querySelector("#sim-maker").value = hit.maker_bps;
          root.querySelector("#sim-taker").value = hit.taker_bps;
        }
        if (linkEl) {
          if (hit.source_url) {
            linkEl.href = hit.source_url;
            linkEl.hidden = false;
            linkEl.textContent = "Ver tarifas oficiales (" + venue + ")";
          } else {
            linkEl.hidden = true;
          }
        }
      } else {
        presetEl.textContent = "sin schedule para " + venue + "/" + mt;
        if (linkEl) linkEl.hidden = true;
      }
      updateFeeModeLabel();
    }

    function resetFeesFromMarket() {
      feesManualOverride = false;
      applyFeePreset(true);
    }

    function markFeesManual() {
      feesManualOverride = true;
      updateFeeModeLabel();
    }

    function loadUniverse() {
      var box = root.querySelector("#sim-venue-picks");
      var mt = root.querySelector("#sim-market").value || "futures";
      if (!QLApi.simUniverse) {
        coinsCache = [
          { id: "BTC", name: "Bitcoin", label: "Bitcoin (BTC)" },
          { id: "ETH", name: "Ethereum", label: "Ethereum (ETH)" },
        ];
        productsByVenue = { binance: coinsCache };
        renderVenuePicks();
        return;
      }
      box.textContent = "cargando productos…";
      QLApi.simUniverse({ market_type: mt, hl_live: true })
        .then(function (d) {
          coinsCache = sortByLabel(d.coins || []);
          venueMeta = d.venues || [];
          productsByVenue = d.products_by_venue || {};
          VENUES.forEach(function (vid) {
            if (!productsByVenue[vid] || !productsByVenue[vid].length) {
              if (vid === "a3" && mt === "spot") {
                productsByVenue[vid] = [];
              } else if (vid !== "a3") {
                productsByVenue[vid] = (coinsCache || []).map(function (c) {
                  return {
                    id: c.id,
                    name: c.name,
                    label: c.label,
                    expiry_label: mt === "spot" ? "spot" : "perpetuo",
                    contract_kind: mt === "spot" ? "spot" : "perpetual",
                    has_daily_variation: false,
                  };
                });
              }
            }
            productsByVenue[vid] = sortByLabel(productsByVenue[vid] || []);
          });
          var hlN = (productsByVenue.hyperliquid || []).length;
          var notes = (d.notes || []).join(" · ");
          if (hlN > 30) {
            box.title = notes || "HL live OK";
          } else if (mt === "futures") {
            box.title =
              "HL trajo pocos productos (" +
              hlN +
              "). ¿Modo Futuros + workbench reiniciado? " +
              notes;
          }
          renderVenuePicks();
          applyFeePreset();
        })
        .catch(function (e) {
          box.textContent = e.message || "error cargando productos";
        });
    }

    function findStrategy(id) {
      return strategiesCache.find(function (s) {
        return (s.id || s.strategy_id) === id;
      });
    }

    function renderGuideHtml(s) {
      var g = s.how_it_works || {};
      var steps = (g.steps || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      var params = (g.params_explained || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      var risks = (g.risks || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      var notes = (g.lab_notes || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      return (
        '<p class="sim-guide-plain"><strong>En simple</strong><br>' +
        esc(g.in_plain_words || g.idea || s.description || "—") +
        "</p>" +
        '<p class="sim-guide-example"><strong>Ejemplo</strong><br>' +
        esc(g.example || "—") +
        "</p>" +
        "<p><strong>Runnable:</strong> " +
        (s.runnable === false ? "no (stub research)" : "sí") +
        (g.runnable_note ? " — " + esc(g.runnable_note) : "") +
        "</p>" +
        "<p><strong>Familia:</strong> " +
        esc(s.family_label_es || s.family || "—") +
        " · <span class=\"muted\">id=" +
        esc(s.id) +
        "</span></p>" +
        "<p><strong>Cuándo compra</strong></p><p>" +
        esc(g.when_buy || "—") +
        "</p>" +
        "<p><strong>Cuándo vende / queda en efectivo</strong></p><p>" +
        esc(g.when_sell || "—") +
        "</p>" +
        "<p><strong>Paso a paso</strong></p><ol style=\"margin:0 0 0.75rem 1.1rem;padding:0\">" +
        steps +
        "</ol>" +
        "<p><strong>Parámetros</strong></p><ul style=\"margin:0 0 0.75rem 1.1rem;padding:0\">" +
        params +
        "</ul>" +
        "<p><strong>Riesgos / límites</strong></p><ul style=\"margin:0 0 0.75rem 1.1rem;padding:0\">" +
        risks +
        "</ul>" +
        "<p><strong>Notas del lab</strong></p><ul style=\"margin:0 0 0.5rem 1.1rem;padding:0\">" +
        notes +
        "</ul>"
      );
    }

    function openStrategyGuide(id) {
      var s = findStrategy(id);
      if (!s) {
        window.alert("Estrategia no cargada todavía. Esperá un segundo y reintentá.");
        return;
      }
      guideStrategyId = id;
      var title =
        "Estrategia: " + (s.name || id) + (s.runnable === false ? " [stub]" : "");
      var pane = document.createElement("div");
      pane.className = "pane-sim-strat-guide";
      pane.innerHTML =
        '<div class="sim-guide-body mono">' +
        renderGuideHtml(s) +
        "</div>" +
        '<div class="pane-row" style="margin-top:0.75rem;gap:0.4rem;flex-wrap:wrap">' +
        '<button type="button" class="btn" id="sim-guide-use">Usar en Comparar</button>' +
        '<button type="button" class="btn secondary" id="sim-guide-close">Cerrar</button>' +
        '<span class="muted" style="font-size:0.75em">Ventana del escritorio: arrastrá el título, redimensioná bordes, × para cerrar.</span>' +
        "</div>";

      var wm = global.QLShell && global.QLShell.wm;
      if (wm && typeof wm.open === "function") {
        if (wm.windows && wm.windows.has(STRAT_GUIDE_WIN)) {
          wm.close(STRAT_GUIDE_WIN);
        }
        wm.open(STRAT_GUIDE_WIN, title, pane, {
          x: 72,
          y: 48,
          w: 540,
          h: 520,
        });
      } else {
        // Fallback sin shell: panel flotante mínimo (sin overlay a pantalla completa)
        var old = document.getElementById("sim-strat-fallback");
        if (old) old.remove();
        var wrap = document.createElement("div");
        wrap.id = "sim-strat-fallback";
        wrap.className = "sim-guide-fallback";
        wrap.appendChild(pane);
        document.body.appendChild(wrap);
      }

      var useBtn = pane.querySelector("#sim-guide-use");
      var closeBtn = pane.querySelector("#sim-guide-close");
      if (useBtn) {
        useBtn.addEventListener("click", function () {
          if (guideStrategyId) {
            root.querySelector("#sim-strat-hist").value = guideStrategyId;
          }
          closeStrategyGuide();
          showTab("comparar");
        });
      }
      if (closeBtn) {
        closeBtn.addEventListener("click", closeStrategyGuide);
      }
    }

    function closeStrategyGuide() {
      var wm = global.QLShell && global.QLShell.wm;
      if (wm && wm.windows && wm.windows.has(STRAT_GUIDE_WIN)) {
        wm.close(STRAT_GUIDE_WIN);
      }
      var fb = document.getElementById("sim-strat-fallback");
      if (fb) fb.remove();
      guideStrategyId = null;
    }

    function loadStrategies() {
      QLApi.labStrategies()
        .then(function (d) {
          strategiesCache = d.strategies || d.items || [];
          familyLabels = d.family_labels_es || {};
          var byFamSelect = {};
          strategiesCache.forEach(function (s) {
            var f = s.family || "other";
            if (!byFamSelect[f]) byFamSelect[f] = [];
            byFamSelect[f].push(s);
          });
          var selFamKeys = FAMILY_ORDER.filter(function (f) {
            return byFamSelect[f];
          }).concat(
            Object.keys(byFamSelect)
              .filter(function (f) {
                return FAMILY_ORDER.indexOf(f) < 0;
              })
              .sort()
          );
          var opts = selFamKeys
            .map(function (fam) {
              var label = familyLabels[fam] || fam;
              var inner = (byFamSelect[fam] || [])
                .slice()
                .sort(function (a, b) {
                  var ka = alphaKey(a.name || a.id || a.strategy_id || "");
                  var kb = alphaKey(b.name || b.id || b.strategy_id || "");
                  if (ka < kb) return -1;
                  if (ka > kb) return 1;
                  return 0;
                })
                .map(function (s) {
                  var id = s.id || s.strategy_id;
                  var lab =
                    (s.name || id) + (s.runnable === false ? " [stub]" : "");
                  return (
                    "<option value=\"" + esc(id) + "\">" + esc(lab) + "</option>"
                  );
                })
                .join("");
              return (
                "<optgroup label=\"" + esc(label) + "\">" + inner + "</optgroup>"
              );
            })
            .join("");
          root.querySelector("#sim-strat-hist").innerHTML = opts;

          var byFam = byFamSelect;
          var famKeys = selFamKeys;

          var html = famKeys
            .map(function (fam, idx) {
              var label = familyLabels[fam] || fam;
              var items = (byFam[fam] || []).slice().sort(function (a, b) {
                var ka = alphaKey(a.name || a.id || a.strategy_id || "");
                var kb = alphaKey(b.name || b.id || b.strategy_id || "");
                if (ka < kb) return -1;
                if (ka > kb) return 1;
                return 0;
              });
              var open = idx === 0 ? " open" : "";
              var rows = items
                .map(function (s) {
                  var id = s.id || s.strategy_id;
                  var runnable = s.runnable !== false;
                  return (
                    '<div class="sim-strat-row">' +
                    "<div>" +
                    "<strong>" +
                    esc(s.name || id) +
                    "</strong> " +
                    '<span class="muted mono">' +
                    esc(id) +
                    "</span>" +
                    (runnable
                      ? ""
                      : ' <span class="data-badge data-badge-synth">stub</span>') +
                    "<br><span class=\"muted\">" +
                    esc(s.description || "") +
                    "</span></div>" +
                    '<div class="sim-strat-actions">' +
                    '<button type="button" class="btn secondary sim-strat-detail" data-id="' +
                    esc(id) +
                    '">Cómo opera</button> ' +
                    '<button type="button" class="btn sim-use-strat" data-id="' +
                    esc(id) +
                    '"' +
                    (runnable ? "" : " disabled") +
                    ">Usar</button>" +
                    "</div></div>"
                  );
                })
                .join("");
              return (
                '<details class="sim-strat-group"' +
                open +
                ">" +
                "<summary>" +
                esc(label) +
                " <span class=\"muted\">(" +
                items.length +
                ")</span></summary>" +
                '<div class="sim-strat-group-body">' +
                rows +
                "</div></details>"
              );
            })
            .join("");
          root.querySelector("#sim-strat-list").innerHTML =
            html || "sin estrategias";

          root.querySelectorAll(".sim-use-strat").forEach(function (btn) {
            btn.addEventListener("click", function () {
              var id = btn.getAttribute("data-id");
              root.querySelector("#sim-strat-hist").value = id;
              showTab("comparar");
            });
          });
          root.querySelectorAll(".sim-strat-detail").forEach(function (btn) {
            btn.addEventListener("click", function () {
              openStrategyGuide(btn.getAttribute("data-id"));
            });
          });
        })
        .catch(function (e) {
          root.querySelector("#sim-strat-list").textContent =
            e.message || "error";
        });
    }

    function collectExtraCosts() {
      return extraCosts.slice();
    }

    function renderExtraCosts() {
      var box = root.querySelector("#sim-extra-costs");
      if (!extraCosts.length) {
        box.textContent = "sin gastos extra";
        return;
      }
      box.innerHTML = extraCosts
        .map(function (c, i) {
          return (
            esc(c.name) +
            " " +
            esc(c.kind) +
            "=" +
            esc(c.amount) +
            ' <button type="button" data-i="' +
            i +
            '" class="sim-rm-cost">×</button>'
          );
        })
        .join(" · ");
      box.querySelectorAll(".sim-rm-cost").forEach(function (b) {
        b.addEventListener("click", function () {
          extraCosts.splice(Number(b.getAttribute("data-i")), 1);
          renderExtraCosts();
        });
      });
    }

    function leverages() {
      if (root.querySelector("#sim-multi-x").checked) {
        return [1, 2, 5, 10];
      }
      return [Number(root.querySelector("#sim-lev").value) || 1];
    }

    function runCompare(strategyId) {
      var pairs = collectPairs();
      var mode = capitalMode();
      var payload = {
        pairs: pairs,
        market_type: root.querySelector("#sim-market").value,
        leverages: leverages(),
        strategy_id: strategyId,
        interval: root.querySelector("#sim-interval").value,
        period_days: periodDays(),
        capital_mode: mode,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        simulate_liquidation: root.querySelector("#sim-liq").checked,
        apply_funding: root.querySelector("#sim-funding").checked,
        annual_bench_rate: Number(root.querySelector("#sim-bench").value || 0) / 100,
        extra_costs: collectExtraCosts(),
      };
      if (mode === "fixed") {
        payload.initial_capital = root.querySelector("#sim-capital").value;
      }
      // Solo override manual: si no, cada venue usa su schedule VIP0 real
      if (feesManualOverride) {
        var mk = root.querySelector("#sim-maker").value;
        var tk = root.querySelector("#sim-taker").value;
        if (mk !== "") payload.maker_bps = mk;
        if (tk !== "") payload.taker_bps = tk;
      }
      return QLApi.simCompare(payload);
    }

    var SUMMARY_TIPS = {
      venue:
        "Mercado / exchange donde se simula la operación.\n" +
        "Ejemplos: Binance, OKX, Bybit, Hyperliquid.\n" +
        "Cada fila es un par exchange × moneda × apalancamiento.\n" +
        "Usa velas históricas públicas; no manda órdenes reales.\n" +
        "LIVE sigue bloqueado en QuantLab.",
      modo:
        "Tipo de mercado simulado: Spot o Futuros.\n" +
        "Spot = comprás/vendés el activo al contado.\n" +
        "Futuros = contrato con apalancamiento y margen.\n" +
        "Cambia fees, sizing y si hay funding/liquidación.\n" +
        "Elegilo arriba en «Modo» antes de correr.",
      sym:
        "Moneda o activo simulado (ej. BTC, ETH).\n" +
        "Es el «underlying» del par en ese exchange.\n" +
        "Lo elegís en el menú Nombre (TICKER) de cada mercado.\n" +
        "Misma estrategia puede dar distinto resultado por liquidez/fees.\n" +
        "No implica recomendación de compra.",
      x:
        "Apalancamiento (leverage) aplicado al overlay.\n" +
        "1x = sin apalancar; 10x multiplica la exposición.\n" +
        "Más x sube ganancia potencial y también el riesgo.\n" +
        "En futuros altos puede disparar liquidación simulada.\n" +
        "Usá multi-x para comparar varias x juntas.",
      inicial:
        "Capital con el que arranca (solo modo Monto fijo).\n" +
        "En Sin monto aparece «sin tope».\n" +
        "Es la caja de partida del backtest / base del PnL %.\n" +
        "No confundir con el margen pico (columna aparte).\n" +
        "No es dinero real depositado en un exchange.",
      "margen-trade":
        "Margen configurado por operación (campo «Por trade»).\n" +
        "En futuros: notional = margen × leverage.\n" +
        "Es el tamaño de riesgo que elegiste, no el pico real.\n" +
        "Siempre se muestra aparte del capital inicial.\n" +
        "Si el pico supera este valor, hubo más de un lote abierto.",
      "margen-pico":
        "Máximo margen estimado durante la corrida (fills).\n" +
        "Se calcula con la posición neta × precio / leverage.\n" +
        "En Sin monto = capital mínimo sugerido para esa estrategia.\n" +
        "Comparalo con tu capital fijo para ver si alcanzaba.\n" +
        "Aprox. de research; no es el motor de margen del exchange.",
      faltante:
        "¿Te faltó plata?\n" +
        "En Monto fijo: shortfall = margen pico − capital (si pico > capital).\n" +
        "«sí» en rojo = necesitabas más capital del que pusiste.\n" +
        "En Sin monto: muestra el capital requerido (= margen pico).\n" +
        "Sirve para dimensionar la cuenta antes de arriesgar de verdad.",
      final:
        "Capital al cerrar el período simulado.\n" +
        "Incluye resultados de trades, fees y (si aplica) funding.\n" +
        "Con leverage refleja el overlay de esa x.\n" +
        "Comparalo con el inicial: subió o bajó la caja.\n" +
        "Si hubo liquidación, puede quedar muy por debajo.",
      ops:
        "Número de operaciones ejecutadas (fills).\n" +
        "Cada fill es una compra/venta que tocó el precio histórico.\n" +
        "Cero fills = la estrategia no entró o solo puso límites sin fill.\n" +
        "Más ops suele implicar más fees acumulados.\n" +
        "No cuenta órdenes que nunca se llenaron.",
      fees:
        "Suma de comisiones cobradas en la simulación.\n" +
        "Por defecto usa el schedule VIP0 de cada exchange.\n" +
        "Solo si editás maker/taker a mano se fuerza ese bps en todos.\n" +
        "«Fees del mercado» vuelve al schedule real.\n" +
        "Restan del capital final.",
      "dif-bench":
        "Diferencia vs el banco (tasa pasiva del período).\n" +
        "Se calcula: PnL de la estrategia − retorno del bench.\n" +
        "Positivo = la estrategia rindió más que dejar plata a esa tasa.\n" +
        "Negativo = el bench hubiera sido mejor en ese tramo.\n" +
        "El % anual del bench lo seteás arriba (ej. 5%).",
      liq:
        "¿Se simuló una liquidación en futuros?\n" +
        "«sí» = el margen no alcanzó y se cortó la posición.\n" +
        "Pasa más con leverage alto y movimientos fuertes.\n" +
        "En spot no aplica liquidación típica de futuros.\n" +
        "Activá/desactivá «simular liquidación» en controles.",
    };

    function tipAttr(key) {
      return ' data-tip="' + esc(SUMMARY_TIPS[key] || "") + '"';
    }

    function numOrNull(v) {
      if (v == null || v === "") return null;
      var n = Number(v);
      return isFinite(n) ? n : null;
    }

    function fmtMoney(v) {
      if (v == null || v === "") return "—";
      var n = Number(v);
      if (!isFinite(n)) return esc(v);
      return esc(n.toLocaleString("es-AR", { maximumFractionDigits: 4 }));
    }

    function formatRows(data) {
      var rows = data.rows || [];
      if (!rows.length) return "sin filas";
      return (
        '<p class="muted" style="font-size:0.75em;margin:0.2rem 0 0.35rem">' +
        "Resumen — pasá el mouse sobre cada título de columna para ver qué significa." +
        "</p>" +
        '<table class="sim-summary-table mono"><thead><tr>' +
        "<th" +
        tipAttr("venue") +
        ">Mercado</th>" +
        "<th" +
        tipAttr("modo") +
        ">Modo</th>" +
        "<th" +
        tipAttr("sym") +
        ">Moneda</th>" +
        "<th" +
        tipAttr("x") +
        ">x</th>" +
        "<th" +
        tipAttr("inicial") +
        ">Capital inicial</th>" +
        "<th" +
        tipAttr("margen-trade") +
        ">Margen/trade</th>" +
        "<th" +
        tipAttr("margen-pico") +
        ">Margen pico</th>" +
        "<th" +
        tipAttr("faltante") +
        ">¿Faltó?</th>" +
        "<th" +
        tipAttr("final") +
        ">Capital final</th>" +
        "<th" +
        tipAttr("ops") +
        ">Nº operaciones</th>" +
        "<th" +
        tipAttr("fees") +
        ">Fees gastados</th>" +
        "<th" +
        tipAttr("dif-bench") +
        ">Dif. vs bench</th>" +
        "<th" +
        tipAttr("liq") +
        ">Liq.</th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (r) {
            var o = r.overlay || {};
            var bt = r.backtest || {};
            var mr = bt.margin_report || {};
            var b = bt.benchmark || r.benchmark || {};
            var mode =
              bt.capital_mode ||
              (data.common && data.common.capital_mode) ||
              "fixed";
            var initialDisp =
              mode === "unconstrained"
                ? "sin tope"
                : bt.display_initial_capital != null
                  ? bt.display_initial_capital
                  : o.initial_equity != null
                    ? o.initial_equity
                    : bt.initial_equity;
            var finalEq = o.final_equity != null ? o.final_equity : bt.final_equity;
            var nOps = bt.n_fills != null ? bt.n_fills : bt.n_orders;
            var fees = bt.total_fees;
            var pnlN = numOrNull(o.pnl);
            var benchN = numOrNull(b.period_return);
            var dif =
              pnlN != null && benchN != null
                ? pnlN - benchN
                : null;
            var difTxt =
              dif == null
                ? r.error
                  ? esc(r.error)
                  : "—"
                : (dif > 0 ? "+" : "") +
                  dif.toLocaleString("es-AR", { maximumFractionDigits: 4 });
            var shortN = numOrNull(mr.capital_shortfall);
            var needMore = mr.needed_more_money === true;
            var faltTxt;
            if (!r.ok && r.error) {
              faltTxt = "—";
            } else if (mode === "unconstrained") {
              faltTxt = "req " + fmtMoney(mr.capital_required || mr.peak_margin);
            } else if (needMore) {
              faltTxt =
                '<span style="color:#d4544a">sí +' +
                fmtMoney(shortN) +
                "</span>";
            } else {
              faltTxt = '<span style="color:#3d9a6a">no</span>';
            }
            return (
              "<tr><td" +
              tipAttr("venue") +
              ">" +
              esc(r.venue) +
              "</td><td" +
              tipAttr("modo") +
              ">" +
              esc(r.market_type) +
              "</td><td" +
              tipAttr("sym") +
              ">" +
              esc(r.underlying || r.instrument_id) +
              "</td><td" +
              tipAttr("x") +
              ">" +
              esc(r.leverage) +
              "</td><td" +
              tipAttr("inicial") +
              ">" +
              (mode === "unconstrained"
                ? esc(initialDisp)
                : fmtMoney(initialDisp)) +
              "</td><td" +
              tipAttr("margen-trade") +
              ">" +
              fmtMoney(mr.margin_per_trade) +
              "</td><td" +
              tipAttr("margen-pico") +
              ">" +
              fmtMoney(mr.peak_margin) +
              "</td><td" +
              tipAttr("faltante") +
              ">" +
              faltTxt +
              "</td><td" +
              tipAttr("final") +
              ">" +
              fmtMoney(finalEq) +
              "</td><td" +
              tipAttr("ops") +
              ">" +
              esc(nOps != null ? nOps : "—") +
              "</td><td" +
              tipAttr("fees") +
              ">" +
              fmtMoney(fees) +
              "</td><td" +
              tipAttr("dif-bench") +
              ">" +
              difTxt +
              "</td><td" +
              tipAttr("liq") +
              ">" +
              (o.liquidated ? "sí" : r.ok === false ? "—" : "no") +
              "</td></tr>"
            );
          })
          .join("") +
        "</tbody></table>"
      );
    }

    function syncLeverage(from) {
      var range = root.querySelector("#sim-lev");
      var num = root.querySelector("#sim-lev-num");
      var v = from === "num" ? Number(num.value) : Number(range.value);
      if (!isFinite(v) || v < 1) v = 1;
      if (v > 125) v = 125;
      v = Math.round(v);
      range.value = String(v);
      num.value = String(v);
      refreshSizing();
    }

    root.querySelectorAll(".sim-tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        showTab(btn.getAttribute("data-tab"));
      });
    });
    root.querySelector("#sim-lev").addEventListener("input", function () {
      syncLeverage("range");
    });
    root.querySelector("#sim-lev-num").addEventListener("input", function () {
      syncLeverage("num");
    });
    root.querySelector("#sim-lev-num").addEventListener("change", function () {
      syncLeverage("num");
    });
    ["#sim-period", "#sim-interval"].forEach(function (sel) {
      root.querySelector(sel).addEventListener("change", refreshNBars);
    });
    ["#sim-cap-fixed", "#sim-cap-free"].forEach(function (sel) {
      var el = root.querySelector(sel);
      if (el) el.addEventListener("change", syncCapitalModeUI);
    });
    ["#sim-capital", "#sim-per-trade", "#sim-market"].forEach(function (sel) {
      root.querySelector(sel).addEventListener("change", function () {
        refreshSizing();
        if (sel === "#sim-market") {
          applyFeePreset(false);
          loadUniverse();
        }
      });
      root.querySelector(sel).addEventListener("input", refreshSizing);
    });
    root.querySelector("#sim-maker").addEventListener("input", markFeesManual);
    root.querySelector("#sim-taker").addEventListener("input", markFeesManual);
    root.querySelector("#sim-fee-reset").addEventListener("click", resetFeesFromMarket);
    root.querySelector("#sim-add-cost").addEventListener("click", function () {
      var name = window.prompt("Nombre del gasto", "retiro");
      if (!name) return;
      var kind = window.prompt("Tipo: fixed_usd o percent_notional", "fixed_usd");
      var amount = window.prompt("Monto", "1");
      if (!kind || amount == null) return;
      extraCosts.push({ name: name, kind: kind, amount: amount });
      renderExtraCosts();
    });
    root.querySelector("#sim-run-hist").addEventListener("click", function () {
      var out = root.querySelector("#sim-out-hist");
      var pairs = collectPairs();
      if (!pairs.length) {
        out.textContent =
          "Elegí al menos un exchange activo y agregá una moneda (menú Nombre (TICKER)).";
        return;
      }
      out.textContent = "comparando " + pairs.length + " pares…";
      runCompare(root.querySelector("#sim-strat-hist").value)
        .then(function (d) {
          out.innerHTML =
            '<span class="data-badge data-badge-real">HISTÓRICO</span> ' +
            formatRows(d);
        })
        .catch(function (e) {
          out.textContent = e.message || String(e);
        });
    });
    root.querySelector("#sim-strat-info").addEventListener("click", function () {
      openStrategyGuide(root.querySelector("#sim-strat-hist").value);
    });
    root.querySelector("#sim-open-mc").addEventListener("click", function () {
      if (global.QLShell && QLShell.open) QLShell.open("montecarlo");
    });
    root.querySelector("#sim-open-gl").addEventListener("click", function () {
      if (global.QLShell && QLShell.open) QLShell.open("guided_lab");
    });
    root.querySelector("#sim-open-blotter").addEventListener("click", function () {
      if (global.QLShell && QLShell.open) QLShell.open("blotter");
    });

    root.refresh = function () {
      refreshNBars();
      syncCapitalModeUI();
      loadFees();
      loadUniverse();
      loadStrategies();
      renderExtraCosts();
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSimulatorPane = createSimulatorPane;
})(window);
