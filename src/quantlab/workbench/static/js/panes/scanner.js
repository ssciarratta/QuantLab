/** Panel Alpha Scanner — MD real multi-venue + período/TF/velas → Simulador. */
(function (global) {
  "use strict";

  var INTERVALS = [
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "12h",
    "1d",
    "1w",
  ];
  var PERIODS = [
    { id: "1", label: "1 día", days: 1 },
    { id: "7", label: "1 semana", days: 7 },
    { id: "30", label: "1 mes", days: 30 },
    { id: "90", label: "3 meses", days: 90 },
    { id: "180", label: "6 meses", days: 180 },
    { id: "365", label: "1 año", days: 365 },
  ];
  var INTERVAL_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
    "3d": 4320,
    "1w": 10080,
    "1M": 43200,
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

  function optHtml(list, selected) {
    return list
      .map(function (x) {
        var id = typeof x === "string" ? x : x.id;
        var label = typeof x === "string" ? x : x.label;
        return (
          '<option value="' +
          esc(id) +
          '"' +
          (String(id) === String(selected) ? " selected" : "") +
          ">" +
          esc(label) +
          "</option>"
        );
      })
      .join("");
  }

  function createScannerPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-scanner";
    root.innerHTML =
      '<div class="pane-section sc-pane">' +
      '<div class="sc-head">' +
      '<p class="muted sc-sub">MD real · ranking por rama · score ≠ rentabilidad · barra superior = mover / × cerrar</p>' +
      "</div>" +
      '<div class="sc-toolbar">' +
      '<label>Modo<select id="sc-scan-mode">' +
      '<option value="individual" selected>Individual</option>' +
      '<option value="pairwise">Pares (pairwise)</option>' +
      "</select></label>" +
      '<label>Fuente<select id="sc-source">' +
      '<option value="real" selected>MD real</option>' +
      '<option value="synthetic">Demo WB</option>' +
      "</select></label>" +
      '<label>Mercado<select id="sc-market">' +
      '<option value="spot" selected>Spot</option>' +
      '<option value="futures">Futuros</option>' +
      "</select></label>" +
      '<label>Ventana<select id="sc-window-mode">' +
      '<option value="period" selected>Período</option>' +
      '<option value="klines">N velas</option>' +
      "</select></label>" +
      '<label id="sc-period-wrap">Período<select id="sc-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label>TF<select id="sc-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<label id="sc-klines-wrap" hidden>Velas' +
      '<input id="sc-klines" type="number" value="720" min="10" max="525600" /></label>' +
      '<label>Rama<select id="sc-profile">' +
      '<option value="auto" selected>Auto</option>' +
      '<option value="trend">Tendenciales</option>' +
      '<option value="momentum">Momentum</option>' +
      '<option value="mean_reversion">Reversión</option>' +
      '<option value="market_making">Market making</option>' +
      '<option value="stats">Estadísticas</option>' +
      '<option value="ml">ML (stubs)</option>' +
      '<option value="multi_asset">Multi-activo</option>' +
      '<option value="microstructure">Microestructura</option>' +
      '<option value="arbitrage">Arbitraje</option>' +
      '<option value="options">Opciones</option>' +
      "</select></label>" +
      '<label>Top<input id="sc-top" type="number" value="5" min="1" max="100" ' +
      'title="Cuántas monedas mostrar en el ranking (1–100)" /></label>' +
      '<label>Universo<select id="sc-limit-mode">' +
      '<option value="n" selected>Cantidad</option>' +
      '<option value="0">Todas</option>' +
      '<option value="custom">Moneda puntual…</option>' +
      "</select></label>" +
      '<label id="sc-limit-n-wrap">N monedas' +
      '<input id="sc-limit-n" type="number" value="30" min="1" max="500" ' +
      'title="Cantidad de monedas del universo a scorear (1–500)" /></label>' +
      '<label id="sc-coin-wrap" hidden>Moneda' +
      '<div class="sc-coin-pick">' +
      '<input id="sc-coin" type="search" placeholder="Buscar: BTC, ETH, NEAR…" ' +
      'autocomplete="off" spellcheck="false" aria-autocomplete="list" ' +
      'aria-controls="sc-coin-suggest" />' +
      '<ul id="sc-coin-suggest" class="sc-coin-suggest" hidden role="listbox"></ul>' +
      "</div></label>" +
      "</div>" +
      '<div class="sc-venues" id="sc-kronos-row" style="flex-wrap:wrap;gap:0.45rem 0.75rem;align-items:center">' +
      '<label title="Forecast de horizonte dentro del Scanner (no es panel aparte)">' +
      '<input type="checkbox" id="sc-kronos-enabled" checked> Kronos</label>' +
      '<label>Top Kronos<input id="sc-kronos-top" type="number" value="20" min="1" max="100" ' +
      'title="A cuántas monedas del ranking aplicar Kronos (1–100)" /></label>' +
      '<label>Horizonte<input id="sc-kronos-pred" type="number" value="12" min="4" max="128" ' +
      'title="Velas futuras (default alineado al TF; editable)" /></label>' +
      '<label>Muestras<input id="sc-kronos-samples" type="number" value="4" min="1" max="16" /></label>' +
      '<label title="Rompe compatibilidad histórica del score legacy">' +
      '<input type="checkbox" id="sc-kronos-legacy"> Kronos en legacy</label>' +
      '<span class="muted" style="font-size:1.10em;margin-left:0.25rem">' +
      "Trad. + Kronos → Final · no garantiza PnL · click en score = memo" +
      "</span>" +
      "</div>" +
      '<div class="sc-venues" id="sc-pairwise-row" hidden style="flex-wrap:wrap;gap:0.45rem 0.75rem;align-items:center">' +
      "<span class=\"muted\">Detectores pairwise</span>" +
      '<label><input type="checkbox" class="sc-pw-det" value="contemporary_correlation" checked> Correlación</label>' +
      '<label><input type="checkbox" class="sc-pw-det" value="lagged_correlation" checked> Lag</label>' +
      '<label><input type="checkbox" class="sc-pw-det" value="cointegration" checked> Cointegración</label>' +
      '<label><input type="checkbox" class="sc-pw-det" value="pair_spread" checked> Spread z</label>' +
      '<label title="Backtest OOS 30% + Deflated Sharpe (más lento)">' +
      '<input type="checkbox" id="sc-pw-validate"> Validación OOS</label>' +
      '<span class="muted" style="font-size:1.02em">min 120 velas · mismo venue · score ≠ rentabilidad</span>' +
      "</div>" +
      '<div class="sc-venues" id="sc-venues-row">' +
      "<span class=\"muted\">Mercados</span>" +
      '<label><input type="checkbox" class="sc-venue-cb" value="binance" checked> Binance</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="okx"> OKX</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="bybit"> Bybit</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="hyperliquid"> HL</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="a3"> A3</label>' +
      '<label title="GBM sobre candidatas; Validar alimenta un candidato (no pisa el activo si empeora)">' +
      '<input type="checkbox" id="sc-include-ml" checked> ML ranking</label>' +
      '<span class="mono muted" id="sc-ml-badge" title="Estado del modelo ML"></span>' +
      '<span class="mono muted" id="sc-nbars" style="margin-left:auto">≈ —</span>' +
      "</div>" +
      '<div class="sc-actions">' +
      '<button type="button" class="btn" id="sc-run">Escanear</button>' +
      '<button type="button" class="btn secondary stop-run" id="sc-stop" hidden disabled title="Detener escaneo">Stop</button>' +
      '<button type="button" class="btn secondary" id="sc-export" title="Descarga JSON auditable de la última consulta">Exportar JSON</button>' +
      '<button type="button" class="btn secondary" id="sc-rank-b-btn" title="Evaluaciones DSR: aprobadas, rechazadas y fallidas">Ranking B</button>' +
      '<span class="mono" id="sc-status">—</span>' +
      "</div>" +
      '<details class="sc-more muted"><summary>Ayuda · tandas y multi-mercado</summary>' +
      '<p id="sc-hint" style="margin:0.35rem 0 0">' +
      "Cantidad / Todas / puntual = monedas scoreadas. Top y Top Kronos editables (incluso 1). Multi-mercado = Comparar + ranking por mercado. " +
      "A3/HL = futuros. ML ranking ON: cada Validar alimenta el modelo. Exportá el JSON para auditoría de terceros." +
      "</p></details>" +
      '<div id="sc-warn"></div>' +
      '<div id="sc-out"></div>' +
      '<div id="sc-detail" class="sc-detail" style="margin-top:0.45rem"></div>' +
      '<div id="sc-rank-b" class="sc-rank-b muted" style="margin-top:0.6rem;font-size:1.02em"></div>' +
      "</div>";

    var lastScan = null;
    var lastRequest = null;
    var selectedIdx = 0;
    /** Índice del bloque by_venue activo (multi). */
    var activeVenueIdx = 0;
    /** Vista multi: "compare" | "venue". */
    var multiView = "compare";
    /** Layout comparar: "grouped" | "flat". */
    var compareLayout = "grouped";
    /** Underlyings expandidos en vista agrupada. */
    var compareExpanded = {};
    /** Catálogo de monedas para typeahead (Moneda puntual). */
    var coinsCache = [];
    var coinSuggestIdx = -1;
    var coinLoadToken = 0;

    function scanMode() {
      var el = root.querySelector("#sc-scan-mode");
      return el && el.value === "pairwise" ? "pairwise" : "individual";
    }

    function selectedPairwiseDetectors() {
      return Array.prototype.slice
        .call(root.querySelectorAll(".sc-pw-det:checked"))
        .map(function (cb) {
          return cb.value;
        });
    }

    function syncScanModeUI() {
      var pw = scanMode() === "pairwise";
      var pwRow = root.querySelector("#sc-pairwise-row");
      var kroRow = root.querySelector("#sc-kronos-row");
      var prof = root.querySelector("#sc-profile");
      var profLbl = prof && prof.closest("label");
      if (pwRow) pwRow.hidden = !pw;
      if (kroRow) kroRow.hidden = pw;
      if (profLbl) profLbl.hidden = pw;
      if (pw) {
        root.querySelector("#sc-source").value = "real";
        Array.prototype.forEach.call(
          root.querySelectorAll(".sc-venue-cb"),
          function (cb) {
            cb.checked = cb.value === "binance";
            cb.disabled = cb.value !== "binance";
          }
        );
        var kl = root.querySelector("#sc-klines");
        if (kl && windowMode() === "klines") {
          var n = parseInt(kl.value, 10) || 720;
          if (n < 120) kl.value = "720";
        }
      } else {
        Array.prototype.forEach.call(
          root.querySelectorAll(".sc-venue-cb"),
          function (cb) {
            cb.disabled = false;
          }
        );
      }
      syncSourceUI();
    }

    function renderPairwiseTable(data, outEl) {
      var signals = data.signals || [];
      if (!signals.length) {
        outEl.innerHTML =
          '<p class="muted">Sin señales pairwise. Probá más monedas o más velas (≥120).</p>';
        return;
      }
      var valMap = {};
      (data.validation || []).forEach(function (v) {
        valMap[v.signal_id] = v;
      });
      var rows = signals
        .map(function (sig, i) {
          var syms = sig.symbols || [];
          var val = valMap[sig.signal_id];
          var rec = sig.recommended_strategy || {};
          var stratLabel = rec.label || rec.strategy_id || "—";
          var valTxt = val
            ? "SR=" +
              Number(val.sharpe_net || 0).toFixed(2) +
              " DSR=" +
              Number(val.deflated_sharpe || 0).toFixed(2) +
              (val.validated ? " ✓" : "")
            : "—";
          return (
            '<tr class="sc-row sc-pw-row" data-idx="' +
            i +
            '">' +
            "<td>" +
            esc(i + 1) +
            "</td>" +
            "<td class=\"mono\">" +
            esc(syms[0] || "—") +
            "</td>" +
            "<td class=\"mono\">" +
            esc(syms[1] || "—") +
            "</td>" +
            "<td>" +
            esc(sig.signal_type || "—") +
            "</td>" +
            "<td class=\"mono\">" +
            esc(sig.lag != null ? sig.lag : "—") +
            "</td>" +
            "<td class=\"mono\">" +
            esc(
              sig.normalized_score != null
                ? Number(sig.normalized_score).toFixed(3)
                : Number(sig.raw_score || 0).toFixed(3)
            ) +
            "</td>" +
            "<td class=\"mono\">" +
            esc(
              sig.confidence != null
                ? Number(sig.confidence).toFixed(3)
                : "—"
            ) +
            "</td>" +
            "<td>" +
            esc(stratLabel) +
            "</td>" +
            "<td class=\"mono muted\">" +
            esc(valTxt) +
            "</td>" +
            '<td><button type="button" class="btn secondary sc-pw-sim" data-idx="' +
            i +
            '">Sim</button></td>' +
            "</tr>"
          );
        })
        .join("");
      var venueLabel = (data.venue || "binance") + "/" + (data.market_type || "spot");
      outEl.innerHTML =
        '<p class="muted sc-meta">' +
        '<span class="data-badge data-badge-real">pairwise · ' +
        esc(venueLabel) +
        '</span> ' +
        "señales=" +
        esc(data.n_signals != null ? data.n_signals : signals.length) +
        " · símbolos=" +
        esc(data.n_symbols != null ? data.n_symbols : "—") +
        " · trials=" +
        esc(data.trial_count != null ? data.trial_count : "—") +
        " · TF=" +
        esc(data.interval || root.querySelector("#sc-interval").value) +
        "</p>" +
        '<table class="mono sc-pw-table" style="width:100%;border-collapse:collapse">' +
        "<thead><tr><th>#</th><th>Pierna A</th><th>Pierna B</th><th>Tipo</th>" +
        "<th>Lag</th><th>Score</th><th>Conf.</th><th>Estrategia</th><th>Validación</th><th></th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table>" +
        '<p class="muted" style="margin-top:0.45rem;font-size:1.02em">' +
        esc(data.note || "Candidatos de investigación — no implica rentabilidad.") +
        "</p>";
      outEl.querySelectorAll(".sc-pw-sim").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.stopPropagation();
          var idx = parseInt(btn.getAttribute("data-idx"), 10) || 0;
          var sig = signals[idx];
          if (!sig || !sig.symbols || sig.symbols.length < 2) return;
          var rec = sig.recommended_strategy || {};
          var mt = data.market_type || root.querySelector("#sc-market").value || "spot";
          openSim({
            source_module: "alpha_scanner_pairwise",
            venue: data.venue || "binance",
            market_type: mt,
            interval: data.interval || root.querySelector("#sc-interval").value,
            underlyings: sig.symbols.map(function (s) {
              return String(s).replace(/^[^:]+:/, "");
            }),
            pair_signal_type: sig.signal_type,
            strategy_id: rec.strategy_id || "pairs_trading",
          });
        });
      });
      outEl.querySelectorAll(".sc-pw-row").forEach(function (tr) {
        tr.addEventListener("click", function () {
          outEl.querySelectorAll(".sc-pw-row").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          var idx = parseInt(tr.getAttribute("data-idx"), 10) || 0;
          renderPairwiseDetail(signals[idx], data);
        });
      });
      if (signals[0]) renderPairwiseDetail(signals[0], data);
    }

    function renderPairwiseDetail(sig, data) {
      var det = root.querySelector("#sc-detail");
      if (!sig) {
        det.innerHTML = "";
        return;
      }
      var meta = sig.metadata || {};
      var rec = sig.recommended_strategy || {};
      var lines = [
        "PAIRWISE — " + (sig.signal_type || "?"),
        "Par: " + (sig.symbols || []).join(" / "),
        "Score raw: " + (sig.raw_score != null ? sig.raw_score : "—"),
        "Lag: " + (sig.lag != null ? sig.lag : "—"),
        "Lookback: " + (sig.lookback != null ? sig.lookback : "—"),
        "Estrategia sugerida: " + (rec.label || rec.strategy_id || "—"),
        "Rationale: " + (rec.rationale || "—"),
        "Hedge ratio: " + (meta.hedge_ratio != null ? meta.hedge_ratio : "—"),
        "ADF p-value: " + (meta.adf_pvalue != null ? meta.adf_pvalue : "—"),
        "Spread z: " + (meta.spread_z != null ? meta.spread_z : "—"),
        "Costo est. (bps): " + (meta.estimated_cost_bps != null ? meta.estimated_cost_bps : "—"),
      ];
      det.innerHTML =
        '<pre class="mono muted" style="white-space:pre-wrap;margin:0;font-size:1.02em">' +
        esc(lines.join("\n")) +
        "</pre>";
    }

    function setStatus(ok, msg) {
      var el = root.querySelector("#sc-status");
      el.textContent = msg;
      el.className =
        "mono " + (ok ? "status-ok" : ok === false ? "status-bad" : "muted");
    }

    function selectedVenues() {
      return Array.prototype.slice
        .call(root.querySelectorAll(".sc-venue-cb:checked"))
        .map(function (cb) {
          return cb.value;
        });
    }

    function windowMode() {
      return root.querySelector("#sc-window-mode").value;
    }

    function syncWindowModeUI() {
      var byPeriod = windowMode() === "period";
      root.querySelector("#sc-period-wrap").hidden = !byPeriod;
      root.querySelector("#sc-klines-wrap").hidden = byPeriod;
      refreshNBars();
    }

    function universeMode() {
      var el = root.querySelector("#sc-limit-mode");
      return el ? el.value : "n";
    }

    function syncUniverseUI() {
      var mode = universeMode();
      var custom = mode === "custom";
      var byCount = mode === "n";
      var wrap = root.querySelector("#sc-coin-wrap");
      if (wrap) wrap.hidden = !custom;
      var nWrap = root.querySelector("#sc-limit-n-wrap");
      if (nWrap) nWrap.hidden = !byCount;
      var kroTop = root.querySelector("#sc-kronos-top");
      if (kroTop) {
        kroTop.disabled = false;
        if (custom) {
          var nCoins = parseCustomCoins().length || 1;
          // Sugerir Top Kronos = monedas pedidas, pero editable.
          if (!kroTop.dataset.userEdited) {
            kroTop.value = String(Math.max(1, nCoins));
          }
          kroTop.title =
            "Kronos sobre las monedas puntuales (editable; sugerido = " +
            nCoins +
            ")";
        } else {
          kroTop.title = "A cuántas monedas del ranking aplicar Kronos (1–100)";
        }
      }
      if (custom) {
        loadCoinCatalog();
        var inp = root.querySelector("#sc-coin");
        if (inp) {
          if (!inp.value) inp.focus();
          openCoinSuggest();
        }
      } else {
        closeCoinSuggest();
      }
    }


    function parseCustomCoins() {
      var raw = (root.querySelector("#sc-coin").value || "").trim();
      if (!raw) return [];
      return raw
        .split(/[,;\s]+/)
        .map(function (x) {
          return x.trim().toUpperCase().replace(/^\$/, "");
        })
        .filter(function (x) {
          return x.length > 0;
        })
        .filter(function (x, i, arr) {
          return arr.indexOf(x) === i;
        });
    }

    function loadCoinCatalog() {
      if (!QLApi.simUniverse) {
        coinsCache = [
          { id: "BTC", name: "Bitcoin", label: "Bitcoin (BTC)" },
          { id: "ETH", name: "Ethereum", label: "Ethereum (ETH)" },
          { id: "SOL", name: "Solana", label: "Solana (SOL)" },
        ];
        return;
      }
      var token = ++coinLoadToken;
      var mt = root.querySelector("#sc-market").value || "spot";
      QLApi.simUniverse({ market_type: mt, hl_live: true })
        .then(function (d) {
          if (token !== coinLoadToken) return;
          var map = {};
          (d.coins || []).forEach(function (c) {
            if (!c || !c.id) return;
            map[String(c.id).toUpperCase()] = {
              id: String(c.id).toUpperCase(),
              name: c.name || c.id,
              label: c.label || c.name || c.id,
            };
          });
          var pbv = d.products_by_venue || {};
          Object.keys(pbv).forEach(function (vid) {
            (pbv[vid] || []).forEach(function (p) {
              var id = String(p.id || p.underlying || "")
                .toUpperCase()
                .replace(/[-/]/g, "")
                .replace(/(USDT|USD|USDC|PERP)$/i, "");
              if (!id || id.length > 12) return;
              if (!map[id]) {
                map[id] = {
                  id: id,
                  name: p.name || id,
                  label: p.label || p.name || id,
                };
              }
            });
          });
          coinsCache = Object.keys(map)
            .sort()
            .map(function (k) {
              return map[k];
            });
          if (
            universeMode() === "custom" &&
            document.activeElement === root.querySelector("#sc-coin")
          ) {
            openCoinSuggest();
          }
        })
        .catch(function () {
          if (token !== coinLoadToken) return;
          if (!coinsCache.length) {
            coinsCache = [
              { id: "BTC", name: "Bitcoin", label: "Bitcoin (BTC)" },
              { id: "ETH", name: "Ethereum", label: "Ethereum (ETH)" },
            ];
          }
        });
    }

    function currentCoinQuery() {
      var raw = root.querySelector("#sc-coin").value || "";
      var parts = raw.split(/[,;\s]+/);
      return foldText(parts[parts.length - 1] || "");
    }

    function filteredCoins(q) {
      var list = coinsCache.slice();
      if (!q) {
        var prefer = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "NEAR"];
        list.sort(function (a, b) {
          var ia = prefer.indexOf(a.id);
          var ib = prefer.indexOf(b.id);
          if (ia >= 0 || ib >= 0) {
            if (ia < 0) return 1;
            if (ib < 0) return -1;
            return ia - ib;
          }
          return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
        });
        return list.slice(0, 14);
      }
      return list
        .filter(function (c) {
          var hay = foldText([c.id, c.name, c.label].join(" "));
          return hay.indexOf(q) >= 0;
        })
        .slice(0, 14);
    }

    function closeCoinSuggest() {
      var box = root.querySelector("#sc-coin-suggest");
      if (box) box.hidden = true;
      coinSuggestIdx = -1;
    }

    function openCoinSuggest() {
      var wrap = root.querySelector("#sc-coin-wrap");
      if (!wrap || wrap.hidden) {
        closeCoinSuggest();
        return;
      }
      var box = root.querySelector("#sc-coin-suggest");
      if (!box) return;
      var q = currentCoinQuery();
      var matches = filteredCoins(q);
      coinSuggestIdx = -1;
      if (!matches.length) {
        box.innerHTML =
          '<li class="sc-coin-empty muted">Sin coincidencias en el catálogo. ' +
          "Podés escribir el ticker igual (ej. BTC).</li>";
        box.hidden = false;
        return;
      }
      box.innerHTML = matches
        .map(function (c, i) {
          return (
            '<li role="option" data-idx="' +
            i +
            '"><button type="button" data-id="' +
            esc(c.id) +
            '"><span class="sc-coin-id">' +
            esc(c.id) +
            '</span><span class="sc-coin-name">' +
            esc(c.name || c.label || "") +
            "</span></button></li>"
          );
        })
        .join("");
      box.querySelectorAll("button").forEach(function (btn) {
        btn.addEventListener("mousedown", function (ev) {
          ev.preventDefault();
          pickCoin(btn.getAttribute("data-id"));
        });
      });
      box.hidden = false;
    }

    function pickCoin(id) {
      if (!id) return;
      var inp = root.querySelector("#sc-coin");
      var raw = inp.value || "";
      var endsWithSep = /[,;\s]$/.test(raw);
      var parts = raw.trim()
        ? raw
            .trim()
            .split(/[,;\s]+/)
            .filter(Boolean)
        : [];
      if (parts.length && !endsWithSep) {
        parts[parts.length - 1] = id;
      } else {
        parts.push(id);
      }
      var uniq = [];
      parts.forEach(function (p) {
        var u = String(p).toUpperCase();
        if (u && uniq.indexOf(u) < 0) uniq.push(u);
      });
      inp.value = uniq.join(", ");
      closeCoinSuggest();
      inp.focus();
    }

    function syncSourceUI() {
      var synth = root.querySelector("#sc-source").value === "synthetic";
      [
        "#sc-market",
        "#sc-interval",
        "#sc-profile",
        "#sc-limit-mode",
        "#sc-limit-n",
        "#sc-top",
        "#sc-kronos-top",
        "#sc-klines",
        "#sc-period",
        "#sc-window-mode",
        "#sc-coin",
      ].forEach(function (sel) {
        var el = root.querySelector(sel);
        if (el) el.disabled = synth;
      });
      root.querySelectorAll(".sc-venue-cb").forEach(function (cb) {
        cb.disabled = synth;
      });
      root.querySelector("#sc-hint").textContent = synth
        ? "Demo local WB:A/B/C (sin red). Para mercados reales elegí «MD real»."
        : "Cantidad libre de monedas (N), Todas, o puntual. Top y Top Kronos también editables (podés poner 1).";
      syncUniverseUI();
    }

    function estimateBarsLocal(days, interval) {
      var mins = INTERVAL_MINUTES[interval] || 60;
      var n = Math.floor((Number(days) * 1440) / mins);
      return n < 1 ? 1 : n;
    }

    function periodLabel() {
      var sel = root.querySelector("#sc-period");
      if (!sel || sel.selectedIndex < 0) return String(sel && sel.value) || "—";
      return sel.options[sel.selectedIndex].text || String(sel.value);
    }

    function refreshNBars() {
      var el = root.querySelector("#sc-nbars");
      if (!el) return;
      if (windowMode() === "klines") {
        var nK = parseInt(root.querySelector("#sc-klines").value, 10) || 0;
        el.textContent =
          "≈ " + nK.toLocaleString("es-AR") + " velas · N fijo";
        el.title =
          "Modo N velas: el scanner pide exactamente esas barras (TF elegido).";
        return;
      }
      var days = parseInt(root.querySelector("#sc-period").value, 10) || 30;
      var iv = root.querySelector("#sc-interval").value || "1h";
      var n = estimateBarsLocal(days, iv);
      var pl = periodLabel();
      el.textContent =
        "≈ " +
        n.toLocaleString("es-AR") +
        " velas · " +
        pl +
        " × " +
        iv;
      el.title =
        "Horizonte «" +
        pl +
        "» con velas de " +
        iv +
        " → se pedirán ~" +
        n.toLocaleString("es-AR") +
        " barras por símbolo.";
      /* Mantener el input N alineado por si el usuario cambia a modo velas. */
      var klines = root.querySelector("#sc-klines");
      if (klines) {
        klines.value = String(Math.min(Math.max(n, 10), 525600));
      }
      if (!QLApi.simPeriod) return;
      QLApi.simPeriod(days, iv)
        .then(function (d) {
          if (windowMode() !== "period") return;
          if (d.n_bars != null) {
            el.textContent =
              (d.n_bars_display ||
                "≈ " + Number(d.n_bars).toLocaleString("es-AR") + " velas") +
              " · " +
              pl +
              " × " +
              iv;
          }
          el.title =
            (d.note ? d.note + "\n" : "") +
            "Horizonte «" +
            pl +
            "» × " +
            iv +
            " → ~" +
            (d.n_bars != null ? d.n_bars : n) +
            " barras.";
          if (klines && d.n_bars != null) {
            klines.value = String(
              Math.min(Math.max(Number(d.n_bars) || n, 10), 525600)
            );
          }
        })
        .catch(function () {});
    }

    function openSim(prefill) {
      if (global.QLShell && typeof QLShell.open === "function") {
        QLShell.open("simulator", { prefill: prefill || {} });
      }
    }

    function activeScanBlock() {
      if (
        lastScan &&
        lastScan.by_venue &&
        lastScan.by_venue.length &&
        lastScan.by_venue[activeVenueIdx]
      ) {
        return lastScan.by_venue[activeVenueIdx];
      }
      return lastScan;
    }

    function normalizeUnd(s) {
      return String(s == null ? "" : s)
        .trim()
        .toUpperCase();
    }

    function fmtScore(v) {
      if (v == null || v === "") return null;
      var n = Number(v);
      return isFinite(n) ? n : null;
    }

    function buildScannerMemo(row, block) {
      var und =
        (row && (row.underlying || row.symbol || row.instrument_id)) || "?";
      var venue = (block && block.venue) || (lastScan && lastScan.venue) || "?";
      var mt =
        (block && block.market_type) ||
        (lastScan && lastScan.market_type) ||
        "?";
      var profile =
        (block && block.profile) || (lastScan && lastScan.profile) || "?";
      var kroMeta =
        (block && block.kronos) || (lastScan && lastScan.kronos) || {};
      var trad = fmtScore(row.traditional_score);
      if (trad == null) trad = fmtScore(row.composite);
      var kro = fmtScore(row.kronos_score);
      var fin = fmtScore(row.final_score);
      if (fin == null) fin = fmtScore(row.composite);
      var km = row.kronos_metrics || {};
      var rec = row.recommendation || {};
      var lines = [
        "QUANTLAB — MEMORANDO ALPHA SCANNER + KRONOS",
        "==========================================",
        "Moneda: " + und,
        "Venue: " + venue + "/" + mt,
        "Perfil / rama: " + profile,
        "Intervalo: " + ((block && block.interval) || "?"),
        "",
        "SCORES",
        "------",
        "Tradicional: " + (trad != null ? trad.toFixed(4) : "null"),
        "Kronos:      " + (kro != null ? kro.toFixed(4) : "null (no aplicado)"),
        "Final:       " + (fin != null ? fin.toFixed(4) : "null"),
        "Peso Kronos: " + (row.kronos_weight != null ? row.kronos_weight : "—"),
        "Aplicado:    " + (row.kronos_applied ? "sí" : "no"),
        "Skip reason: " + (row.kronos_skip_reason || "—"),
        "",
        "MÉTRICAS KRONOS (forecast de contexto; NO rentabilidad)",
        "------------------------------------------------------",
        "Volatilidad futura: " +
          (km.kronos_forecast_volatility != null
            ? Number(km.kronos_forecast_volatility).toFixed(6)
            : "null"),
        "Dispersión:         " +
          (km.kronos_forecast_dispersion != null
            ? Number(km.kronos_forecast_dispersion).toFixed(6)
            : "null"),
        "Riesgo ruptura:     " +
          (km.kronos_breakout_risk != null
            ? Number(km.kronos_breakout_risk).toFixed(4)
            : "null"),
        "Riesgo tendencia:   " +
          (km.kronos_trend_risk != null
            ? Number(km.kronos_trend_risk).toFixed(4)
            : "null"),
        "Prob. rango:        " +
          (km.kronos_range_probability != null
            ? Number(km.kronos_range_probability).toFixed(4)
            : "null"),
        "Estabilidad:        " +
          (km.kronos_regime_stability != null
            ? Number(km.kronos_regime_stability).toFixed(4)
            : "null"),
        "Confianza (acuerdo):" +
          (km.kronos_confidence != null
            ? Number(km.kronos_confidence).toFixed(4)
            : "null"),
        "  ⚠ confianza ≠ probabilidad calibrada",
        "MM score:           " +
          (km.kronos_market_making_score != null
            ? Number(km.kronos_market_making_score).toFixed(4)
            : "null"),
        "Horizonte (velas):  " + (row.kronos_horizon != null ? row.kronos_horizon : "—"),
        "",
        "META ESCANEADO KRONOS",
        "---------------------",
        "status: " + (kroMeta.status || "ausente"),
        "model: " + (kroMeta.model || "—"),
        "device: " + (kroMeta.device_resolved || kroMeta.device || "—"),
        "lookback: " + (kroMeta.lookback != null ? kroMeta.lookback : "—"),
        "pred_len: " + (kroMeta.pred_len != null ? kroMeta.pred_len : "—"),
        "samples: " + (kroMeta.sample_count != null ? kroMeta.sample_count : "—"),
        "applied_count: " +
          (kroMeta.applied_count != null ? kroMeta.applied_count : "—"),
        "failed_count: " +
          (kroMeta.failed_count != null ? kroMeta.failed_count : "—"),
        "inference_ms: " +
          (kroMeta.inference_ms_total != null
            ? Math.round(kroMeta.inference_ms_total)
            : "—"),
        "",
        "EXPLICACIÓN",
        "-----------",
        row.kronos_explanation ||
          rec.text ||
          "Sin explicación Kronos (ranking tradicional).",
        "",
        "Estrategia compatible a probar: " +
          (row.compatible_strategy ||
            rec.family_label_es ||
            rec.family ||
            profile),
        "",
        "LIMITACIONES",
        "------------",
        "- Kronos no garantiza rentabilidad.",
        "- No reemplaza backtest ni Monte Carlo.",
        "- No conoce el libro de órdenes (solo OHLCV).",
        "- Resultados = forecast de contexto, no certezas.",
      ];
      var csv =
        "campo,valor\n" +
        [
          ["moneda", und],
          ["venue", venue + "/" + mt],
          ["perfil", profile],
          ["traditional_score", trad],
          ["kronos_score", kro],
          ["final_score", fin],
          ["kronos_breakout_risk", km.kronos_breakout_risk],
          ["kronos_forecast_volatility", km.kronos_forecast_volatility],
          ["kronos_regime_stability", km.kronos_regime_stability],
          ["kronos_confidence", km.kronos_confidence],
          ["kronos_status", kroMeta.status],
        ]
          .map(function (p) {
            return p[0] + "," + (p[1] == null ? "" : String(p[1]));
          })
          .join("\n");
      return {
        kind: "scanner",
        title: "Memorando · Scanner " + und,
        text: lines.join("\n"),
        csv: csv,
        filenameBase:
          "quantlab-scanner-" +
          String(und).replace(/[^\w.-]+/g, "_") +
          "-" +
          Date.now().toString(36),
        nRows: 11,
      };
    }

    function openScannerMemoForRow(row) {
      var block = activeScanBlock() || lastScan || {};
      var memo = buildScannerMemo(row || {}, block);
      if (global.QLSimRegistry && typeof global.QLSimRegistry.add === "function") {
        global.QLSimRegistry.add({
          kind: "scanner",
          title: memo.title,
          summary: (row && (row.underlying || row.symbol)) || "scan",
          params: lastRequest || {},
          memo: memo,
        });
      }
      if (
        global.QLSimRegistry &&
        typeof global.QLSimRegistry.openMemo === "function"
      ) {
        global.QLSimRegistry.openMemo(memo, lastRequest || {});
      } else {
        window.alert(memo.text.slice(0, 1500));
      }
    }

    function scoreComposite(s) {
      if (!s) return null;
      if (s.final_score != null) return Number(s.final_score);
      if (s.composite != null) return Number(s.composite);
      if (s.base_score != null) return Number(s.base_score);
      return null;
    }

    function scoreFamily(s) {
      if (!s || !s.recommendation) return "—";
      return (
        s.recommendation.family_label_es ||
        s.recommendation.family ||
        "—"
      );
    }

    /** Agrupa scores multi-venue por underlying; orden = ranking del venue principal. */
    function buildCompareGroups(data) {
      var venues = (data && data.by_venue) || [];
      var byUnd = {};
      venues.forEach(function (block, vIdx) {
        (block.scores || []).forEach(function (s, sIdx) {
          var und = normalizeUnd(
            s.underlying || s.symbol || s.instrument_id
          );
          if (!und) return;
          if (!byUnd[und]) byUnd[und] = [];
          byUnd[und].push({
            venue: block.venue || "?",
            market_type: block.market_type || "",
            row: s,
            rank: sIdx + 1,
            venueIdx: vIdx,
            scoreIdx: sIdx,
            composite: scoreComposite(s),
          });
        });
      });
      var ordered = [];
      var seen = {};
      var primary = venues[0];
      if (primary && primary.scores) {
        primary.scores.forEach(function (s) {
          var und = normalizeUnd(
            s.underlying || s.symbol || s.instrument_id
          );
          if (!und || seen[und]) return;
          seen[und] = true;
          ordered.push({ underlying: und, entries: byUnd[und] });
        });
      }
      Object.keys(byUnd)
        .sort()
        .forEach(function (und) {
          if (seen[und]) return;
          ordered.push({ underlying: und, entries: byUnd[und] });
        });
      return ordered;
    }

    function primaryEntry(group) {
      if (!group || !group.entries || !group.entries.length) return null;
      for (var i = 0; i < group.entries.length; i++) {
        if (group.entries[i].venueIdx === 0) return group.entries[i];
      }
      return group.entries[0];
    }

    function selectCompareEntry(entry) {
      if (!entry) return;
      activeVenueIdx = entry.venueIdx;
      renderDetail(entry.scoreIdx);
    }

    function renderDetail(idx) {
      var box = root.querySelector("#sc-detail");
      var block = activeScanBlock();
      if (!block || !block.scores || !block.scores.length) {
        box.innerHTML = "";
        return;
      }
      selectedIdx = Math.max(0, Math.min(idx, block.scores.length - 1));
      var row = block.scores[selectedIdx];
      var rec = row.recommendation || block.recommendations || {};
      var explained = rec.score_explained || row.score_explained || null;
      var venue = block.venue || (lastScan && lastScan.venue) || "binance";
      var mt = block.market_type || (lastScan && lastScan.market_type) || "spot";
      var und =
        row.underlying ||
        (block.selected_underlyings || [])[selectedIdx] ||
        "";
      var iv = block.interval || (lastScan && lastScan.interval) || "1h";
      var comp =
        row.composite != null
          ? Number(row.composite)
          : row.base_score != null
            ? Number(row.base_score)
            : null;

      var stratChips = (rec.strategies || [])
        .map(function (s) {
          return (
            '<button type="button" class="btn secondary sc-chip" data-kind="strategy" data-id="' +
            esc(s.id) +
            '" title="' +
            esc(s.runnable ? "runnable" : "stub") +
            '">' +
            esc(s.name || s.id) +
            (s.runnable ? "" : " · stub") +
            "</button>"
          );
        })
        .join(" ");

      var tfChips = (rec.timeframes || [])
        .map(function (t) {
          return (
            '<button type="button" class="btn secondary sc-chip" data-kind="tf" data-id="' +
            esc(t.interval) +
            '">' +
            esc(t.interval) +
            (t.primary ? " ★" : "") +
            "</button>"
          );
        })
        .join(" ");

      var factorLis = ((explained && explained.factors) || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      var nextLis = ((explained && explained.next_steps) || [])
        .map(function (x) {
          return "<li>" + esc(x) + "</li>";
        })
        .join("");
      var band = (explained && explained.band) || {};
      var tradD = fmtScore(row.traditional_score);
      if (tradD == null) tradD = fmtScore(row.composite);
      var kroD = fmtScore(row.kronos_score);
      var finD = fmtScore(row.final_score);
      if (finD == null) finD = comp;
      var km = row.kronos_metrics || {};
      var scoreBlock =
        '<div class="sc-score-explain" style="margin:0 0 0.65rem;padding:0.55rem 0.65rem;' +
        "border-left:3px solid var(--amber-dim,#a67c3a);" +
        'background:rgba(212,140,50,0.07);border-radius:0 6px 6px 0">' +
        '<p style="margin:0 0 0.35rem"><strong>Final ' +
        esc(finD != null ? finD.toFixed(2) : "—") +
        "</strong>" +
        (finD != null ? " (" + esc((finD * 100).toFixed(1)) + " pts)" : "") +
        " · Trad " +
        esc(tradD != null ? tradD.toFixed(2) : "—") +
        " · Kronos " +
        esc(kroD != null ? kroD.toFixed(2) : "—") +
        (band.title ? " · " + esc(band.title) : "") +
        " · " +
        esc(venue) +
        "/" +
        esc(mt) +
        "</p>" +
        '<p class="muted" style="margin:0 0 0.35rem;font-size:1.10em">' +
        esc(
          row.kronos_explanation ||
            (explained && explained.headline) ||
            rec.text ||
            ""
        ) +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:1.10em">' +
        "Ruptura " +
        esc(
          km.kronos_breakout_risk != null
            ? Number(km.kronos_breakout_risk).toFixed(2)
            : "—"
        ) +
        " · Vol futura " +
        esc(
          km.kronos_forecast_volatility != null
            ? Number(km.kronos_forecast_volatility).toFixed(4)
            : "—"
        ) +
        " · Estabilidad " +
        esc(
          km.kronos_regime_stability != null
            ? Number(km.kronos_regime_stability).toFixed(2)
            : "—"
        ) +
        " · Confianza " +
        esc(
          km.kronos_confidence != null
            ? Number(km.kronos_confidence).toFixed(2)
            : "—"
        ) +
        " <span class=\"muted\">(acuerdo, no calibrada)</span></p>" +
        '<p style="margin:0 0 0.35rem;font-size:1.10em"><strong>¿Qué es este número?</strong><br>' +
        esc(
          (explained && explained.what_is) ||
            "Va de 0 a 1: compara esta moneda con las otras del scan para la rama elegida. No es rentabilidad."
        ) +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:1.10em"><strong>¿Por qué en esta rama?</strong><br>' +
        esc((explained && explained.family_why) || "") +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:1.10em"><strong>Esta banda</strong><br>' +
        esc(band.why || "") +
        "</p>" +
        '<p class="muted" style="margin:0 0 0.35rem;font-size:1.06em">' +
        esc(
          (explained && explained.ranges_help) ||
            "0.50–0.99 ≈ rangos útiles para probar; ≥0.75 mejor ajuste."
        ) +
        "</p>" +
        (factorLis
          ? "<p style=\"margin:0 0 0.2rem;font-size:1.10em\"><strong>Factores que arman el score</strong></p>" +
            '<ul style="margin:0 0 0.45rem 1.1rem;padding:0;font-size:1.08em">' +
            factorLis +
            "</ul>"
          : "") +
        (nextLis
          ? "<p style=\"margin:0 0 0.2rem;font-size:1.10em\"><strong>Qué hacer ahora</strong></p>" +
            '<ol style="margin:0 0 0.25rem 1.1rem;padding:0;font-size:1.08em">' +
            nextLis +
            "</ol>"
          : "") +
        '<p class="muted" style="margin:0 0 0.35rem;font-size:1.04em">' +
        esc((explained && explained.note) || "Score ≠ rentabilidad. LIVE bloqueado.") +
        "</p>" +
        '<button type="button" class="btn secondary" id="sc-open-memo">Ver memorando Kronos</button>' +
        "</div>";

      box.innerHTML =
        '<div class="pane-section" style="border:1px solid var(--border,#333);border-radius:8px;padding:0.55rem 0.7rem">' +
        "<h4 style=\"margin:0 0 0.35rem\">Detalle del score · " +
        esc(und || row.instrument_id) +
        " · " +
        esc(rec.family_label_es || rec.family || "—") +
        "</h4>" +
        scoreBlock +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem;margin-bottom:0.35rem">' +
        "<span class=\"muted\">Estrategias</span> " +
        (stratChips || "—") +
        "</div>" +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem;margin-bottom:0.45rem">' +
        "<span class=\"muted\">Timeframes</span> " +
        (tfChips || "—") +
        "</div>" +
        '<button type="button" class="btn" id="sc-open-sim">Abrir en Simulador</button> ' +
        '<button type="button" class="btn secondary" id="sc-validate-one" title="1 estrategia · DSR · registra trial siempre">Validar</button> ' +
        '<button type="button" class="btn slt-launch-btn" id="sc-open-live-test">▶ Corrida en vivo</button>' +
        "</div>";

      box.querySelectorAll(".sc-chip").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var kind = btn.getAttribute("data-kind");
          var id = btn.getAttribute("data-id");
          var prefill = {
            venue: venue,
            market_type: mt,
            underlying: und,
            interval: iv,
          };
          if (kind === "strategy") prefill.strategy_id = id;
          if (kind === "tf") prefill.interval = id;
          if (!prefill.strategy_id && rec.strategies && rec.strategies[0]) {
            prefill.strategy_id = rec.strategies[0].id;
          }
          openSim(prefill);
        });
      });
      var openBtn = box.querySelector("#sc-open-sim");
      if (openBtn) {
        openBtn.addEventListener("click", function () {
          var prefill = {
            venue: venue,
            market_type: mt,
            underlying: und,
            interval: iv,
          };
          if (rec.strategies && rec.strategies[0]) {
            prefill.strategy_id = rec.strategies[0].id;
          }
          openSim(prefill);
        });
      }
      var valBtn = box.querySelector("#sc-validate-one");
      if (valBtn) {
        valBtn.addEventListener("click", function () {
          var strat =
            (rec.strategies && rec.strategies[0] && rec.strategies[0].id) ||
            "momentum";
          var signals = (block && block.signals) || (lastScan && lastScan.signals) || [];
          var sig = null;
          var iid = row.instrument_id || "";
          for (var si = 0; si < signals.length; si++) {
            var ss = signals[si].symbols || [];
            if (ss[0] === iid || String(ss[0] || "").indexOf(und) >= 0) {
              sig = signals[si];
              break;
            }
          }
          if (!sig) {
            setStatus(false, "sin AlphaSignal — re-escaneá (signals[] requerido)");
            return;
          }
          setStatus(null, "validando " + strat + "…");
          QLApi.validateCandidate({
            signal: sig,
            strategy_id: strat,
            venue: venue,
            market_type: mt,
            interval: iv,
            kline_limit:
              (block && block.kline_limit) ||
              (lastScan && lastScan.kline_limit) ||
              240,
            underlyings: und ? [und] : undefined,
            scan_id:
              (lastScan && lastScan.persisted && lastScan.persisted.scan_id) ||
              (lastScan && lastScan.scan_id) ||
              undefined,
          })
            .then(function (d) {
              var v = (d && d.validation) || {};
              setStatus(
                !!v.ok,
                "Validación · SR=" +
                  Number(v.sharpe_net || 0).toFixed(2) +
                  " DSR=" +
                  Number(v.deflated_sharpe || 0).toFixed(2) +
                  (v.validated ? " ✓ Ranking B" : " (no validada)")
              );
              loadRankingB();
            })
            .catch(function (e) {
              setStatus(false, (e && e.message) || String(e));
            });
        });
      }
      var liveBtn = box.querySelector("#sc-open-live-test");
      if (liveBtn) {
        liveBtn.addEventListener("click", function () {
          var scanId =
            (lastScan && lastScan.persisted && lastScan.persisted.scan_id) ||
            (lastScan && lastScan.scan_id) ||
            null;
          var prefill = {
            source_module: "alpha_scanner",
            scan_id: scanId,
            venue: venue,
            market_type: mt,
            underlying: und,
            symbol: und && String(und).toUpperCase().indexOf("USDT") >= 0
              ? String(und).toUpperCase()
              : String(und || "BTC").toUpperCase() + "USDT",
            interval: iv,
            score: row.score,
            profile: rec.family || rec.profile,
            strategies: rec.strategies,
            execution_destination: "PAPER",
            message:
              "Scanner · " +
              (und || row.instrument_id || "?") +
              " · " +
              (iv || "?") +
              " · score " +
              (row.score != null ? row.score : "—"),
          };
          if (rec.strategies && rec.strategies[0]) {
            prefill.strategy_id = rec.strategies[0].id;
          }
          if (global.QLShell && QLShell.open) {
            QLShell.open("strategy_live_test", { prefill: prefill });
          }
        });
      }
      var memoBtn = box.querySelector("#sc-open-memo");
      if (memoBtn) {
        memoBtn.addEventListener("click", function () {
          openScannerMemoForRow(row);
        });
      }
    }

    function renderWarnings(data) {
      var box = root.querySelector("#sc-warn");
      if (!box) return;
      var warns = (data && data.warnings) || [];
      var status = (data && data.score_status) || "ok";
      var kronosPop = ((data && data.kronos && data.kronos.popups) || []).slice();
      if (data && data.by_venue) {
        data.by_venue.forEach(function (b) {
          ((b.kronos && b.kronos.popups) || []).forEach(function (p) {
            kronosPop.push(p);
          });
        });
      }
      var wantKronos =
        root.querySelector("#sc-kronos-enabled") &&
        root.querySelector("#sc-kronos-enabled").checked;
      var hasKronosMeta =
        (data && data.kronos) ||
        (data &&
          data.by_venue &&
          data.by_venue.some(function (b) {
            return b && b.kronos;
          }));
      if (wantKronos && !hasKronosMeta) {
        kronosPop.unshift({
          id: "kronos_backend_stale",
          level: "warn",
          title: "Kronos no llegó del servidor",
          body:
            "La UI pidió Kronos pero la respuesta no trae bloque kronos. " +
            "Reiniciá el Workbench (el proceso viejo no aplica forecast) y hard-refresh (Ctrl+F5).",
        });
      }
      if (hasKronosMeta) {
        var km =
          (data && data.kronos) ||
          (data.by_venue && data.by_venue[0] && data.by_venue[0].kronos) ||
          {};
        if (km.status && km.status !== "applied") {
          kronosPop.unshift({
            id: "kronos_status",
            level: "info",
            title: "Kronos: " + km.status,
            body:
              "applied=" +
              (km.applied_count != null ? km.applied_count : "—") +
              " · failed=" +
              (km.failed_count != null ? km.failed_count : "—") +
              (km.skip_reason ? " · " + km.skip_reason : "") +
              ". Si Kronos=— en la tabla, no se mezcló al final.",
          });
        }
      }
      if (!warns.length && status === "ok" && !kronosPop.length) {
        box.innerHTML = "";
        return;
      }
      var lis = warns
        .map(function (w) {
          return "<li>" + esc(w) + "</li>";
        })
        .join("");
      var kLis = kronosPop
        .map(function (p) {
          return (
            "<li><strong>" +
            esc(p.title || "Kronos") +
            "</strong> — " +
            esc(p.body || "") +
            "</li>"
          );
        })
        .join("");
      box.innerHTML =
        '<div class="sc-warn"><strong>Aviso ranking</strong>' +
        (status && status !== "ok"
          ? ' · <span class="mono">' + esc(status) + "</span>"
          : "") +
        (lis ? "<ul>" + lis + "</ul>" : "") +
        (kLis ? "<strong>Kronos</strong><ul>" + kLis + "</ul>" : "") +
        "</div>";
    }

    function exportScanAudit() {
      if (!lastScan) {
        setStatus(false, "nada que exportar — escaneá primero");
        return;
      }
      var payload = {
        schema: "quantlab.alpha_scanner.audit.v1",
        exported_at: new Date().toISOString(),
        request: lastRequest,
        result: lastScan,
        note:
          "Paquete auditable de la última consulta Alpha Scanner. " +
          "Score ≠ rentabilidad. LIVE bloqueado.",
      };
      var text = JSON.stringify(payload, null, 2);
      var blob = new Blob([text], { type: "application/json;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      var stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      a.href = url;
      a.download = "quantlab-scanner-audit-" + stamp + ".json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus(true, "exportado");
    }

    function renderScoresTable(block, outEl) {
      if (!block || !block.scores || !block.scores.length) {
        outEl.innerHTML += '<p class="muted">Sin scores en este venue.</p>';
        return;
      }
      var degraded =
        block.score_status === "degraded" ||
        (block.warnings && block.warnings.length) ||
        (lastScan && lastScan.score_status === "degraded");
      var rowsHtml = block.scores
        .map(function (s, i) {
          var und = s.underlying || s.symbol || s.instrument_id;
          var finalN = fmtScore(s.final_score);
          if (finalN == null) finalN = fmtScore(s.composite);
          if (finalN == null) finalN = fmtScore(s.base_score);
          var tradN = fmtScore(s.traditional_score);
          if (tradN == null) tradN = fmtScore(s.composite);
          var kroN = fmtScore(s.kronos_score);
          var comp = finalN != null ? finalN.toFixed(2) : "—";
          var pts = finalN != null ? (finalN * 100).toFixed(1) : "—";
          var tradTxt = tradN != null ? tradN.toFixed(2) : "—";
          var kroTxt = kroN != null ? kroN.toFixed(2) : "—";
          var fam =
            (s.recommendation && s.recommendation.family_label_es) ||
            (s.recommendation && s.recommendation.family) ||
            s.compatible_strategy ||
            "—";
          var tied = s.score_status === "tied_zero" || (degraded && finalN === 0);
          var aviso = tied
            ? "empatado / sin discriminación"
            : s.kronos_explanation
              ? String(s.kronos_explanation)
              : s.score_reason
                ? String(s.score_reason)
                : "—";
          var km = s.kronos_metrics || {};
          var riskTxt =
            km.kronos_breakout_risk != null
              ? Number(km.kronos_breakout_risk).toFixed(2)
              : "—";
          return (
            '<tr class="sc-row' +
            (i === 0 ? " sc-row-sel" : "") +
            '" data-idx="' +
            i +
            '" style="cursor:pointer">' +
            "<td>" +
            (i + 1) +
            "</td>" +
            '<td class="mono">' +
            esc(und) +
            "</td>" +
            '<td class="mono sc-memo-cell" data-memo="1" title="Click = memorando">' +
            esc(tradTxt) +
            "</td>" +
            '<td class="mono sc-memo-cell" data-memo="1" title="Click = memorando Kronos">' +
            esc(kroTxt) +
            "</td>" +
            '<td class="mono sc-score-cell sc-memo-cell' +
            (tied ? " sc-score-tied" : "") +
            '" data-memo="1" title="' +
            esc(
              tied
                ? "Score empatado en 0 — ver avisos arriba"
                : "Click = memorando Trad/Kronos/Final"
            ) +
            '" style="text-decoration:underline;text-underline-offset:2px;' +
            (tied
              ? ""
              : "color:var(--amber,#d48c32)") +
            '">' +
            esc(comp) +
            " <span class=\"muted\">(" +
            esc(pts) +
            " pts)</span></td>" +
            "<td>" +
            esc(fam) +
            "</td>" +
            '<td class="mono muted" title="Riesgo de ruptura Kronos">' +
            esc(riskTxt) +
            "</td>" +
            '<td class="muted" style="font-size:0.92em">' +
            esc(aviso) +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      outEl.innerHTML +=
        '<p class="muted sc-meta">' +
        '<span class="data-badge data-badge-real">' +
        esc((block.venue || "lab") + "/" + (block.market_type || "—")) +
        "</span> " +
        "rama=" +
        esc(block.profile || "") +
        " · elegibles=" +
        esc(block.eligible) +
        " · TF=" +
        esc(block.interval || (lastScan && lastScan.interval) || "") +
        " · tanda=" +
        esc(
          block.universe_mode === "puntual"
            ? "puntual"
            : block.universe_mode === "custom"
              ? "custom"
              : block.universe_mode === "all"
                ? "todas"
                : block.symbol_limit != null
                  ? block.symbol_limit
                  : ""
        ) +
        (block.requested_underlyings && block.requested_underlyings.length
          ? " · pedido=" + esc(block.requested_underlyings.join(","))
          : "") +
        (block.n_universe != null ? " (" + esc(block.n_universe) + ")" : "") +
        " · fetched=" +
        esc(block.n_symbols_fetched != null ? block.n_symbols_fetched : block.fetched) +
        (block.md_meta && block.md_meta.provider
          ? " · md=" + esc(block.md_meta.provider)
          : "") +
        (block.kronos && block.kronos.status
          ? " · kronos=" + esc(block.kronos.status)
          : "") +
        (block.score_status && block.score_status !== "ok"
          ? " · <span class=\"sc-score-tied\">" +
            esc(block.score_status) +
            "</span>"
          : "") +
        "</p>" +
        '<table class="mono" style="width:100%;border-collapse:collapse">' +
        "<thead><tr><th>#</th><th>Moneda</th><th>Trad.</th><th>Kronos</th>" +
        "<th>Final (pts)</th><th>Estrategia a probar</th><th>Ruptura</th><th>Nota</th></tr></thead>" +
        "<tbody>" +
        rowsHtml +
        "</tbody></table>";
      outEl.querySelectorAll(".sc-row").forEach(function (tr) {
        tr.addEventListener("click", function (ev) {
          outEl.querySelectorAll(".sc-row").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          var idx = parseInt(tr.getAttribute("data-idx"), 10) || 0;
          renderDetail(idx);
          if (
            ev.target &&
            ev.target.closest &&
            ev.target.closest(".sc-memo-cell")
          ) {
            var row = (block.scores || [])[idx];
            if (row) openScannerMemoForRow(row);
          }
        });
      });
    }

    function renderProposalBlock(prop, title) {
      if (!prop || !prop.auto_mode) return "";
      var stratChips = (prop.strategies || [])
        .map(function (s) {
          return (
            '<button type="button" class="btn secondary sc-chip sc-proposal-chip" data-kind="strategy" data-id="' +
            esc(s.id) +
            '">' +
            esc(s.name || s.id) +
            (s.runnable ? "" : " · stub") +
            "</button>"
          );
        })
        .join(" ");
      var tfChips = (prop.timeframes || [])
        .map(function (t) {
          return (
            '<button type="button" class="btn secondary sc-chip sc-proposal-chip" data-kind="tf" data-id="' +
            esc(t.interval) +
            '">' +
            esc(t.interval) +
            (t.primary ? " ★" : "") +
            "</button>"
          );
        })
        .join(" ");
      var votes = prop.votes || {};
      var voteTxt = Object.keys(votes)
        .map(function (k) {
          return k + "×" + votes[k];
        })
        .join(" · ");
      return (
        '<div class="pane-section" style="border:1px solid var(--ok-dim,#3a7a4a);border-radius:8px;padding:0.55rem 0.7rem;margin-bottom:0.55rem;background:rgba(58,122,74,0.06)">' +
        "<h4 style=\"margin:0 0 0.35rem\">" +
        esc(title || "Propuesta Auto") +
        " · " +
        esc(prop.family_label_es || prop.family || "—") +
        "</h4>" +
        '<p style="margin:0 0 0.4rem;font-size:1.14em">' +
        esc(prop.text || "") +
        "</p>" +
        (voteTxt
          ? '<p class="muted" style="margin:0 0 0.35rem;font-size:1.04em">Votos top: ' +
            esc(voteTxt) +
            "</p>"
          : "") +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem;margin-bottom:0.25rem">' +
        stratChips +
        "</div>" +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem">' +
        tfChips +
        "</div>" +
        '<p class="muted" style="margin:0.35rem 0 0;font-size:1.04em">' +
        esc(prop.note || "Score ≠ rentabilidad.") +
        "</p></div>"
      );
    }

    function wireProposalChips(host) {
      if (!host) return;
      host.querySelectorAll(".sc-proposal-chip").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var kind = btn.getAttribute("data-kind");
          var id = btn.getAttribute("data-id");
          if (!id || !lastScan) return;
          var prop = lastScan.proposal || {};
          if (kind === "strategy" && global.QLShell && QLShell.open) {
            QLShell.open("simulator", {
              prefill: {
                family: prop.family,
                strategy_id: id,
                interval:
                  (prop.timeframes &&
                    prop.timeframes[0] &&
                    prop.timeframes[0].interval) ||
                  lastScan.interval ||
                  "1h",
                underlying: prop.top_underlying,
                venue: lastScan.venue,
                market_type: lastScan.market_type,
              },
            });
          }
          if (kind === "tf") {
            var sel = root.querySelector("#sc-interval");
            if (sel) {
              sel.value = id;
              refreshNBars();
            }
          }
        });
      });
    }

    function renderComparison(cmp) {
      if (!cmp) return "";
      var summaryRows = (cmp.venue_summary || [])
        .map(function (v) {
          return (
            "<tr><td class=\"mono\">" +
            esc(v.venue) +
            "</td><td>" +
            esc(v.top_underlying || "—") +
            "</td><td class=\"mono\">" +
            esc(v.top_pts != null ? v.top_pts.toFixed(1) : "—") +
            "</td><td class=\"mono\">" +
            esc(v.mean_top_pts != null ? v.mean_top_pts.toFixed(1) : "—") +
            "</td></tr>"
          );
        })
        .join("");
      var cross = (cmp.by_underlying || [])
        .slice(0, 12)
        .map(function (u) {
          return (
            '<li style="margin:0.2rem 0">' +
            esc(u.text || u.underlying) +
            "</li>"
          );
        })
        .join("");
      return (
        '<div class="pane-section" style="border:1px solid var(--amber-dim,#a67c3a);border-radius:8px;padding:0.55rem 0.7rem;margin-bottom:0.55rem">' +
        "<h4 style=\"margin:0 0 0.35rem\">Comparación entre mercados</h4>" +
        (cmp.headline
          ? '<p style="margin:0 0 0.45rem;font-size:1.14em"><strong>' +
            esc(cmp.headline) +
            "</strong></p>"
          : "") +
        '<table class="mono" style="width:100%;font-size:1.08em;border-collapse:collapse;margin-bottom:0.45rem">' +
        "<thead><tr><th>Venue</th><th>Top moneda</th><th>Top pts</th><th>Media top pts</th></tr></thead>" +
        "<tbody>" +
        summaryRows +
        "</tbody></table>" +
        (cross
          ? '<p class="muted" style="margin:0 0 0.2rem;font-size:1.06em">Misma moneda · ventaja del mejor venue</p><ul style="margin:0 0 0.35rem 1.1rem;padding:0;font-size:1.08em">' +
            cross +
            "</ul>"
          : '<p class="muted" style="font-size:1.06em">Pocas monedas en común entre venues para cruzar.</p>') +
        '<p class="muted" style="margin:0;font-size:1.04em">' +
        esc(cmp.note || "") +
        "</p></div>"
      );
    }

    function formatScoreCell(compN, tied) {
      var comp = compN != null ? compN.toFixed(2) : "—";
      var pts = compN != null ? (compN * 100).toFixed(1) : "—";
      return (
        '<td class="mono sc-score-cell' +
        (tied ? " sc-score-tied" : "") +
        '" style="text-decoration:underline;text-underline-offset:2px;' +
        (tied ? "" : "color:var(--amber,#d48c32)") +
        '">' +
        esc(comp) +
        ' <span class="muted">(' +
        esc(pts) +
        " pts)</span></td>"
      );
    }

    function renderCompareTable(data, outEl, opts) {
      var groups = buildCompareGroups(data);
      var primaryVenue =
        (data.by_venue && data.by_venue[0] && data.by_venue[0].venue) || "?";
      var tools =
        '<div class="sc-compare-tools">' +
        '<span class="muted">Orden = ranking de ' +
        esc(primaryVenue) +
        "</span>" +
        '<span class="sc-layout-toggle">' +
        '<button type="button" class="btn secondary sc-layout-btn' +
        (compareLayout === "grouped" ? " active" : "") +
        '" data-layout="grouped">Agrupado</button>' +
        '<button type="button" class="btn secondary sc-layout-btn' +
        (compareLayout === "flat" ? " active" : "") +
        '" data-layout="flat">Plano</button>' +
        "</span></div>";

      if (!groups.length) {
        outEl.innerHTML =
          tools + '<p class="muted">Sin scores para comparar.</p>';
        return;
      }

      var bodyHtml = "";
      if (compareLayout === "flat") {
        var flatIdx = 0;
        groups.forEach(function (g) {
          (g.entries || []).forEach(function (e) {
            var compN = e.composite;
            var tied =
              e.row &&
              (e.row.score_status === "tied_zero" ||
                (compN === 0 && data.score_status === "degraded"));
            flatIdx += 1;
            bodyHtml +=
              '<tr class="sc-row sc-cmp-flat' +
              (flatIdx === 1 ? " sc-row-sel" : "") +
              '" data-vidx="' +
              e.venueIdx +
              '" data-sidx="' +
              e.scoreIdx +
              '" style="cursor:pointer">' +
              "<td>" +
              flatIdx +
              "</td>" +
              '<td class="mono">' +
              esc(g.underlying) +
              "</td>" +
              '<td class="mono">' +
              esc(e.venue + "/" + (e.market_type || "")) +
              "</td>" +
              formatScoreCell(compN, tied) +
              "<td>" +
              esc(scoreFamily(e.row)) +
              "</td></tr>";
          });
        });
        outEl.innerHTML =
          tools +
          '<p class="muted sc-meta">Vista plana · moneda + venue · familia por venue</p>' +
          '<table class="mono sc-cmp-table" style="width:100%;border-collapse:collapse">' +
          "<thead><tr><th>#</th><th>Moneda</th><th>Venue</th><th>Score (pts)</th><th>Familia</th></tr></thead>" +
          "<tbody>" +
          bodyHtml +
          "</tbody></table>";
      } else {
        groups.forEach(function (g, gi) {
          var pe = primaryEntry(g);
          var best = null;
          (g.entries || []).forEach(function (e) {
            if (e.composite == null) return;
            if (!best || e.composite > best.composite) best = e;
          });
          var showComp = pe && pe.composite != null ? pe.composite : best && best.composite;
          var nVen = (g.entries || []).length;
          var open = !!compareExpanded[g.underlying];
          var parentSel =
            pe &&
            pe.venueIdx === activeVenueIdx &&
            pe.scoreIdx === selectedIdx &&
            !open;
          bodyHtml +=
            '<tr class="sc-row sc-cmp-parent' +
            (parentSel || (gi === 0 && !(opts && opts.keepDetail) && !open)
              ? " sc-row-sel"
              : "") +
            (open ? " sc-cmp-open" : "") +
            '" data-und="' +
            esc(g.underlying) +
            '" data-vidx="' +
            (pe ? pe.venueIdx : 0) +
            '" data-sidx="' +
            (pe ? pe.scoreIdx : 0) +
            '" style="cursor:pointer">' +
            "<td>" +
            (gi + 1) +
            "</td>" +
            '<td class="mono">' +
            '<span class="sc-cmp-chevron" aria-hidden="true">' +
            (open ? "▼" : "▶") +
            "</span> " +
            esc(g.underlying) +
            "</td>" +
            formatScoreCell(showComp, false) +
            '<td class="muted">' +
            esc(String(nVen)) +
            " venue" +
            (nVen === 1 ? "" : "s") +
            (best
              ? " · mejor " + esc(best.venue)
              : "") +
            "</td></tr>";
          if (open) {
            (g.entries || []).forEach(function (e) {
              var tied =
                e.row &&
                (e.row.score_status === "tied_zero" || e.composite === 0);
              var childSel =
                e.venueIdx === activeVenueIdx && e.scoreIdx === selectedIdx;
              bodyHtml +=
                '<tr class="sc-cmp-child' +
                (childSel ? " sc-row-sel" : "") +
                '" data-vidx="' +
                e.venueIdx +
                '" data-sidx="' +
                e.scoreIdx +
                '" style="cursor:pointer">' +
                "<td></td>" +
                '<td class="mono muted" style="padding-left:1.35rem">' +
                esc(e.venue + "/" + (e.market_type || "")) +
                ' <span class="muted">#' +
                esc(String(e.rank)) +
                "</span></td>" +
                formatScoreCell(e.composite, tied) +
                "<td>" +
                esc(scoreFamily(e.row)) +
                "</td></tr>";
            });
          }
        });
        outEl.innerHTML =
          tools +
          '<p class="muted sc-meta">Click moneda = expandir venues debajo · subfila = detalle de ese venue</p>' +
          '<table class="mono sc-cmp-table" style="width:100%;border-collapse:collapse">' +
          "<thead><tr><th>#</th><th>Moneda / Venue</th><th>Score (pts)</th><th>Familia / venues</th></tr></thead>" +
          "<tbody>" +
          bodyHtml +
          "</tbody></table>";
      }

      outEl.querySelectorAll(".sc-layout-btn").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.stopPropagation();
          compareLayout = btn.getAttribute("data-layout") || "grouped";
          outEl.innerHTML = "";
          renderCompareTable(data, outEl, { keepDetail: true });
        });
      });

      outEl.querySelectorAll(".sc-cmp-flat").forEach(function (tr) {
        tr.addEventListener("click", function () {
          outEl.querySelectorAll(".sc-row").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          selectCompareEntry({
            venueIdx: parseInt(tr.getAttribute("data-vidx"), 10) || 0,
            scoreIdx: parseInt(tr.getAttribute("data-sidx"), 10) || 0,
          });
        });
      });

      outEl.querySelectorAll(".sc-cmp-parent").forEach(function (tr) {
        tr.addEventListener("click", function () {
          var und = tr.getAttribute("data-und") || "";
          compareExpanded[und] = !compareExpanded[und];
          selectCompareEntry({
            venueIdx: parseInt(tr.getAttribute("data-vidx"), 10) || 0,
            scoreIdx: parseInt(tr.getAttribute("data-sidx"), 10) || 0,
          });
          outEl.innerHTML = "";
          renderCompareTable(data, outEl, { keepDetail: true });
        });
      });

      outEl.querySelectorAll(".sc-cmp-child").forEach(function (tr) {
        tr.addEventListener("click", function () {
          outEl.querySelectorAll(".sc-row, .sc-cmp-child").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          selectCompareEntry({
            venueIdx: parseInt(tr.getAttribute("data-vidx"), 10) || 0,
            scoreIdx: parseInt(tr.getAttribute("data-sidx"), 10) || 0,
          });
        });
      });

      if (!(opts && opts.keepDetail)) {
        var first =
          groups[0] &&
          (compareLayout === "flat"
            ? groups[0].entries && groups[0].entries[0]
            : primaryEntry(groups[0]));
        if (first) selectCompareEntry(first);
      }
    }

    function showMultiTable(data, tableHost, out) {
      if (multiView === "compare" && data.by_venue && data.by_venue.length > 1) {
        tableHost.innerHTML = "";
        renderCompareTable(data, tableHost);
        return;
      }
      var vIdx = activeVenueIdx;
      if (vIdx < 0 || vIdx >= data.by_venue.length) vIdx = 0;
      activeVenueIdx = vIdx;
      tableHost.innerHTML = "";
      renderScoresTable(data.by_venue[vIdx], tableHost);
      renderDetail(0);
      out.querySelectorAll(".sc-venue-tab").forEach(function (b) {
        b.classList.toggle(
          "active",
          b.getAttribute("data-vidx") === String(vIdx)
        );
      });
      var cmpTab = out.querySelector('.sc-view-tab[data-view="compare"]');
      if (cmpTab) cmpTab.classList.remove("active");
    }

    function renderScores(data) {
      var out = root.querySelector("#sc-out");
      lastScan = data;
      var mlBadge = root.querySelector("#sc-ml-badge");
      if (mlBadge) {
        var ml = (data && data.ml_ranking) || {};
        if (ml.enabled && ml.active) {
          mlBadge.textContent = ml.bootstrap
            ? "ML sintético"
            : "ML " + (ml.model_id || "activo").slice(0, 12);
        } else if (ml.enabled) {
          mlBadge.textContent = "ML off";
        } else {
          mlBadge.textContent = "";
        }
      }
      activeVenueIdx = 0;
      compareExpanded = {};
      /* Agrupado: expandir todas las monedas al escanear (ver venues apilados). */
      if (
        data &&
        data.kind === "multi_venue_scanner" &&
        data.by_venue &&
        data.by_venue.length > 1
      ) {
        buildCompareGroups(data).forEach(function (g) {
          compareExpanded[g.underlying] = true;
        });
      }
      root.querySelector("#sc-detail").innerHTML = "";
      renderWarnings(data);
      if (!data) {
        out.innerHTML = '<p class="muted">Sin scores.</p>';
        return;
      }
      if (data.kind === "pairwise_scanner") {
        renderPairwiseTable(data, out);
        return;
      }
      var html = "";
      if (data.kind === "multi_venue_scanner" && data.by_venue && data.by_venue.length) {
        multiView =
          data.by_venue.length > 1 ? "compare" : "venue";
        html += renderComparison(data.comparison);
        if (data.auto_mode && data.proposal) {
          html += renderProposalBlock(data.proposal, "Propuesta Auto (global)");
        }
        if (data.auto_mode && data.proposal_by_venue && data.proposal_by_venue.length) {
          html += data.proposal_by_venue
            .map(function (pv) {
              return renderProposalBlock(
                pv.proposal,
                "Propuesta · " + (pv.venue || "?")
              );
            })
            .join("");
        }
        if (data.venue_errors && data.venue_errors.length) {
          html +=
            '<p class="muted" style="font-size:1.06em;color:var(--bad,#c66)">Errores: ' +
            esc(
              data.venue_errors
                .map(function (e) {
                  return e.venue + "=" + e.error;
                })
                .join(" · ")
            ) +
            "</p>";
        }
        html += '<div class="sim-tabs sc-multi-tabs" style="margin:0.35rem 0">';
        if (data.by_venue.length > 1) {
          html +=
            '<button type="button" class="sim-tab sc-view-tab' +
            (multiView === "compare" ? " active" : "") +
            '" data-view="compare">Comparar</button>';
        }
        html += data.by_venue
          .map(function (b, i) {
            return (
              '<button type="button" class="sim-tab sc-venue-tab' +
              (multiView === "venue" && i === 0 ? " active" : "") +
              '" data-vidx="' +
              i +
              '">' +
              esc((b.venue || "?") + "/" + (b.market_type || "")) +
              "</button>"
            );
          })
          .join("");
        html += '</div><div id="sc-venue-table"></div>';
        out.innerHTML = html;
        wireProposalChips(out);
        var tableHost = out.querySelector("#sc-venue-table");
        showMultiTable(data, tableHost, out);
        var cmpBtn = out.querySelector('.sc-view-tab[data-view="compare"]');
        if (cmpBtn) {
          cmpBtn.addEventListener("click", function () {
            multiView = "compare";
            out.querySelectorAll(".sc-venue-tab, .sc-view-tab").forEach(
              function (b) {
                b.classList.remove("active");
              }
            );
            cmpBtn.classList.add("active");
            showMultiTable(data, tableHost, out);
          });
        }
        out.querySelectorAll(".sc-venue-tab").forEach(function (btn) {
          btn.addEventListener("click", function () {
            multiView = "venue";
            activeVenueIdx = parseInt(btn.getAttribute("data-vidx"), 10) || 0;
            out.querySelectorAll(".sc-venue-tab, .sc-view-tab").forEach(
              function (b) {
                b.classList.remove("active");
              }
            );
            btn.classList.add("active");
            showMultiTable(data, tableHost, out);
          });
        });
        return;
      }
      if (!data.scores || !data.scores.length) {
        out.innerHTML = '<p class="muted">Sin scores.</p>';
        return;
      }
      out.innerHTML = data.auto_mode
        ? renderProposalBlock(data.proposal, "Propuesta Auto")
        : "";
      renderScoresTable(data, out);
      wireProposalChips(out);
      renderDetail(0);
    }

    root.querySelector("#sc-source").addEventListener("change", syncSourceUI);
    root.querySelector("#sc-scan-mode").addEventListener("change", syncScanModeUI);
    root.querySelector("#sc-window-mode").addEventListener("change", syncWindowModeUI);
    root.querySelector("#sc-limit-mode").addEventListener("change", syncUniverseUI);
    var limN = root.querySelector("#sc-limit-n");
    if (limN) limN.addEventListener("change", syncUniverseUI);
    var kroTopInp = root.querySelector("#sc-kronos-top");
    if (kroTopInp) {
      kroTopInp.addEventListener("input", function () {
        kroTopInp.dataset.userEdited = "1";
      });
    }
    var coinInp = root.querySelector("#sc-coin");
    coinInp.addEventListener("focus", function () {
      loadCoinCatalog();
      openCoinSuggest();
    });
    coinInp.addEventListener("input", function () {
      openCoinSuggest();
      if (universeMode() === "custom") {
        syncUniverseUI();
      }
    });
    coinInp.addEventListener("keydown", function (ev) {
      var box = root.querySelector("#sc-coin-suggest");
      var open = box && !box.hidden;
      var items = open ? box.querySelectorAll("button[data-id]") : [];
      if (ev.key === "ArrowDown" && open && items.length) {
        ev.preventDefault();
        coinSuggestIdx = Math.min(coinSuggestIdx + 1, items.length - 1);
        items[coinSuggestIdx].focus();
        return;
      }
      if (ev.key === "ArrowUp" && open && items.length) {
        ev.preventDefault();
        coinSuggestIdx = Math.max(coinSuggestIdx - 1, 0);
        items[coinSuggestIdx].focus();
        return;
      }
      if (ev.key === "Escape") {
        closeCoinSuggest();
        return;
      }
      if (ev.key === "Enter") {
        if (open && coinSuggestIdx >= 0 && items[coinSuggestIdx]) {
          ev.preventDefault();
          pickCoin(items[coinSuggestIdx].getAttribute("data-id"));
          return;
        }
        if (open && items.length === 1) {
          ev.preventDefault();
          pickCoin(items[0].getAttribute("data-id"));
          return;
        }
        ev.preventDefault();
        closeCoinSuggest();
        root.querySelector("#sc-run").click();
      }
    });
    coinInp.addEventListener("blur", function () {
      setTimeout(closeCoinSuggest, 140);
    });
    root.querySelector("#sc-period").addEventListener("change", refreshNBars);
    root.querySelector("#sc-interval").addEventListener("change", refreshNBars);
    root.querySelector("#sc-klines").addEventListener("input", refreshNBars);
    root.querySelector("#sc-market").addEventListener("change", function () {
      if (universeMode() === "custom") {
        loadCoinCatalog();
      }
      if (root.querySelector("#sc-market").value === "spot") {
        var hl = root.querySelector('.sc-venue-cb[value="hyperliquid"]');
        if (hl && hl.checked) {
          /* HL solo futures: al elegir spot no desmarcamos; el backend fuerza futures */
        }
      }
      refreshNBars();
    });
    root.querySelectorAll(".sc-venue-cb").forEach(function (cb) {
      cb.addEventListener("change", function () {
        if (
          (cb.value === "a3" || cb.value === "hyperliquid") &&
          cb.checked &&
          root.querySelector("#sc-market").value === "spot"
        ) {
          root.querySelector("#sc-market").value = "futures";
          loadCoinCatalog();
        }
      });
    });
    syncSourceUI();
    syncWindowModeUI();
    loadCoinCatalog();

    if (QLApi.alphaProfiles) {
      QLApi.alphaProfiles()
        .then(function (d) {
          var sel = root.querySelector("#sc-profile");
          var profiles = d.profiles || [];
          if (!profiles.length) return;
          sel.innerHTML = profiles
            .map(function (p) {
              var name = p.name || p.id;
              var label = p.label_es || name;
              return (
                '<option value="' + esc(name) + '">' + esc(label) + "</option>"
              );
            })
            .join("");
          sel.value = d.default_profile || "auto";
          if (!sel.value) sel.value = "auto";
          var topEl = root.querySelector("#sc-top");
          if (topEl && d.top_n_max) {
            topEl.max = String(d.top_n_max);
            topEl.min = String(d.top_n_min || 1);
          }
          var limN2 = root.querySelector("#sc-limit-n");
          if (limN2) {
            if (d.symbol_limit_max) limN2.max = String(d.symbol_limit_max);
            if (d.symbol_limit_min) limN2.min = String(d.symbol_limit_min);
            if (!limN2.value) {
              limN2.value = String(d.default_symbol_limit || 30);
            }
          }
          var kroTop2 = root.querySelector("#sc-kronos-top");
          if (kroTop2 && d.top_n_max) {
            kroTop2.max = String(d.top_n_max);
          }
          syncUniverseUI();
        })
        .catch(function () {});
    }

    root.querySelector("#sc-export").addEventListener("click", exportScanAudit);
    root.querySelector("#sc-rank-b-btn").addEventListener("click", loadRankingB);

    function loadRankingB() {
      var box = root.querySelector("#sc-rank-b");
      if (!box || !QLApi.validatedStrategies) return;
      box.innerHTML = '<p class="muted">Cargando Ranking B…</p>';
      QLApi.validatedStrategies()
        .then(function (d) {
          var rows = (d && d.strategies) || [];
          if (!rows.length) {
            box.innerHTML =
              '<p class="muted"><strong>Ranking B</strong>: vacío. ' +
              "Usá «Validar» sobre una candidata. Incluye aprobadas, rechazadas y fallidas.</p>";
            return;
          }
          var head =
            "<p><strong>Ranking B</strong> — evaluaciones · " +
            "ok=" +
            esc(d.n_validated != null ? d.n_validated : "—") +
            " · rech=" +
            esc(d.n_rejected != null ? d.n_rejected : "—") +
            " · fall=" +
            esc(d.n_failed != null ? d.n_failed : "—") +
            " · trials=" +
            esc(d.trial_count != null ? d.trial_count : "—") +
            "</p>";
          var table =
            '<table class="sc-table" style="width:100%;margin-top:0.35rem"><thead><tr>' +
            "<th>Estado</th><th>Estrategia</th><th>Símbolos</th>" +
            "<th>SR</th><th>DSR</th><th>MDD</th>" +
            "</tr></thead><tbody>" +
            rows
              .slice(0, 30)
              .map(function (r) {
                var st = r.status || (r.validated ? "validated_historically" : "rejected");
                var label =
                  st === "validated_historically"
                    ? "validada"
                    : st === "failed"
                      ? "fallida"
                      : "rechazada";
                return (
                  "<tr class=\"mono\">" +
                  "<td>" +
                  esc(label) +
                  "</td><td>" +
                  esc(r.strategy_id || "?") +
                  "</td><td>" +
                  esc((r.symbols || []).join("/")) +
                  "</td><td>" +
                  esc(
                    r.sharpe_net != null ? Number(r.sharpe_net).toFixed(2) : "—"
                  ) +
                  "</td><td>" +
                  esc(
                    r.deflated_sharpe != null
                      ? Number(r.deflated_sharpe).toFixed(3)
                      : "—"
                  ) +
                  "</td><td>" +
                  esc(
                    r.max_drawdown != null
                      ? Number(r.max_drawdown).toFixed(2)
                      : "—"
                  ) +
                  "</td></tr>"
                );
              })
              .join("") +
            "</tbody></table>";
          box.innerHTML = head + table;
        })
        .catch(function (e) {
          box.innerHTML =
            '<p class="muted">Ranking B: ' + esc((e && e.message) || e) + "</p>";
        });
    }

    if (global.QLRunGate) {
      QLRunGate.bindStopButton(root.querySelector("#sc-stop"), {
        kinds: ["scanner"],
        onStop: function () {
          setStatus(false, "detenido");
        },
      });
      QLRunGate.bindBusyHost(root, { kinds: ["scanner"] });
    }

    root.querySelector("#sc-run").addEventListener("click", function () {
      var topN = parseInt(root.querySelector("#sc-top").value, 10) || 5;
      var venuesPreview = selectedVenues();
      var summary =
        (root.querySelector("#sc-source").value === "synthetic"
          ? "sintético"
          : venuesPreview.join(",") || "?") +
        " · " +
        (root.querySelector("#sc-interval").value || "") +
        " · top " +
        topN;

      function startScan(handle) {
        setStatus(null, "ejecutando…");
        root.querySelector("#sc-out").textContent = "";
        root.querySelector("#sc-detail").innerHTML = "";
        root.querySelector("#sc-warn").innerHTML = "";
        var fetchOpts =
          handle && handle.signal ? { signal: handle.signal } : undefined;
        var promise;
        if (root.querySelector("#sc-source").value === "synthetic") {
          lastRequest = { source: "synthetic", top_n: topN };
          promise = QLApi.labScanner({ top_n: topN }, fetchOpts).then(
            function (d) {
              renderScores(
                Object.assign({}, d, {
                  venue: "lab",
                  market_type: "synthetic",
                  scores: (d.scores || []).map(function (s) {
                    return Object.assign({}, s, {
                      underlying: s.instrument_id,
                      recommendation: {
                        text: "Demo sintético — pasá a MD real para familia/estrategias/TF.",
                        strategies: [],
                        timeframes: [],
                        family_label_es: "—",
                      },
                    });
                  }),
                })
              );
              return d;
            }
          );
        } else if (scanMode() === "pairwise") {
          var venues = selectedVenues();
          if (!venues.length || venues.indexOf("binance") < 0) {
            setStatus(false, "pairwise requiere Binance spot");
            if (handle) handle.end();
            return;
          }
          var mode = universeMode();
          var nLimit = parseInt(root.querySelector("#sc-limit-n").value, 10) || 20;
          if (nLimit < 2) nLimit = 2;
          var kLimit = 720;
          if (windowMode() === "period") {
            var pd =
              parseInt(root.querySelector("#sc-period").value, 10) || 30;
            var iv = root.querySelector("#sc-interval").value || "1h";
            var mins = INTERVAL_MINUTES[iv] || 60;
            kLimit = Math.ceil((pd * 24 * 60) / mins);
          } else {
            kLimit =
              parseInt(root.querySelector("#sc-klines").value, 10) || 720;
          }
          if (kLimit < 120) kLimit = 120;
          var dets = selectedPairwiseDetectors();
          if (!dets.length) {
            setStatus(false, "marcá al menos un detector");
            if (handle) handle.end();
            return;
          }
          var pwOpts = {
            venue: "binance",
            market_type: root.querySelector("#sc-market").value,
            symbol_limit: mode === "0" ? 30 : nLimit,
            interval: root.querySelector("#sc-interval").value,
            kline_limit: kLimit,
            top_n: topN,
            include_signals: true,
            run_validation: !!(
              root.querySelector("#sc-pw-validate") &&
              root.querySelector("#sc-pw-validate").checked
            ),
            include_ml: !(
              root.querySelector("#sc-include-ml") &&
              !root.querySelector("#sc-include-ml").checked
            ),
            detectors: dets,
          };
          lastRequest = Object.assign({ source: "pairwise" }, pwOpts);
          promise = QLApi.pairwiseScanner(pwOpts).then(function (d) {
            renderScores(d);
            return d;
          });
        } else {
          var venues = selectedVenues();
          if (!venues.length) {
            setStatus(false, "marcá al menos un venue");
            if (handle) handle.end();
            return;
          }
          var mode = universeMode();
          var customCoins = null;
          if (mode === "custom") {
            customCoins = parseCustomCoins();
            if (!customCoins.length) {
              setStatus(false, "escribí al menos una moneda (ej. BTC)");
              syncUniverseUI();
              if (handle) handle.end();
              return;
            }
          }
          var nLimit = parseInt(root.querySelector("#sc-limit-n").value, 10) || 30;
          if (nLimit < 1) nLimit = 1;
          var kroN = parseInt(root.querySelector("#sc-kronos-top").value, 10) || 1;
          if (kroN < 1) kroN = 1;
          var opts = {
            venues: venues,
            market_type: root.querySelector("#sc-market").value,
            top_n: topN,
            symbol_limit: customCoins ? 0 : mode === "0" ? 0 : nLimit,
            interval: root.querySelector("#sc-interval").value,
            profile: root.querySelector("#sc-profile").value,
            include_ml: !(
              root.querySelector("#sc-include-ml") &&
              !root.querySelector("#sc-include-ml").checked
            ),
            fetchOpts: fetchOpts,
            kronos: {
              kronos_enabled: !!(
                root.querySelector("#sc-kronos-enabled") &&
                root.querySelector("#sc-kronos-enabled").checked
              ),
              kronos_top_n: customCoins
                ? Math.max(1, Math.min(kroN, customCoins.length))
                : kroN,
              kronos_pred_len:
                parseInt(root.querySelector("#sc-kronos-pred").value, 10) || 12,
              kronos_sample_count:
                parseInt(root.querySelector("#sc-kronos-samples").value, 10) || 4,
              kronos_legacy_override: !!(
                root.querySelector("#sc-kronos-legacy") &&
                root.querySelector("#sc-kronos-legacy").checked
              ),
            },
          };
          if (customCoins) {
            opts.underlyings = customCoins;
          }
          if (windowMode() === "period") {
            opts.period_days =
              parseInt(root.querySelector("#sc-period").value, 10) || 30;
          } else {
            opts.kline_limit =
              parseInt(root.querySelector("#sc-klines").value, 10) || 720;
          }
          lastRequest = Object.assign({ source: "real" }, opts);
          promise = QLApi.venueScanner(opts).then(function (d) {
            renderScores(d);
            return d;
          });
        }
        promise
          .then(function () {
            if (
              handle &&
              global.QLRunGate &&
              typeof QLRunGate.current === "function"
            ) {
              var cur = QLRunGate.current();
              if (cur && cur.id && handle.id && cur.id !== handle.id) {
                return; /* corrida reemplazada: no tocar status */
              }
            }
            setStatus(true, "OK");
          })
          .catch(function (err) {
            if (QLLabUI.isAbortError && QLLabUI.isAbortError(err)) {
              setStatus(false, "detenido");
            } else {
              setStatus(false, err.message || String(err));
            }
          })
          .then(
            function () {
              if (handle) handle.end();
            },
            function () {
              if (handle) handle.end();
            }
          );
      }

      if (!global.QLRunGate) {
        startScan(null);
        return;
      }
      QLRunGate.begin({
        kind: "scanner",
        label: "Scanner",
        summary: summary,
        busyRoot: root,
      }).then(function (handle) {
        if (!handle) return;
        startScan(handle);
      });
    });

    syncScanModeUI();
    root.refresh = async function () {
      refreshNBars();
    };
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createScannerPane = createScannerPane;
})(window);
