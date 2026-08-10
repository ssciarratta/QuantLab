/** Simulador multi-mercado — comparar venues × productos (guías en panel Estrategias). */
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
      '<div class="pane-section sim-pane">' +
      '<div class="sim-head">' +
      "<h3>Simulador</h3>" +
      '<p class="muted sim-sub">Comparar mercados × productos × leverage · LIVE bloqueado</p>' +
      "</div>" +
      '<details class="sim-more muted">' +
      "<summary>Ayuda · qué es vs Guided / Backtest</summary>" +
      '<p class="sim-tab-hint" style="margin:0.35rem 0 0">' +
      "<strong>Guided Lab</strong> = practicar. <strong>Backtest</strong> = velas sintéticas. " +
      "<strong>Simulador</strong> = Binance/OKX/Bybit/HL/A3 × productos × leverage. " +
      "Guías de estrategias → menú QL · <strong>Estrategias</strong>. A3 = margen + diferencias diarias." +
      "</p></details>" +
      '<div class="sim-common">' +
      '<div class="sim-toolbar">' +
      '<label>Modo<select id="sim-market">' +
      '<option value="spot">Spot</option><option value="futures" selected>Futuros</option></select></label>' +
      '<label class="sim-lev-lab">Leverage' +
      '<span class="sim-lev-row">' +
      '<input type="range" id="sim-lev" min="1" max="125" value="1">' +
      '<input type="number" id="sim-lev-num" min="1" max="125" step="1" value="1" ' +
      'data-tip="Apalancamiento. Deslizador o número (1–125). Spot ≈ 1x; futuros podés subir la x.">' +
      '<span class="muted">x</span></span></label>' +
      '<label class="sim-check"><input type="checkbox" id="sim-multi-x"> multi-x</label>' +
      '<label>Período<select id="sim-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label>Intervalo<select id="sim-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<label>Bench %<input type="number" id="sim-bench" value="5" min="0" step="0.1"></label>' +
      '<label class="sim-check"><input type="checkbox" id="sim-liq" checked> liq.</label>' +
      '<label class="sim-check"><input type="checkbox" id="sim-funding" checked> funding</label>' +
      '<span class="muted sim-nbars" id="sim-nbars">≈ —</span>' +
      "</div>" +
      '<div class="sim-toolbar sim-toolbar-cap">' +
      '<fieldset class="sim-capital-mode">' +
      "<legend>Capital</legend>" +
      '<label class="sim-check"><input type="radio" name="sim-cap-mode" id="sim-cap-fixed" value="fixed" checked> Fijo</label> ' +
      '<label class="sim-check"><input type="radio" name="sim-cap-mode" id="sim-cap-free" value="unconstrained"> Sin monto</label>' +
      '<label id="sim-capital-wrap">USDT <input type="number" id="sim-capital" value="10000" min="1"></label>' +
      '<label>Por trade <input type="number" id="sim-per-trade" value="500" min="1"></label>' +
      '<span class="mono muted" id="sim-size-hint">—</span>' +
      "</fieldset>" +
      "</div>" +
      '<details class="sim-more muted">' +
      "<summary>Fees · gastos · capital (detalle)</summary>" +
      '<p id="sim-cap-help" style="margin:0.3rem 0">' +
      "Siempre se calcula el margen pico. En fijo: ves si faltó plata. En sin monto: el pico es el mínimo sugerido." +
      "</p>" +
      '<div class="sim-toolbar sim-toolbar-fees">' +
      '<span class="muted">Fees</span> ' +
      '<span class="mono" id="sim-fee-preset" data-tip="Comisiones VIP0 del schedule del lab. Por defecto cada mercado usa las suyas.">—</span>' +
      ' <a id="sim-fee-source" class="sim-fee-link" href="#" target="_blank" rel="noopener noreferrer" hidden>Tarifas</a>' +
      '<label>maker <input id="sim-maker" type="number" step="0.1"></label>' +
      '<label>taker <input id="sim-taker" type="number" step="0.1"></label>' +
      '<button type="button" class="btn secondary" id="sim-fee-reset" data-tip="Vuelve al schedule del mercado.">Fees mercado</button>' +
      '<span class="mono muted" id="sim-fee-mode" style="font-size:1.04em">por mercado</span>' +
      '<button type="button" class="btn secondary" id="sim-add-cost">+ Gasto</button>' +
      "</div>" +
      '<div id="sim-extra-costs" class="mono muted" style="font-size:1.08em"></div>' +
      "</details>" +
      "</div>" +
      '<div class="sim-panel" data-panel="comparar">' +
      '<div class="sim-actions sim-step-first">' +
      '<label>Estrategia <select id="sim-strat-hist"></select></label>' +
      '<button type="button" class="btn secondary" id="sim-strat-info" data-tip="Detalle de la estrategia (panel Estrategias).">¿Cómo opera?</button>' +
      '<button type="button" class="btn" id="sim-run-hist">Correr y comparar</button>' +
      '<button type="button" class="btn secondary" id="sim-run-rank" hidden ' +
      'data-tip="Solo con UNA moneda agregada (chip) en mercados tildados. Corre el universo runnable (sin dummy/buy_once) y muestra top por PnL %.">' +
      "Mejores estrategias (1 moneda)</button>" +
      '<button type="button" class="btn secondary stop-run" id="sim-stop" hidden disabled ' +
      'title="Detener la corrida activa de este panel">Stop</button>' +
      '<button type="button" class="btn secondary" id="sim-open-strategies">Estrategias</button>' +
      '<span class="mono muted sim-run-status" id="sim-run-status">—</span>' +
      "</div>" +
      '<div class="mono" id="sim-out-hist">—</div>' +
      '<p class="muted sim-meta">Mercados y monedas · escribí para buscar · Agregar · al tildar otro mercado se copia la misma moneda</p>' +
      '<div id="sim-venue-picks" class="sim-venue-picks">cargando monedas…</div>' +
      '<div class="sim-actions sim-shortcuts">' +
      '<button type="button" class="btn secondary" id="sim-open-gl">Guided Lab</button>' +
      '<button type="button" class="btn" id="sim-open-mc" ' +
      'title="Estresa la selección actual (mercado + moneda + estrategia) en Monte Carlo">' +
      "Monte Carlo</button>" +
      '<button type="button" class="btn slt-launch-btn" id="sim-open-live-test" ' +
      'title="Abrir Corrida en vivo con mercado + moneda + estrategia actuales (no arranca solo)">' +
      "▶ Corrida en vivo</button>" +
      '<span class="muted mono" id="sim-mc-sel-hint">Elegí mercado + moneda</span>' +
      '<button type="button" class="btn secondary" id="sim-open-blotter">Paper Blotter</button>' +
      "</div>" +
      "</div>" +
      "</div>";

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
    /** Prefill desde Alpha Scanner (venue/underlying/strategy/TF). */
    var pendingPrefill = null;
    /** Último handoff hacia Monte Carlo / memos (moneda + params). */
    var lastSimHandoff = null;
    /** @type {Object.<string, boolean>} */
    var venueEnabled = {
      binance: false,
      okx: false,
      bybit: false,
      hyperliquid: false,
      a3: false,
    };
    /** Texto de búsqueda por venue (se conserva al re-render). */
    var searchByVenue = {};
    var STRAT_GUIDE_WIN = "sim_strategy_guide";

    function showTab(_name) {
      /* Guías viven en panel Estrategias — no hay solapas acá. */
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
            selectedByVenue[vid] = [];
          }
          if (venueEnabled[vid] == null) {
            venueEnabled[vid] = false;
          }
          var checked = !!venueEnabled[vid];
          var qTrim = String(q || "").trim();
          var listOpen = checked && qTrim.length > 0;
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
              ? "Escribí: petróleo, oro, GOLD…"
              : vid === "a3"
                ? "Escribí: soja, maíz, trigo…"
                : "Escribí moneda o símbolo (apt, BTC…)";
          var countTxt = !checked
            ? "tildá el mercado para buscar"
            : !listOpen
              ? "escribí para buscar · catálogo " + allList.length
              : plist.length + " / " + allList.length + " coincidencias";
          var kindHint = "";
          if (vid === "hyperliquid" && allList.length && listOpen) {
            var kinds = {};
            plist.forEach(function (p) {
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
            ' autocomplete="off">' +
            '<select class="sim-coin-select" data-venue="' +
            esc(vid) +
            '" size="6"' +
            (checked ? "" : " disabled") +
            (listOpen ? "" : " hidden") +
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
            (checked && listOpen ? "" : " disabled") +
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
          var addBtn = box.querySelector('.sim-coin-add[data-venue="' + vid + '"]');
          var allList = sortByLabel(productsByVenue[vid] || coinsCache || []);
          var qTrim = String(searchByVenue[vid] || "").trim();
          var plist = filteredProducts(vid);
          if (sel) {
            if (!qTrim) {
              sel.hidden = true;
              sel.innerHTML = "";
            } else {
              sel.hidden = false;
              sel.innerHTML = plist.length
                ? optionsHtmlForVenue(vid, plist)
                : '<option value="">(sin coincidencias)</option>';
            }
          }
          if (addBtn) addBtn.disabled = !qTrim;
          if (meta) {
            meta.textContent = !qTrim
              ? "escribí para buscar · catálogo " + allList.length
              : plist.length + " / " + allList.length + " coincidencias";
          }
          syncMcSelHint();
        });
        inp.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter") {
            ev.preventDefault();
            var vid = inp.getAttribute("data-venue");
            var add = box.querySelector('.sim-coin-add[data-venue="' + vid + '"]');
            if (add && !add.disabled) add.click();
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
          addProductToVenue(vid, cid, true);
          autoAddSameTickerToChecked(vid, cid);
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
          if (c.checked) {
            // Al tildar un mercado, copiá las monedas ya elegidas en otros
            Object.keys(selectedByVenue).forEach(function (srcVid) {
              (selectedByVenue[srcVid] || []).forEach(function (cid) {
                autoAddSameTickerToChecked(srcVid, cid);
              });
            });
          }
          renderVenuePicks();
          applyFeePreset();
        });
      });
      syncRankButton();
      syncMcSelHint();
    }

    function syncMcSelHint() {
      var hint = root.querySelector("#sim-mc-sel-hint");
      var btn = root.querySelector("#sim-open-mc");
      var pairs = collectPairs();
      var label =
        pairs.length > 0
          ? pairs
              .map(function (p) {
                return (p.venue || "?") + "/" + (p.underlying || "?");
              })
              .join(", ")
          : "";
      if (hint) {
        hint.textContent = label
          ? "→ " + label
          : "Elegí mercado + moneda";
      }
      if (btn) {
        btn.disabled = pairs.length === 0;
        btn.title = label
          ? "Monte Carlo ligado a: " + label
          : "Elegí al menos un mercado y una moneda";
      }
    }

    function freezeHandoffCapital(handoff, common) {
      if (!handoff || !common || typeof common !== "object") return handoff;
      if (common.capital_mode) handoff.capital_mode = common.capital_mode;
      if (common.initial_capital != null && common.initial_capital !== "") {
        handoff.initial_capital = String(common.initial_capital);
      }
      if (common.per_trade_usd != null && common.per_trade_usd !== "") {
        handoff.per_trade_usd = String(common.per_trade_usd);
      }
      if (common.run_cash != null && common.run_cash !== "") {
        handoff.run_cash = String(common.run_cash);
      }
      lastSimHandoff = handoff;
      return handoff;
    }

    function openMonteCarloFromSelection() {
      var prep = preparePairsForRun();
      var sid =
        (root.querySelector("#sim-strat-hist") &&
          root.querySelector("#sim-strat-hist").value) ||
        "";
      // Preferir snapshot de la ultima Comparar/Ranking (capital / por trade),
      // no el formulario actual (puede haber vuelto al default 10000).
      var handoff = null;
      if (lastSimHandoff && lastSimHandoff.pairs && lastSimHandoff.pairs.length) {
        try {
          handoff = JSON.parse(JSON.stringify(lastSimHandoff));
        } catch (e) {
          handoff = lastSimHandoff;
        }
      }
      if (!handoff || !handoff.pairs || !handoff.pairs.length) {
        handoff = buildSimHandoff("compare", prep.pairs, {
          strategy_id: sid,
        });
      } else if (sid && !handoff.strategy_id) {
        handoff.strategy_id = sid;
      }
      if (!handoff.pairs || !handoff.pairs.length) {
        window.alert(
          "Elegí al menos un mercado y una moneda en el Simulador antes de abrir Monte Carlo.\n" +
            "Así el estrés queda ligado a esa selección (no «al aire»)."
        );
        return;
      }
            // Prefill: horizonte ~ periodo Comparar (tope 5000) + ruido estres 50 bps.
      // Fidelidad de motor (estrategia/caja/L/funding); NO calibra el % historico.
      var MC_MAX_BARS = 5000;
      var nbarsHint = 60;
      var pd = Number(handoff.period_days);
      var iv = String(handoff.interval || "1h");
      if (isFinite(pd) && pd > 0) {
        var mins = 60;
        if (/^\d+m$/i.test(iv)) mins = parseInt(iv, 10);
        else if (/^\d+h$/i.test(iv)) mins = parseInt(iv, 10) * 60;
        else if (/^\d+d$/i.test(iv)) mins = parseInt(iv, 10) * 1440;
        var est = Math.ceil((pd * 24 * 60) / mins);
        if (isFinite(est) && est > 0) nbarsHint = Math.max(60, Math.min(MC_MAX_BARS, est));
      } else {
        nbarsHint = MC_MAX_BARS;
      }
      if (global.QLShell && QLShell.open) {
        QLShell.open("montecarlo", {
          prefill: {
            sim_context: handoff,
            n_bars: nbarsHint,
            noise_bps: 50,
            message:
              "Estres ligado a: " +
              (handoff.summary_line || handoff.coin || "simulacion") +
              " · velas/esc≈" +
              nbarsHint +
              " · ruido 50 bps · mismo leverage/funding que Comparar (no calibra PnL)",
          },
        });
      }
    }

    function executionSymbolFromHandoff(handoff) {
      var p0 = handoff.pairs && handoff.pairs[0];
      var raw = (p0 && (p0.ticker || p0.underlying)) || handoff.coin || "BTC";
      raw = String(raw).split(",")[0].trim().toUpperCase();
      var aliases = { UNISWAP: "UNI", BITCOIN: "BTC", ETHEREUM: "ETH", WBTC: "BTC" };
      if (raw.indexOf("USDT") < 0) {
        var base = raw.replace(/USDT$/i, "");
        if (aliases[base]) base = aliases[base];
        return base + "USDT";
      }
      var base2 = raw.replace(/USDT$/i, "");
      if (aliases[base2]) return aliases[base2] + "USDT";
      return raw;
    }

    function openLiveTestFromSelection() {
      var prep = preparePairsForRun();
      var sid =
        (root.querySelector("#sim-strat-hist") &&
          root.querySelector("#sim-strat-hist").value) ||
        "";
      var handoff = null;
      if (lastSimHandoff && lastSimHandoff.pairs && lastSimHandoff.pairs.length) {
        try {
          handoff = JSON.parse(JSON.stringify(lastSimHandoff));
        } catch (e) {
          handoff = lastSimHandoff;
        }
      }
      if (!handoff || !handoff.pairs || !handoff.pairs.length) {
        handoff = buildSimHandoff("compare", prep.pairs, {
          strategy_id: sid,
        });
      } else if (sid && !handoff.strategy_id) {
        handoff.strategy_id = sid;
      }
      if (!handoff.pairs || !handoff.pairs.length) {
        window.alert(
          "Elegí al menos un mercado y una moneda antes de probar con datos reales."
        );
        return;
      }
      var sym = executionSymbolFromHandoff(handoff);
      var sidFinal = handoff.strategy_id || sid || "buy_once";
      var stratMeta = findStrategy(sidFinal);
      if (global.QLShell && QLShell.open) {
        QLShell.open("strategy_live_test", {
          prefill: {
            source_module: "simulator",
            sim_context: handoff,
            strategy_id: sidFinal,
            symbol: sym,
            execution_destination: "PAPER",
            market_type: handoff.market_type,
            interval: handoff.interval,
            venue: handoff.venues && handoff.venues[0],
            strategy_parameters: (stratMeta && stratMeta.default_params) || {},
            message: "Simulador · " + (handoff.summary_line || sym),
          },
        });
      }
    }

    function canonicalTicker(venue, id) {
      var p = productFor(venue, id);
      var raw = (p && (p.name || p.id)) || id || "";
      if (String(raw).indexOf(":") >= 0) {
        raw = String(raw).split(":").pop();
      }
      // A3 SOJ/MAY26 → SOJ
      if (String(raw).indexOf("/") >= 0) {
        raw = String(raw).split("/")[0];
      }
      return foldText(raw);
    }

    function findProductIdByTicker(venue, ticker) {
      var t = foldText(ticker);
      if (!t) return null;
      var list = productsByVenue[venue] || coinsCache || [];
      var i;
      for (i = 0; i < list.length; i++) {
        var p = list[i];
        var id = String(p.id || "");
        var name = String(p.name || "");
        var short = id.indexOf(":") >= 0 ? id.split(":").pop() : id;
        if (foldText(id) === t || foldText(name) === t || foldText(short) === t) {
          return id;
        }
      }
      return null;
    }

    function addProductToVenue(vid, cid, warn) {
      if (!cid) return false;
      if (!selectedByVenue[vid]) selectedByVenue[vid] = [];
      if (selectedByVenue[vid].indexOf(cid) >= 0) {
        venueEnabled[vid] = true;
        return false;
      }
      selectedByVenue[vid].push(cid);
      venueEnabled[vid] = true;
      if (warn) maybeWarnMargin(vid, cid);
      return true;
    }

    function autoAddSameTickerToChecked(sourceVenue, cid) {
      var ticker = canonicalTicker(sourceVenue, cid);
      if (!ticker) return;
      Object.keys(venueEnabled).forEach(function (vid) {
        if (vid === sourceVenue) return;
        if (!venueEnabled[vid]) return;
        // A3 no comparte tickers crypto; HL HIP-3 ↔ crypto sí por nombre corto
        if (vid === "a3" || sourceVenue === "a3") return;
        var match = findProductIdByTicker(vid, ticker);
        if (match) addProductToVenue(vid, match, false);
      });
    }

    /** Propaga chips de monedas a todos los mercados tildados (crypto↔crypto). */
    function syncCoinsToCheckedVenues() {
      var added = [];
      var sources = [];
      Object.keys(selectedByVenue).forEach(function (vid) {
        (selectedByVenue[vid] || []).forEach(function (cid) {
          sources.push({ venue: vid, cid: cid });
        });
      });
      sources.forEach(function (src) {
        if (src.venue === "a3") return;
        var ticker = canonicalTicker(src.venue, src.cid);
        if (!ticker) return;
        root.querySelectorAll(".sim-venue-on:checked").forEach(function (c) {
          var vid = c.value;
          if (vid === src.venue || vid === "a3") return;
          venueEnabled[vid] = true;
          var match = findProductIdByTicker(vid, ticker);
          if (!match) return;
          if (addProductToVenue(vid, match, false)) {
            added.push(vid);
          }
        });
      });
      return added;
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

    /** Antes de correr: sincroniza chips y reporta mercados tildados sin moneda. */
    function preparePairsForRun() {
      var added = syncCoinsToCheckedVenues();
      if (added.length) {
        renderVenuePicks();
        applyFeePreset();
      }
      var pairs = collectPairs();
      var checked = [];
      root.querySelectorAll(".sim-venue-on:checked").forEach(function (c) {
        checked.push(c.value);
      });
      var inPairs = {};
      pairs.forEach(function (p) {
        inPairs[p.venue] = true;
      });
      var skipped = checked.filter(function (v) {
        return !inPairs[v];
      });
      return { pairs: pairs, skipped: skipped, synced: added };
    }

    function uniqueCoinKeys() {
      var keys = {};
      collectPairs().forEach(function (p) {
        var t = canonicalTicker(p.venue, p.underlying) || p.underlying;
        var base = String(t || "")
          .toUpperCase()
          .replace(/[-/]/g, "")
          .replace(/(USDT|USD|USDC|PERP)$/i, "");
        keys[base || foldText(t)] = true;
      });
      return Object.keys(keys);
    }

    function syncRankButton() {
      var btn = root.querySelector("#sim-run-rank");
      if (!btn) return;
      var show = uniqueCoinKeys().length === 1;
      btn.hidden = !show;
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
          tryApplyPrefill();
        })
        .catch(function (e) {
          box.textContent = e.message || "error cargando productos";
        });
    }

    function tryApplyPrefill() {
      if (!pendingPrefill) return;
      var p = pendingPrefill;

      if (p.interval) {
        var iv = root.querySelector("#sim-interval");
        if (iv) {
          iv.value = p.interval;
          refreshNBars();
        }
      }
      if (p.period_days != null) {
        var pd = root.querySelector("#sim-period");
        if (pd) {
          var want = String(p.period_days);
          var hasPd = false;
          for (var pi = 0; pi < pd.options.length; pi++) {
            if (pd.options[pi].value === want) {
              hasPd = true;
              break;
            }
          }
          if (hasPd) {
            pd.value = want;
            refreshNBars();
          }
        }
      }
      if (p.leverage != null && p.leverage !== "") {
        var lev = root.querySelector("#sim-lev");
        var levNum = root.querySelector("#sim-lev-num");
        var lv = String(p.leverage);
        if (lev) lev.value = lv;
        if (levNum) levNum.value = lv;
      }
      if (p.capital_mode === "unconstrained") {
        var free = root.querySelector("#sim-cap-free");
        if (free) free.checked = true;
        syncCapitalModeUI();
      } else if (p.capital_mode === "fixed") {
        var fixed = root.querySelector("#sim-cap-fixed");
        if (fixed) fixed.checked = true;
        syncCapitalModeUI();
      }
      if (p.initial_capital != null && p.initial_capital !== "") {
        var capEl = root.querySelector("#sim-capital");
        if (capEl) capEl.value = String(p.initial_capital);
      }
      if (p.per_trade_usd != null && p.per_trade_usd !== "") {
        var pt = root.querySelector("#sim-per-trade");
        if (pt) pt.value = String(p.per_trade_usd);
      }
      if (p.bench_pct != null && p.bench_pct !== "") {
        var bench = root.querySelector("#sim-bench");
        if (bench) bench.value = String(p.bench_pct);
      } else if (p.annual_bench_rate != null && p.annual_bench_rate !== "") {
        var benchR = root.querySelector("#sim-bench");
        if (benchR) {
          benchR.value = String(Number(p.annual_bench_rate) * 100);
        }
      }
      if (p.liq != null) {
        var liq = root.querySelector("#sim-liq");
        if (liq) liq.checked = !!p.liq;
      }
      if (p.funding != null) {
        var fund = root.querySelector("#sim-funding");
        if (fund) fund.checked = !!p.funding;
      }
      if (p.strategy_id) {
        var sel = root.querySelector("#sim-strat-hist");
        if (sel) {
          var has = false;
          for (var i = 0; i < sel.options.length; i++) {
            if (sel.options[i].value === p.strategy_id) {
              has = true;
              break;
            }
          }
          if (has) sel.value = p.strategy_id;
        }
      }

      if (p.pairs && Array.isArray(p.pairs) && p.pairs.length) {
        var universeReady =
          Object.keys(productsByVenue).length > 0 || coinsCache.length > 0;
        if (!universeReady) {
          /* Esperar a que loadUniverse termine (vuelve a llamar tryApplyPrefill). */
          return;
        }
        VENUES.forEach(function (vid) {
          selectedByVenue[vid] = [];
          venueEnabled[vid] = false;
          searchByVenue[vid] = "";
        });
        var restored = 0;
        p.pairs.forEach(function (pair) {
          if (!pair || !pair.venue) return;
          var raw = pair.underlying || pair.ticker;
          if (!raw) return;
          var cid =
            findProductIdByTicker(pair.venue, raw) ||
            (pair.ticker ? findProductIdByTicker(pair.venue, pair.ticker) : null) ||
            raw;
          if (addProductToVenue(pair.venue, cid, false)) restored += 1;
          else if ((selectedByVenue[pair.venue] || []).indexOf(cid) >= 0) {
            restored += 1;
          }
          venueEnabled[pair.venue] = true;
        });
        renderVenuePicks();
        applyFeePreset();
        refreshSizing();
        syncRankButton();
        syncMcSelHint();
        showTab("comparar");
        setRunStatus(
          restored
            ? "reabierto · " +
                restored +
                " par(es) · listo para Comparar / Monte Carlo"
            : "reabierto · params de form (sin pares coincidentes en catálogo)",
          !restored
        );
        pendingPrefill = null;
        return;
      }

      if (p.venue && p.underlying) {
        if (!productsByVenue[p.venue] || !productsByVenue[p.venue].length) {
          return;
        }
        var cid =
          findProductIdByTicker(p.venue, p.underlying) || p.underlying;
        addProductToVenue(p.venue, cid, true);
        venueEnabled[p.venue] = true;
        renderVenuePicks();
        showTab("comparar");
        pendingPrefill = null;
      } else if (p.strategy_id && strategiesCache.length) {
        pendingPrefill = null;
      } else if (
        !p.strategy_id &&
        !p.venue &&
        !(p.pairs && p.pairs.length)
      ) {
        /* Solo meta de form — ya aplicado. */
        pendingPrefill = null;
      }
    }

    function applyPrefill(prefill) {
      if (!prefill || typeof prefill !== "object") return;
      pendingPrefill = Object.assign({}, pendingPrefill || {}, prefill);
      if (prefill.market_type) {
        var msel = root.querySelector("#sim-market");
        if (msel && msel.value !== prefill.market_type) {
          msel.value = prefill.market_type;
          loadUniverse();
          loadFees();
          return;
        }
      }
      tryApplyPrefill();
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
      var exSteps = (g.example_steps || [])
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
      var whenUse = (g.when_to_use || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      return (
        '<p class="sim-guide-plain"><strong>En simple</strong><br>' +
        esc(g.in_plain_words || g.idea || s.description || "—") +
        "</p>" +
        (whenUse
          ? "<p><strong>Cuándo usarla</strong></p>" +
            '<ul class="sim-guide-list">' +
            whenUse +
            "</ul>"
          : "") +
        "<p><strong>Paso a paso (cómo decide el lab)</strong></p>" +
        '<ol class="sim-guide-list">' +
        (steps || "<li>—</li>") +
        "</ol>" +
        "<p><strong>Cuándo compra</strong></p><p class=\"sim-guide-line\">" +
        esc(g.when_buy || "—") +
        "</p>" +
        "<p><strong>Cuándo vende / queda en efectivo</strong></p><p class=\"sim-guide-line\">" +
        esc(g.when_sell || "—") +
        "</p>" +
        '<div class="sim-guide-example"><strong>Ejemplo</strong><br>' +
        esc(g.example || "—") +
        (exSteps
          ? '<p style="margin:0.45rem 0 0.2rem"><strong>Ejemplo paso a paso</strong></p>' +
            '<ol class="sim-guide-list">' +
            exSteps +
            "</ol>"
          : "") +
        "</div>" +
        "<p><strong>Runnable:</strong> " +
        (s.runnable === false ? "no (stub research)" : "sí") +
        (g.runnable_note ? " — " + esc(g.runnable_note) : "") +
        "</p>" +
        "<p><strong>Familia:</strong> " +
        esc(s.family_label_es || s.family || "—") +
        " · <span class=\"muted\">id=" +
        esc(s.id) +
        "</span></p>" +
        "<details class=\"sim-guide-detail\"><summary><strong>Parámetros, riesgos y notas del lab</strong></summary>" +
        "<p><strong>Parámetros</strong></p><ul class=\"sim-guide-list\">" +
        params +
        "</ul>" +
        "<p><strong>Riesgos / límites</strong></p><ul class=\"sim-guide-list\">" +
        risks +
        "</ul>" +
        "<p><strong>Notas del lab</strong></p><ul class=\"sim-guide-list\">" +
        notes +
        "</ul></details>"
      );
    }

    function strategyCardHtml(s, openCard) {
      var id = s.id || s.strategy_id;
      var runnable = s.runnable !== false;
      var g = s.how_it_works || {};
      var teaser = (g.in_plain_words || s.description || "").slice(0, 110);
      return (
        '<details class="sim-strat-card" data-strat-id="' +
        esc(id) +
        '"' +
        (openCard ? " open" : "") +
        ">" +
        "<summary>" +
        "<strong>" +
        esc(s.name || id) +
        "</strong> " +
        '<span class="muted mono">' +
        esc(id) +
        "</span>" +
        (runnable
          ? ' <span class="data-badge">runnable</span>'
          : ' <span class="data-badge data-badge-synth">stub · aún no corre</span>') +
        (teaser
          ? '<div class="muted" style="font-weight:400;font-size:1.04em;margin-top:0.15rem">' +
            esc(teaser) +
            (teaser.length >= 110 ? "…" : "") +
            "</div>"
          : "") +
        "</summary>" +
        '<div class="sim-strat-card-body">' +
        renderGuideHtml(s) +
        '<div class="sim-strat-actions" style="margin-top:0.5rem">' +
        '<button type="button" class="btn sim-use-strat" data-id="' +
        esc(id) +
        '"' +
        (runnable ? "" : " disabled title=\"Stub: todavía no se puede correr\"") +
        ">Usar en Comparar</button> " +
        '<button type="button" class="btn secondary sim-strat-detail" data-id="' +
        esc(id) +
        '">Abrir en ventana</button>' +
        "</div></div></details>"
      );
    }

    function bindStratListActions() {
      root.querySelectorAll(".sim-use-strat").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var id = btn.getAttribute("data-id");
          var sel = root.querySelector("#sim-strat-hist");
          if (sel) sel.value = id;
          showTab("comparar");
          var hist = root.querySelector("#sim-strat-hist");
          if (hist && typeof hist.focus === "function") hist.focus();
        });
      });
      root.querySelectorAll(".sim-strat-detail").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          openStrategyGuide(btn.getAttribute("data-id"));
        });
      });
    }

    function renderStratCatalog() {
      var listEl = root.querySelector("#sim-strat-list");
      var countEl = root.querySelector("#sim-strat-count");
      var q = foldText(
        (root.querySelector("#sim-strat-search") &&
          root.querySelector("#sim-strat-search").value) ||
          ""
      );
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
      var shown = 0;
      var html = selFamKeys
        .map(function (fam, idx) {
          var label = familyLabels[fam] || fam;
          var items = (byFamSelect[fam] || [])
            .slice()
            .sort(function (a, b) {
              var ka = alphaKey(a.name || a.id || "");
              var kb = alphaKey(b.name || b.id || "");
              if (ka < kb) return -1;
              if (ka > kb) return 1;
              return 0;
            })
            .filter(function (s) {
              if (!q) return true;
              var hay = foldText(
                [
                  s.id,
                  s.name,
                  s.description,
                  s.family,
                  s.family_label_es,
                  (s.how_it_works && s.how_it_works.in_plain_words) || "",
                ].join(" ")
              );
              return hay.indexOf(q) >= 0;
            });
          if (!items.length) return "";
          shown += items.length;
          var open = !q && idx === 0 ? " open" : q ? " open" : "";
          var whenFam =
            (items[0].how_it_works && items[0].how_it_works.when_to_use) || [];
          var famIntro =
            whenFam.length > 0
              ? '<p class="muted sim-fam-when" style="font-size:1.06em;margin:0.25rem 0 0.45rem">' +
                "<strong>Cuándo usar esta familia:</strong> " +
                esc(whenFam[0]) +
                "</p>"
              : "";
          return (
            '<details class="sim-strat-group"' +
            open +
            ">" +
            "<summary>" +
            esc(label) +
            ' <span class="muted">(' +
            items.length +
            ")</span></summary>" +
            '<div class="sim-strat-group-body">' +
            famIntro +
            items
              .map(function (s, j) {
                return strategyCardHtml(s, !q && idx === 0 && j === 0);
              })
              .join("") +
            "</div></details>"
          );
        })
        .join("");
      listEl.innerHTML = html || '<p class="muted">sin coincidencias</p>';
      if (countEl) {
        countEl.textContent = shown + " / " + strategiesCache.length;
      }
      bindStratListActions();
    }

    function openStrategyGuide(id) {
      if (global.QLShell && QLShell.open) {
        QLShell.open("strategies", { focusId: id });
        return;
      }
      window.alert("Abrí el panel Estrategias desde el menú QL.");
    }

    function closeStrategyGuide() {
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
          tryApplyPrefill();
        })
        .catch(function (e) {
          var sel = root.querySelector("#sim-strat-hist");
          if (sel) {
            sel.innerHTML =
              "<option value=\"\">" + esc(e.message || "error") + "</option>";
          }
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

    function setRunStatus(msg, isErr) {
      var st = root.querySelector("#sim-run-status");
      var out = root.querySelector("#sim-out-hist");
      if (st) {
        st.textContent = msg || "—";
        st.style.color = isErr ? "#d4544a" : "";
      }
      if (out && msg) {
        out.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    }

    function runCompare(strategyId, pairs, fetchOpts) {
      pairs = pairs || collectPairs();
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
      // Solo override manual: si no, cada mercado usa su schedule VIP0 real
      if (feesManualOverride) {
        var mk = root.querySelector("#sim-maker").value;
        var tk = root.querySelector("#sim-taker").value;
        if (mk !== "") payload.maker_bps = mk;
        if (tk !== "") payload.taker_bps = tk;
      }
      return QLApi.simCompare(payload, fetchOpts);
    }

    function runRankStrategies(pairs, fetchOpts) {
      if (!QLApi.simRankStrategies) {
        return Promise.reject(
          new Error(
            "API simRankStrategies no cargada — reiniciá el Workbench y Ctrl+F5."
          )
        );
      }
      pairs = pairs || collectPairs();
      var mode = capitalMode();
      var payload = {
        pairs: pairs,
        market_type: root.querySelector("#sim-market").value,
        leverage: Number(root.querySelector("#sim-lev").value) || 1,
        interval: root.querySelector("#sim-interval").value,
        period_days: periodDays(),
        capital_mode: mode,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        simulate_liquidation: root.querySelector("#sim-liq").checked,
        apply_funding: root.querySelector("#sim-funding").checked,
        annual_bench_rate: Number(root.querySelector("#sim-bench").value || 0) / 100,
        extra_costs: collectExtraCosts(),
        top_n: 10,
      };
      if (mode === "fixed") {
        payload.initial_capital = root.querySelector("#sim-capital").value;
      }
      if (feesManualOverride) {
        var mk = root.querySelector("#sim-maker").value;
        var tk = root.querySelector("#sim-taker").value;
        if (mk !== "") payload.maker_bps = mk;
        if (tk !== "") payload.taker_bps = tk;
      }
      return QLApi.simRankStrategies(payload, fetchOpts);
    }

    function runSummaryLine(kind, pairs) {
      var coins = (pairs || [])
        .map(function (p) {
          return p.underlying || p.ticker || "?";
        })
        .filter(function (v, i, a) {
          return a.indexOf(v) === i;
        });
      var markets = (pairs || [])
        .map(function (p) {
          return p.venue;
        })
        .filter(function (v, i, a) {
          return a.indexOf(v) === i;
        });
      return (
        coins.join(",") +
        " · " +
        markets.join(",") +
        " · " +
        (kind === "rank"
          ? "ranking"
          : root.querySelector("#sim-strat-hist").value || "?") +
        " · " +
        (root.querySelector("#sim-interval").value || "") +
        " · " +
        periodDays() +
        "d"
      );
    }

    function isAbortErr(e) {
      return (
        global.QLLabUI && QLLabUI.isAbortError
          ? QLLabUI.isAbortError(e)
          : e && (e.name === "AbortError" || /abort/i.test(String(e.message || e)))
      );
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
        "Capital al cerrar el período, YA NETO de fees VIP0/override y gastos extra.\n" +
        "Cada fill descuenta comisión del fee model del mercado.\n" +
        "PnL = capital final − inicial (fees incluidos, no hay que restarlos de nuevo).\n" +
        "Con leverage refleja el overlay de esa x.\n" +
        "La columna «Fees gastados» es el detalle; ya está dentro de este neto.",
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
        "Ya están descontados en «Capital final (neto)».",
      "fee-op":
        "Fee promedio por operación (fill).\n" +
        "Se calcula: fees totales ÷ nº de fills.\n" +
        "Útil para comparar mercados con distinta actividad.\n" +
        "Si no hubo fills, muestra —.\n" +
        "No incluye gastos extra fijos del panel.",
      rentab:
        "Rentabilidad del overlay (PnL %), YA neta de fees.\n" +
        "Las filas se ordenan por moneda y luego por esta % (mayor primero).\n" +
        "Así comparás el mismo activo entre exchanges.\n" +
        "En modo sin monto el % usa la equity de corrida del lab.\n" +
        "Miralo junto a fee/op y dif. vs bench.",
      "dif-bench":        "Diferencia vs el banco (tasa pasiva del período).\n" +
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
      // &#10; evita que saltos de línea rompan el atributo HTML en innerHTML
      var raw = SUMMARY_TIPS[key] || "";
      return (
        ' data-tip="' +
        esc(raw).replace(/\r?\n/g, "&#10;") +
        '"'
      );
    }

    function numOrNull(v) {
      if (v == null || v === "") return null;
      var n = Number(v);
      return isFinite(n) ? n : null;
    }

    function fmtMoney(v) {
      if (global.QLFmt && QLFmt.num) return QLFmt.num(v, 2);
      if (v == null || v === "") return "—";
      var n = Number(v);
      if (!isFinite(n)) return esc(v);
      return esc(
        n.toLocaleString("es-AR", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      );
    }

    function fmtPct(v) {
      if (global.QLFmt && QLFmt.pct) return QLFmt.pct(v);
      if (v == null || v === "") return "—";
      var n = Number(v);
      if (!isFinite(n)) return esc(v);
      return fmtMoney(n) + "%";
    }

    /** Margen/trade y pico: margin_report, o fallback sizing / aliases. */
    function resolveMarginFields(bt, row) {
      var mr = (bt && bt.margin_report) || (row && row.margin_report) || {};
      var sizing = (bt && bt.sizing) || {};
      var marginTrade =
        mr.margin_per_trade != null && mr.margin_per_trade !== ""
          ? mr.margin_per_trade
          : bt && bt.margin_per_trade != null
            ? bt.margin_per_trade
            : sizing.margin != null
              ? sizing.margin
              : null;
      var peak =
        mr.peak_margin != null && mr.peak_margin !== ""
          ? mr.peak_margin
          : bt && bt.peak_margin != null
            ? bt.peak_margin
            : null;
      return { mr: mr, marginTrade: marginTrade, peak: peak };
    }

    function formatRows(data) {
      var rows = (data.rows || []).slice().sort(function (a, b) {
        var ua = foldText(a.underlying || a.instrument_id || "");
        var ub = foldText(b.underlying || b.instrument_id || "");
        if (ua < ub) return -1;
        if (ua > ub) return 1;
        var pa = numOrNull((a.overlay || {}).pnl_pct);
        var pb = numOrNull((b.overlay || {}).pnl_pct);
        if (pa == null && pb == null) return 0;
        if (pa == null) return 1;
        if (pb == null) return -1;
        return pb - pa;
      });
      if (!rows.length) return "sin filas";
      return (
        '<p class="muted" style="font-size:1.06em;margin:0.2rem 0 0.35rem">' +
        "Resumen — orden: moneda A→Z, luego rentabilidad % ↓. " +
        "Al agregar una moneda en un mercado tildado se intenta copiar a los otros tildados." +
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
        ">Capital final (neto)</th>" +
        "<th" +
        tipAttr("rentab") +
        ">Rentab. %</th>" +
        "<th" +
        tipAttr("ops") +
        ">Nº operaciones</th>" +
        "<th" +
        tipAttr("fees") +
        ">Fees gastados</th>" +
        "<th" +
        tipAttr("fee-op") +
        ">Fee/op</th>" +
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
            var marginFields = resolveMarginFields(bt, r);
            var mr = marginFields.mr;
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
            var feeOp =
              bt.avg_fee_per_fill != null
                ? bt.avg_fee_per_fill
                : (function () {
                    var f = numOrNull(fees);
                    var n = numOrNull(nOps);
                    return f != null && n != null && n > 0 ? f / n : null;
                  })();
            var pnlPct = o.pnl_pct;
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
                  dif.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  });
            var shortN = numOrNull(mr.capital_shortfall);
            var needMore = mr.needed_more_money === true;
            var hasMarginReport =
              marginFields.marginTrade != null || marginFields.peak != null;
            var faltTxt;
            if (!r.ok && r.error) {
              faltTxt = "—";
            } else if (!hasMarginReport) {
              faltTxt =
                '<span class="muted" title="Reiniciá el workbench para cargar margen">¿?</span>';
            } else if (mode === "unconstrained") {
              faltTxt =
                "req " +
                fmtMoney(mr.capital_required || marginFields.peak);
            } else if (needMore) {
              faltTxt =
                '<span style="color:#d4544a">sí +' +
                fmtMoney(shortN) +
                "</span>";
            } else {
              faltTxt = '<span style="color:#3d9a6a">no</span>';
            }
            var rentTxt =
              pnlPct == null || pnlPct === ""
                ? "—"
                : fmtPct(pnlPct);
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
              fmtMoney(marginFields.marginTrade) +
              "</td><td" +
              tipAttr("margen-pico") +
              ">" +
              fmtMoney(marginFields.peak) +
              "</td><td" +
              tipAttr("faltante") +
              ">" +
              faltTxt +
              "</td><td" +
              tipAttr("final") +
              ">" +
              fmtMoney(finalEq) +
              "</td><td" +
              tipAttr("rentab") +
              ">" +
              rentTxt +
              "</td><td" +
              tipAttr("ops") +
              ">" +
              esc(nOps != null ? nOps : "—") +
              "</td><td" +
              tipAttr("fees") +
              ">" +
              fmtMoney(fees) +
              "</td><td" +
              tipAttr("fee-op") +
              ">" +
              fmtMoney(feeOp) +
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

    function rankTableHtml(m) {
      if (!m.ok) {
        return (
          '<p class="muted">' + esc(m.error || "sin datos") + "</p>"
        );
      }
      var rows = m.ranked || [];
      return (
        '<table class="sim-summary-table sim-rank-table mono"><thead><tr>' +
        "<th>#</th><th>PnL %</th><th>PnL</th><th>Familia</th><th>Estrategia</th><th>Ops</th>" +
        "</tr></thead><tbody>" +
        rows
          .map(function (r) {
            var o = r.overlay || {};
            var bt = r.backtest || {};
            var nOps = bt.n_fills != null ? bt.n_fills : bt.n_orders;
            return (
              '<tr data-strategy="' +
              esc(r.strategy_id) +
              '"><td>' +
              esc(r.rank) +
              "</td><td>" +
              fmtPct(o.pnl_pct) +
              "</td><td>" +
              fmtMoney(o.pnl) +
              "</td><td>" +
              esc(r.family_label_es || r.family || "—") +
              "</td><td>" +
              esc(r.strategy_name || r.strategy_id) +
              "</td><td>" +
              (nOps != null ? esc(nOps) : "—") +
              "</td></tr>"
            );
          })
          .join("") +
        "</tbody></table>" +
        '<p class="muted" style="font-size:1.06em;margin:0.35rem 0 0">' +
        esc(m.n_strategies_ok || 0) +
        "/" +
        esc(m.n_strategies_run || 0) +
        " OK · " +
        esc(m.n_families_covered || 0) +
        " familias</p>"
      );
    }

    function formatRankResults(data) {
      var markets = data.markets || [];
      var coin = data.coin || "?";
      var common = data.common || {};
      if (!markets.length) return "sin mercados";
      var head =
        '<div class="sim-rank-dock-head">' +
        '<span class="data-badge data-badge-real">RANK</span> ' +
        esc(coin) +
        " · universo " +
        esc(common.n_strategies_universe || "—") +
        " · top " +
        esc(common.top_n || 10) +
        " · x" +
        esc(common.leverage || "1") +
        ' <button type="button" class="btn secondary sim-rank-memo-btn" style="margin-left:0.4rem">Ver memorando</button>' +
        '<label class="sim-rank-dock-font">Letra ' +
        '<input type="range" class="sim-rank-dock-font-range" min="70" max="140" value="100" step="5">' +
        "</label>" +
        "</div>" +
        '<p class="muted" style="font-size:1.04em;margin:0.2rem 0 0.4rem">' +
        "Resultados dentro del Simulador · × cierra cada mercado · click en fila = usar estrategia." +
        "</p>";
      var cols =
        '<div class="sim-rank-dock" id="sim-rank-dock">' +
        markets
          .map(function (m, i) {
            var venue = m.venue || m.market_label || "?";
            return (
              '<details class="sim-rank-panel" open data-venue="' +
              esc(venue) +
              '" data-i="' +
              i +
              '">' +
              "<summary class=\"sim-rank-panel-sum\">" +
              "<strong>" +
              esc(venue) +
              "</strong>" +
              ' <span class="muted mono">' +
              esc(m.underlying || coin) +
              "</span>" +
              (m.ok
                ? ' <span class="muted">· ' +
                  esc((m.ranked || []).length) +
                  " estrategias</span>"
                : ' <span class="status-bad">error</span>') +
              ' <button type="button" class="sim-rank-panel-close" title="Cerrar este mercado" aria-label="Cerrar">×</button>' +
              "</summary>" +
              '<div class="sim-rank-panel-body">' +
              rankTableHtml(m) +
              "</div></details>"
            );
          })
          .join("") +
        "</div>";
      return head + cols;
    }

    function bindRankDockActions(container, data) {
      if (!container) return;
      var dock = container.querySelector("#sim-rank-dock") || container;
      var fontRange = container.querySelector(".sim-rank-dock-font-range");
      if (fontRange) {
        fontRange.addEventListener("input", function () {
          var pct = Number(fontRange.value) || 100;
          dock.style.fontSize = pct / 100 + "rem";
        });
      }
      container.querySelectorAll(".sim-rank-panel-close").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var panel = btn.closest(".sim-rank-panel");
          if (panel) panel.remove();
        });
      });
      /* Evitar que el × dispare toggle del details vía summary */
      container.querySelectorAll(".sim-rank-panel-sum").forEach(function (sum) {
        sum.addEventListener("click", function (ev) {
          if (ev.target && ev.target.closest && ev.target.closest(".sim-rank-panel-close")) {
            ev.preventDefault();
          }
        });
      });
      container.querySelectorAll("tr[data-strategy]").forEach(function (tr) {
        tr.style.cursor = "pointer";
        tr.title = "Click: usar en Comparar";
        tr.addEventListener("click", function () {
          var sid = tr.getAttribute("data-strategy");
          var sel = root.querySelector("#sim-strat-hist");
          if (sel && sid) sel.value = sid;
        });
      });
      var memoBtn = container.querySelector(".sim-rank-memo-btn");
      if (memoBtn && data) {
        memoBtn.addEventListener("click", function () {
          openSimMemoPresentation(buildRankMemo(data));
        });
      }
    }

    function closeFloatingRankWindows() {
      var wm = global.QLShell && global.QLShell.wm;
      if (!wm || !wm.windows) return;
      var ids = [];
      wm.windows.forEach(function (_rec, id) {
        if (String(id).indexOf("sim_rank_") === 0) ids.push(id);
      });
      ids.forEach(function (id) {
        if (typeof wm.close === "function") wm.close(id);
      });
    }

    function csvCell(v) {
      var s = v == null ? "" : String(v);
      if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
      return s;
    }

    function stampNow() {
      var d = new Date();
      function z(n) {
        return n < 10 ? "0" + n : String(n);
      }
      return (
        d.getFullYear() +
        z(d.getMonth() + 1) +
        z(d.getDate()) +
        "_" +
        z(d.getHours()) +
        z(d.getMinutes()) +
        z(d.getSeconds())
      );
    }

    function downloadBlob(filename, text, mime) {
      var blob = new Blob([text], { type: mime || "text/plain;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () {
        URL.revokeObjectURL(url);
      }, 60000);
      return url;
    }

    function collectRunMeta() {
      return {
        generated_at: new Date().toISOString(),
        market_type: root.querySelector("#sim-market").value,
        interval: root.querySelector("#sim-interval").value,
        period_days: periodDays(),
        leverage: root.querySelector("#sim-lev").value,
        capital_mode: capitalMode(),
        initial_capital: root.querySelector("#sim-capital").value,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        bench_pct: root.querySelector("#sim-bench").value,
        liq: !!root.querySelector("#sim-liq").checked,
        funding: !!root.querySelector("#sim-funding").checked,
        live_blocked: true,
        tool: "QuantLab Simulador",
      };
    }

    function strategyLabel(id) {
      var s = findStrategy(id);
      if (s) return (s.name || id) + " (" + id + ")";
      return id || "—";
    }

    /** Snapshot para Monte Carlo / memorando: moneda + params de ESTA simulación. */
    function buildSimHandoff(kind, pairs, extra) {
      extra = extra || {};
      var meta = collectRunMeta();
      var sid =
        extra.strategy_id ||
        (root.querySelector("#sim-strat-hist") &&
          root.querySelector("#sim-strat-hist").value) ||
        "";
      var pairList = (pairs || collectPairs()).map(function (p) {
        return {
          venue: p.venue,
          underlying: p.underlying,
          ticker: canonicalTicker(p.venue, p.underlying) || p.underlying,
        };
      });
      var coins = [];
      pairList.forEach(function (p) {
        var t = p.ticker || p.underlying;
        if (t && coins.indexOf(t) < 0) coins.push(t);
      });
      var venues = [];
      pairList.forEach(function (p) {
        if (p.venue && venues.indexOf(p.venue) < 0) venues.push(p.venue);
      });
      var handoff = {
        source: "simulator",
        kind: kind || "compare",
        strategy_id: sid,
        strategy_label: strategyLabel(sid),
        coins: coins,
        coin: coins.length === 1 ? coins[0] : coins.join(", "),
        venues: venues,
        pairs: pairList,
        market_type: meta.market_type,
        interval: meta.interval,
        period_days: meta.period_days,
        leverage: meta.leverage,
        capital_mode: meta.capital_mode,
        initial_capital: meta.initial_capital,
        per_trade_usd: meta.per_trade_usd,
        bench_pct: meta.bench_pct,
        liq: meta.liq,
        funding: meta.funding,
        generated_at: meta.generated_at,
        summary_line:
          (kind === "rank" ? "Ranking" : "Comparar") +
          " · " +
          (coins.join(", ") || "sin moneda") +
          " · " +
          (venues.join(", ") || "sin mercado") +
          " · " +
          strategyLabel(sid) +
          " · " +
          meta.interval +
          " · " +
          meta.period_days +
          "d · x" +
          meta.leverage,
      };
      if (extra.coin) handoff.coin = extra.coin;
      lastSimHandoff = handoff;
      return handoff;
    }

    function formatHandoffBlock(h) {
      if (!h) return [];
      return [
        "— IDENTIDAD DE ESTA CORRIDA —",
        "Qué: " + (h.kind === "rank" ? "Ranking estrategias" : "Comparar mercados"),
        "Moneda(s): " + (h.coin || (h.coins && h.coins.join(", ")) || "—"),
        "Mercado(s): " + ((h.venues && h.venues.join(", ")) || "—"),
        "Estrategia: " + (h.strategy_label || h.strategy_id || "—"),
        "Tipo: " + (h.market_type || "—"),
        "TF / período: " + (h.interval || "—") + " · " + (h.period_days != null ? h.period_days + " días" : "—"),
        "Leverage: x" + (h.leverage != null ? h.leverage : "—"),
        "Capital: " +
          (h.capital_mode || "—") +
          " · inicial=" +
          (h.initial_capital != null ? h.initial_capital : "—") +
          " · por trade=" +
          (h.per_trade_usd != null ? h.per_trade_usd : "—"),
        "Pares: " +
          ((h.pairs || [])
            .map(function (p) {
              return (p.venue || "?") + "/" + (p.ticker || p.underlying || "?");
            })
            .join(", ") || "—"),
        "",
      ];
    }

    function buildCompareMemo(data) {
      var common = data.common || {};
      var meta = collectRunMeta();
      var rows = data.rows || [];
      var pairs = (rows || []).map(function (r) {
        return { venue: r.venue, underlying: r.underlying || r.instrument_id };
      });
            var handoff = freezeHandoffCapital(
        buildSimHandoff("compare", pairs.length ? pairs : null, {
          strategy_id: (common && common.strategy_id) || "",
        }),
        common
      );
      var lines = [];
      lines.push("QUANTLAB — MEMORANDO DE SIMULACIÓN (Comparar)");
      lines.push("Generado: " + meta.generated_at);
      lines.push("LIVE_BLOCKED=true · research / sin order routing");
      lines.push("");
      lines = lines.concat(formatHandoffBlock(handoff));
      lines.push("— PARÁMETROS DETALLE —");
      lines.push("Estrategia: " + (common.strategy_id || handoff.strategy_id || "—"));
      lines.push("Modo: " + (common.market_type || meta.market_type));
      lines.push("Intervalo: " + (common.interval || meta.interval));
      lines.push("Período (días): " + (common.period_days != null ? common.period_days : meta.period_days));
      lines.push("Velas (kline_limit): " + (common.kline_limit != null ? common.kline_limit : "—"));
      lines.push("Capital mode: " + (common.capital_mode || meta.capital_mode));
      lines.push("Capital inicial: " + (common.initial_capital != null ? common.initial_capital : meta.initial_capital));
      lines.push("Por trade (USDT): " + (common.per_trade_usd || meta.per_trade_usd));
      lines.push("Bench anual: " + (common.annual_bench_rate || meta.bench_pct + "%"));
      lines.push("Liquidación sim: " + (common.simulate_liquidation != null ? common.simulate_liquidation : meta.liq));
      lines.push("Funding: " + (common.apply_funding != null ? common.apply_funding : meta.funding));
      lines.push("Fees: PnL y capital final YA NETOS (MakerTaker VIP0 por mercado).");
      lines.push("Filas: " + rows.length);
      lines.push("");
      lines.push("— RESULTADOS POR MERCADO —");
      var csvHeader = [
        "mercado",
        "modo",
        "moneda",
        "instrumento",
        "leverage",
        "strategy_id",
        "ok",
        "error",
        "capital_inicial",
        "capital_final_neto",
        "pnl",
        "pnl_pct",
        "n_ops",
        "fees_totales",
        "fee_por_op",
        "margen_trade",
        "margen_pico",
        "faltante",
        "bench_period_return",
        "dif_vs_bench",
        "liquidated",
        "fee_maker_bps",
        "fee_taker_bps",
        "session_id",
      ];
      var csvLines = [csvHeader.join(",")];
      rows.forEach(function (r, i) {
        var o = r.overlay || {};
        var bt = r.backtest || {};
        var mf = resolveMarginFields(bt, r);
        var mr = mf.mr;
        var b = bt.benchmark || {};
        var fees = bt.total_fees;
        var nOps = bt.n_fills != null ? bt.n_fills : bt.n_orders;
        var feeOp =
          bt.avg_fee_per_fill != null
            ? bt.avg_fee_per_fill
            : numOrNull(fees) != null && numOrNull(nOps) > 0
              ? numOrNull(fees) / numOrNull(nOps)
              : null;
        var pnlN = numOrNull(o.pnl);
        var benchN = numOrNull(b.period_return);
        var dif = pnlN != null && benchN != null ? pnlN - benchN : null;
        var feeSched = (bt.fee_schedule_venue || {});
        lines.push("");
        lines.push("#" + (i + 1) + " " + (r.venue || "?") + " · " + (r.underlying || "?") + " · x" + (r.leverage || "?"));
        lines.push("  ok=" + !!r.ok + (r.error ? " error=" + r.error : ""));
        lines.push("  instrumento=" + (r.instrument_id || "—"));
        lines.push("  capital_final_neto=" + (o.final_equity != null ? o.final_equity : bt.final_equity));
        lines.push("  pnl=" + (o.pnl != null ? o.pnl : "—") + " · pnl%=" + (o.pnl_pct != null ? o.pnl_pct : "—"));
        lines.push("  ops=" + (nOps != null ? nOps : "—") + " · fees=" + (fees != null ? fees : "—") + " · fee/op=" + (feeOp != null ? feeOp : "—"));
        lines.push("  margen/trade=" + (mf.marginTrade != null ? mf.marginTrade : "—") + " · pico=" + (mf.peak != null ? mf.peak : "—"));
        lines.push("  dif_vs_bench=" + (dif != null ? dif : "—") + " · liq=" + !!o.liquidated);
        lines.push(
          "  fees_schedule=" +
            (feeSched.maker_bps != null ? feeSched.maker_bps : "?") +
            "/" +
            (feeSched.taker_bps != null ? feeSched.taker_bps : "?") +
            " bps maker/taker"
        );
        csvLines.push(
          [
            r.venue,
            r.market_type,
            r.underlying,
            r.instrument_id,
            r.leverage,
            r.strategy_id,
            r.ok,
            r.error || "",
            o.initial_equity != null ? o.initial_equity : bt.initial_equity,
            o.final_equity != null ? o.final_equity : bt.final_equity,
            o.pnl,
            o.pnl_pct,
            nOps,
            fees,
            feeOp,
            mf.marginTrade,
            mf.peak,
            mr.capital_shortfall || "",
            b.period_return,
            dif,
            o.liquidated,
            feeSched.maker_bps,
            feeSched.taker_bps,
            data.session_id || "",
          ]
            .map(csvCell)
            .join(",")
        );
      });
      lines.push("");
      lines.push("— FIN MEMORANDO —");
      lines.push("Adjuntá el CSV para verificación fila a fila.");
      return {
        kind: "compare",
        title: "Memorando · Comparar",
        text: lines.join("\n"),
        csv: csvLines.join("\n"),
        filenameBase: "quantlab-sim-compare-" + stampNow(),
        nRows: rows.length,
      };
    }

    function buildRankMemo(data) {
      var common = data.common || {};
      var meta = collectRunMeta();
      var markets = data.markets || [];
      var pairs = markets.map(function (m) {
        return { venue: m.venue, underlying: m.underlying || data.coin };
      });
      var handoff = freezeHandoffCapital(
        buildSimHandoff("rank", pairs, {
          strategy_id: "",
          coin: data.coin || "",
        }),
        common
      );
      var lines = [];
      lines.push("QUANTLAB — MEMORANDO DE SIMULACIÓN (Ranking estrategias)");
      lines.push("Generado: " + meta.generated_at);
      lines.push("LIVE_BLOCKED=true · research / sin order routing");
      lines.push("");
      lines = lines.concat(formatHandoffBlock(handoff));
      lines.push("— PARÁMETROS DETALLE —");
      lines.push("Moneda: " + (data.coin || handoff.coin || "—"));
      lines.push("Modo: " + (common.market_type || meta.market_type));
      lines.push("Intervalo: " + (common.interval || meta.interval));
      lines.push("Velas: " + (common.kline_limit != null ? common.kline_limit : "—"));
      lines.push("Leverage: x" + (common.leverage || meta.leverage));
      lines.push("Capital mode: " + (common.capital_mode || meta.capital_mode));
      lines.push("Por trade: " + (common.per_trade_usd || meta.per_trade_usd));
      lines.push("Universo estrategias: " + (common.n_strategies_universe || "—"));
      lines.push("Excluidas: " + ((common.excluded_strategy_ids || []).join(", ") || "—"));
      lines.push("Top N: " + (common.top_n || 10) + " (≥1 por familia)");
      lines.push("Fees: PnL % YA NETO de comisiones VIP0 por mercado.");
      lines.push("Mercados: " + markets.length);
      lines.push("");
      var csvHeader = [
        "mercado",
        "moneda",
        "rank",
        "strategy_id",
        "strategy_name",
        "family",
        "family_label",
        "ok_market",
        "market_error",
        "pnl",
        "pnl_pct",
        "n_ops",
        "fees",
        "leverage",
        "interval",
        "kline_limit",
        "session_id",
      ];
      var csvLines = [csvHeader.join(",")];
      markets.forEach(function (m) {
        lines.push("");
        lines.push("### Mercado " + (m.venue || "?") + " · " + (m.underlying || data.coin || "?"));
        lines.push(
          "  ok=" +
            !!m.ok +
            (m.error ? " error=" + m.error : "") +
            " · OK " +
            (m.n_strategies_ok || 0) +
            "/" +
            (m.n_strategies_run || 0) +
            " · familias " +
            (m.n_families_covered || 0)
        );
        (m.ranked || []).forEach(function (r) {
          var o = r.overlay || {};
          var bt = r.backtest || {};
          var nOps = bt.n_fills != null ? bt.n_fills : bt.n_orders;
          lines.push(
            "  #" +
              r.rank +
              " " +
              (r.strategy_name || r.strategy_id) +
              " [" +
              (r.family_label_es || r.family || "?") +
              "] pnl%=" +
              (o.pnl_pct != null ? o.pnl_pct : "—") +
              " pnl=" +
              (o.pnl != null ? o.pnl : "—") +
              " ops=" +
              (nOps != null ? nOps : "—") +
              " fees=" +
              (bt.total_fees != null ? bt.total_fees : "—")
          );
          csvLines.push(
            [
              m.venue,
              m.underlying || data.coin,
              r.rank,
              r.strategy_id,
              r.strategy_name,
              r.family,
              r.family_label_es,
              m.ok,
              m.error || "",
              o.pnl,
              o.pnl_pct,
              nOps,
              bt.total_fees,
              common.leverage || meta.leverage,
              common.interval || meta.interval,
              common.kline_limit,
              data.session_id || "",
            ]
              .map(csvCell)
              .join(",")
          );
        });
        if (!m.ok && !(m.ranked || []).length) {
          csvLines.push(
            [
              m.venue,
              m.underlying || data.coin,
              "",
              "",
              "",
              "",
              "",
              false,
              m.error || "",
              "",
              "",
              "",
              "",
              common.leverage,
              common.interval,
              common.kline_limit,
              data.session_id || "",
            ]
              .map(csvCell)
              .join(",")
          );
        }
      });
      lines.push("");
      lines.push("— FIN MEMORANDO —");
      lines.push("Adjuntá el CSV para verificación fila a fila.");
      return {
        kind: "rank",
        title: "Memorando · Ranking " + (data.coin || ""),
        text: lines.join("\n"),
        csv: csvLines.join("\n"),
        filenameBase: "quantlab-sim-rank-" + (data.coin || "coin") + "-" + stampNow(),
        nRows: csvLines.length - 1,
      };
    }

    function registerSimRun(memo, summary, params) {
      if (!memo || !global.QLSimRegistry || typeof global.QLSimRegistry.add !== "function") {
        return;
      }
      try {
        global.QLSimRegistry.add({
          kind: memo.kind,
          title: memo.title,
          summary: summary || "",
          params: params || {},
          memo: memo,
        });
      } catch (e) {}
    }

    function openSimMemoPresentation(memo, opts) {
      if (!memo) return;
      opts = opts || {};
      if (opts.register) {
        registerSimRun(memo, opts.summary, opts.params);
      }
      // Tras una corrida (register): no saltar a Mis simulaciones ni al memo.
      // Solo abrir el memorando si el usuario lo pide (botón «Ver memorando»).
      var openMemo =
        opts.openMemo === true || (!opts.register && opts.openMemo !== false);
      if (!openMemo) {
        if (opts.register) {
          setRunStatus(
            "listo · guardado en Mis simulaciones (panel queda detrás)"
          );
        }
        return;
      }
      if (global.QLSimRegistry && typeof global.QLSimRegistry.openMemo === "function") {
        global.QLSimRegistry.openMemo(memo, opts.params);
        setRunStatus(
          "memorando listo · " + (memo.filenameBase || "memo") + ".csv"
        );
        return;
      }
      setRunStatus("memorando listo (sin panel registro)");
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
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        showTab(btn.getAttribute("data-tab"));
      });
    });
    var openStratBtn = root.querySelector("#sim-open-strategies");
    if (openStratBtn) {
      openStratBtn.addEventListener("click", function (ev) {
        ev.preventDefault();
        if (global.QLShell && QLShell.open) QLShell.open("strategies");
      });
    }
    var stratSearch = root.querySelector("#sim-strat-search");
    if (stratSearch) {
      stratSearch.addEventListener("input", function () {});
    }
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
      var prep = preparePairsForRun();
      var pairs = prep.pairs;
      if (!pairs.length) {
        var msg =
          "Elegí al menos un mercado activo y agregá una moneda con el botón «+».";
        out.textContent = msg;
        setRunStatus(msg, true);
        return;
      }
      var markets = pairs
        .map(function (p) {
          return p.venue;
        })
        .filter(function (v, i, a) {
          return a.indexOf(v) === i;
        });
      var note =
        "comparando " +
        pairs.length +
        " par(es) en " +
        markets.join(", ") +
        "…";
      if (prep.skipped.length) {
        note +=
          " · sin moneda en: " + prep.skipped.join(", ") + " (no se incluyen)";
      }
      var stratId = root.querySelector("#sim-strat-hist").value;
      var gateSpec = {
        kind: "sim_compare",
        label: "Comparar",
        summary: runSummaryLine("compare", pairs),
        busyRoot: root,
      };

      function afterCompare(d) {
        var feeNote =
          '<p class="muted" style="font-size:1.04em;margin:0.15rem 0">' +
          "PnL y capital final ya son NETOS de fees (VIP0 por mercado). " +
          "La columna «Fees gastados» es el detalle; no hay que restarlos otra vez. " +
          '<button type="button" class="btn secondary sim-compare-memo-btn" style="margin-left:0.35rem">Ver memorando</button>' +
          "</p>";
        out.innerHTML =
          '<span class="data-badge data-badge-real">HISTÓRICO</span> ' +
          feeNote +
          formatRows(d) +
          '<div class="sim-actions sim-mc-after-table" style="margin-top:0.55rem">' +
          '<button type="button" class="btn sim-compare-mc-btn" ' +
          'title="Estresa esta misma selección (mercado + moneda + estrategia) en Monte Carlo">' +
          "Monte Carlo</button>" +
          '<span class="muted mono" style="margin-left:0.45rem">' +
          esc(markets.join(", ")) +
          " · " +
          esc(
            (pairs[0] && (pairs[0].underlying || pairs[0].ticker)) ||
              "selección"
          ) +
          "</span></div>";
        var memoBtn = out.querySelector(".sim-compare-memo-btn");
        if (memoBtn) {
          memoBtn.addEventListener("click", function () {
            openSimMemoPresentation(buildCompareMemo(d));
          });
        }
        var mcBtn = out.querySelector(".sim-compare-mc-btn");
        if (mcBtn) {
          mcBtn.addEventListener("click", function () {
            openMonteCarloFromSelection();
          });
        }
        syncMcSelHint();
        setRunStatus(
          "listo · " +
            (d.rows || []).length +
            " filas · mercados: " +
            markets.join(", ") +
            " · guardado en Mis simulaciones"
        );
        try {
          var cmpMemo = buildCompareMemo(d);
          openSimMemoPresentation(cmpMemo, {
            register: true,
            summary:
              (d.rows || []).length +
              " filas · " +
              markets.join(", "),
            params: {
              kind: "compare",
              strategy_id: (d.common && d.common.strategy_id) || "",
              markets: markets,
              pairs: pairs,
              common: d.common || {},
              meta: collectRunMeta(),
              sim_context: freezeHandoffCapital(
                lastSimHandoff ||
                  buildSimHandoff("compare", pairs, {
                    strategy_id: (d.common && d.common.strategy_id) || "",
                  }),
                d.common || {}
              ),
            },
          });
        } catch (memoErr) {
          setRunStatus(
            "listo · memo error: " + (memoErr.message || memoErr),
            true
          );
        }
      }

      function startCompare(handle) {
        out.textContent = note;
        setRunStatus(note);
        var fetchOpts =
          handle && handle.signal ? { signal: handle.signal } : undefined;
        runCompare(stratId, pairs, fetchOpts)
          .then(afterCompare)
          .catch(function (e) {
            if (isAbortErr(e)) {
              out.textContent = "detenido";
              setRunStatus("detenido", true);
              return;
            }
            var err = e.message || String(e);
            out.textContent = err;
            setRunStatus(err, true);
          })
          .then(function () {
            if (handle) handle.end();
          });
      }

      if (!global.QLRunGate) {
        startCompare(null);
        return;
      }
      QLRunGate.begin(gateSpec).then(function (handle) {
        if (!handle) return;
        startCompare(handle);
      });
    });
    var rankBtn = root.querySelector("#sim-run-rank");
    if (rankBtn) {
      rankBtn.addEventListener("click", function () {
        var out = root.querySelector("#sim-out-hist");
        var prep = preparePairsForRun();
        var pairs = prep.pairs;
        var coins = uniqueCoinKeys();
        if (coins.length !== 1) {
          var need =
            coins.length === 0
              ? "Agregá UNA moneda con «+» en un mercado tildado (buscar en la lista no alcanza)."
              : "Para ranking dejá exactamente UNA moneda (sacá las otras con ×).";
          out.textContent = need;
          setRunStatus(need, true);
          syncRankButton();
          return;
        }
        if (!pairs.length) {
          var noPair = "Elegí al menos un mercado con esa moneda.";
          out.textContent = noPair;
          setRunStatus(noPair, true);
          return;
        }
        var busy =
          "Ranking " +
          coins[0] +
          " · " +
          pairs.length +
          " mercado(s) · ~37 estrategias (puede tardar 1–3 min)…";
        if (prep.skipped.length) {
          busy += " · omitidos: " + prep.skipped.join(", ");
        }

        function startRank(handle) {
          out.textContent = busy;
          setRunStatus(busy);
          rankBtn.disabled = true;
          closeFloatingRankWindows();
          var fetchOpts =
            handle && handle.signal ? { signal: handle.signal } : undefined;
          runRankStrategies(pairs, fetchOpts)
            .then(function (d) {
              out.innerHTML = formatRankResults(d);
              bindRankDockActions(out, d);
              out.scrollIntoView({ block: "nearest", behavior: "smooth" });
              var nOk = (d.markets || []).filter(function (m) {
                return m.ok;
              }).length;
              setRunStatus(
                "listo · " +
                  coins[0] +
                  " · " +
                  nOk +
                  "/" +
                  pairs.length +
                  " mercados · paneles en Simulador"
              );
              try {
                var rankMemo = buildRankMemo(d);
                openSimMemoPresentation(rankMemo, {
                  register: true,
                  summary:
                    (d.coin || coins[0]) +
                    " · " +
                    nOk +
                    "/" +
                    pairs.length +
                    " mercados",
                  params: {
                    kind: "rank",
                    coin: d.coin || coins[0],
                    markets: pairs.map(function (p) {
                      return p.venue;
                    }),
                    pairs: pairs,
                    meta: collectRunMeta(),
                    sim_context: freezeHandoffCapital(
                      lastSimHandoff ||
                        buildSimHandoff("rank", pairs, {
                          strategy_id: "",
                          coin: d.coin || coins[0],
                        }),
                      d.common || {}
                    ),
                  },
                });
              } catch (memoErr) {
                setRunStatus(
                  "listo · memo error: " + (memoErr.message || memoErr),
                  true
                );
              }
            })
            .catch(function (e) {
              if (isAbortErr(e)) {
                out.textContent = "detenido";
                setRunStatus("detenido", true);
                return;
              }
              var err = e.message || String(e);
              out.textContent = err;
              setRunStatus(err, true);
            })
            .then(function () {
              if (handle) handle.end();
              rankBtn.disabled = false;
              syncRankButton();
            });
        }

        if (!global.QLRunGate) {
          startRank(null);
          return;
        }
        QLRunGate.begin({
          kind: "sim_rank",
          label: "Ranking",
          summary: runSummaryLine("rank", pairs),
          busyRoot: root,
        }).then(function (handle) {
          if (!handle) return;
          startRank(handle);
        });
      });
    }
    if (global.QLRunGate) {
      QLRunGate.bindStopButton(root.querySelector("#sim-stop"), {
        kinds: ["sim_compare", "sim_rank"],
        onStop: function () {
          setRunStatus("detenido", true);
          var out = root.querySelector("#sim-out-hist");
          if (out) out.textContent = "detenido";
        },
      });
      QLRunGate.bindBusyHost(root, { kinds: ["sim_compare", "sim_rank"] });
    }
    root.querySelector("#sim-strat-info").addEventListener("click", function () {
      openStrategyGuide(root.querySelector("#sim-strat-hist").value);
    });
    function bindOpenMc(el) {
      if (!el) return;
      el.addEventListener("click", function () {
        openMonteCarloFromSelection();
      });
    }
    bindOpenMc(root.querySelector("#sim-open-mc"));
    var liveTestBtn = root.querySelector("#sim-open-live-test");
    if (liveTestBtn) {
      liveTestBtn.addEventListener("click", function () {
        openLiveTestFromSelection();
      });
    }
    syncMcSelHint();

    root.getSimHandoff = function () {
      return lastSimHandoff || buildSimHandoff("compare", collectPairs(), {});
    };
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

    root.applyPrefill = applyPrefill;

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSimulatorPane = createSimulatorPane;
})(window);
