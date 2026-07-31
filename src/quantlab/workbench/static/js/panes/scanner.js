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
      "<h3>Alpha Scanner</h3>" +
      '<p class="muted sc-sub">MD real · ranking por rama · score ≠ rentabilidad</p>' +
      "</div>" +
      '<div class="sc-toolbar">' +
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
      '<label>Top<input id="sc-top" type="number" value="5" min="1" max="10" /></label>' +
      '<label>Universo<select id="sc-limit">' +
      '<option value="20">20</option>' +
      '<option value="30" selected>30</option>' +
      '<option value="40">40</option>' +
      '<option value="50">50</option>' +
      '<option value="0">Todas</option>' +
      '<option value="custom">Moneda puntual…</option>' +
      "</select></label>" +
      '<label id="sc-coin-wrap" hidden>Moneda' +
      '<div class="sc-coin-pick">' +
      '<input id="sc-coin" type="search" placeholder="Buscar: BTC, ETH, NEAR…" ' +
      'autocomplete="off" spellcheck="false" aria-autocomplete="list" ' +
      'aria-controls="sc-coin-suggest" />' +
      '<ul id="sc-coin-suggest" class="sc-coin-suggest" hidden role="listbox"></ul>' +
      "</div></label>" +
      "</div>" +
      '<div class="sc-venues" id="sc-venues-row">' +
      "<span class=\"muted\">Mercados</span>" +
      '<label><input type="checkbox" class="sc-venue-cb" value="binance" checked> Binance</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="okx"> OKX</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="bybit"> Bybit</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="hyperliquid"> HL</label>' +
      '<label><input type="checkbox" class="sc-venue-cb" value="a3"> A3</label>' +
      '<span class="mono muted" id="sc-nbars" style="margin-left:auto">≈ —</span>' +
      "</div>" +
      '<div class="sc-actions">' +
      '<button type="button" class="btn" id="sc-run">Escanear</button>' +
      '<button type="button" class="btn secondary stop-run" id="sc-stop" hidden disabled title="Detener escaneo">Stop</button>' +
      '<button type="button" class="btn secondary" id="sc-export" title="Descarga JSON auditable de la última consulta">Exportar JSON</button>' +
      '<span class="mono" id="sc-status">—</span>' +
      "</div>" +
      '<details class="sc-more muted"><summary>Ayuda · tandas y multi-mercado</summary>' +
      '<p id="sc-hint" style="margin:0.35rem 0 0">' +
      "Tanda = monedas scoreadas. Multi-mercado = pestaña Comparar (misma moneda, scores por mercado) + ranking por mercado. " +
      "A3/HL = futuros. Exportá el JSON para auditoría de terceros." +
      "</p></details>" +
      '<div id="sc-warn"></div>' +
      '<div id="sc-out"></div>' +
      '<div id="sc-detail" class="sc-detail" style="margin-top:0.45rem"></div>' +
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

    function syncUniverseUI() {
      var custom = root.querySelector("#sc-limit").value === "custom";
      var wrap = root.querySelector("#sc-coin-wrap");
      if (wrap) wrap.hidden = !custom;
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
            root.querySelector("#sc-limit").value === "custom" &&
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
        "#sc-limit",
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
        : "Tanda = monedas scoreadas. Universo «Moneda puntual»: buscá en el catálogo (typeahead). Multi-venue = Comparar + ranking por mercado.";
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

    function scoreComposite(s) {
      if (!s) return null;
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
      var scoreBlock =
        '<div class="sc-score-explain" style="margin:0 0 0.65rem;padding:0.55rem 0.65rem;' +
        "border-left:3px solid var(--amber-dim,#a67c3a);" +
        'background:rgba(212,140,50,0.07);border-radius:0 6px 6px 0">' +
        '<p style="margin:0 0 0.35rem"><strong>Score ' +
        esc(comp != null ? comp.toFixed(2) : "—") +
        "</strong>" +
        (comp != null ? " (" + esc((comp * 100).toFixed(1)) + " pts)" : "") +
        (band.title ? " · " + esc(band.title) : "") +
        " · " +
        esc(venue) +
        "/" +
        esc(mt) +
        "</p>" +
        '<p class="muted" style="margin:0 0 0.35rem;font-size:0.8em">' +
        esc((explained && explained.headline) || rec.text || "") +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:0.8em"><strong>¿Qué es este número?</strong><br>' +
        esc(
          (explained && explained.what_is) ||
            "Va de 0 a 1: compara esta moneda con las otras del scan para la rama elegida. No es rentabilidad."
        ) +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:0.8em"><strong>¿Por qué en esta rama?</strong><br>' +
        esc((explained && explained.family_why) || "") +
        "</p>" +
        '<p style="margin:0 0 0.35rem;font-size:0.8em"><strong>Esta banda</strong><br>' +
        esc(band.why || "") +
        "</p>" +
        '<p class="muted" style="margin:0 0 0.35rem;font-size:0.75em">' +
        esc(
          (explained && explained.ranges_help) ||
            "0.50–0.99 ≈ rangos útiles para probar; ≥0.75 mejor ajuste."
        ) +
        "</p>" +
        (factorLis
          ? "<p style=\"margin:0 0 0.2rem;font-size:0.8em\"><strong>Factores que arman el score</strong></p>" +
            '<ul style="margin:0 0 0.45rem 1.1rem;padding:0;font-size:0.78em">' +
            factorLis +
            "</ul>"
          : "") +
        (nextLis
          ? "<p style=\"margin:0 0 0.2rem;font-size:0.8em\"><strong>Qué hacer ahora</strong></p>" +
            '<ol style="margin:0 0 0.25rem 1.1rem;padding:0;font-size:0.78em">' +
            nextLis +
            "</ol>"
          : "") +
        '<p class="muted" style="margin:0;font-size:0.72em">' +
        esc((explained && explained.note) || "Score ≠ rentabilidad. LIVE bloqueado.") +
        "</p></div>";

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
        '<button type="button" class="btn" id="sc-open-sim">Abrir en Simulador</button>' +
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
    }

    function renderWarnings(data) {
      var box = root.querySelector("#sc-warn");
      if (!box) return;
      var warns = (data && data.warnings) || [];
      var status = (data && data.score_status) || "ok";
      if (!warns.length && status === "ok") {
        box.innerHTML = "";
        return;
      }
      var lis = warns
        .map(function (w) {
          return "<li>" + esc(w) + "</li>";
        })
        .join("");
      box.innerHTML =
        '<div class="sc-warn"><strong>Aviso ranking</strong>' +
        (status && status !== "ok"
          ? ' · <span class="mono">' + esc(status) + "</span>"
          : "") +
        (lis ? "<ul>" + lis + "</ul>" : "") +
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
          var compN =
            s.composite != null
              ? Number(s.composite)
              : s.base_score != null
                ? Number(s.base_score)
                : null;
          var comp = compN != null ? compN.toFixed(2) : "—";
          var pts = compN != null ? (compN * 100).toFixed(1) : "—";
          var fam =
            (s.recommendation && s.recommendation.family_label_es) ||
            (s.recommendation && s.recommendation.family) ||
            "—";
          var tied = s.score_status === "tied_zero" || (degraded && compN === 0);
          var aviso = tied
            ? "empatado / sin discriminación"
            : s.score_reason
              ? String(s.score_reason)
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
            '<td class="mono sc-score-cell' +
            (tied ? " sc-score-tied" : "") +
            '" title="' +
            esc(
              tied
                ? "Score empatado en 0 — ver avisos arriba"
                : "Click para ver qué significa este score"
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
          block.universe_mode === "all"
            ? "todas"
            : block.symbol_limit != null
              ? block.symbol_limit
              : ""
        ) +
        (block.n_universe != null ? " (" + esc(block.n_universe) + ")" : "") +
        " · fetched=" +
        esc(block.n_symbols_fetched != null ? block.n_symbols_fetched : block.fetched) +
        (block.md_meta && block.md_meta.provider
          ? " · md=" + esc(block.md_meta.provider)
          : "") +
        (block.score_status && block.score_status !== "ok"
          ? " · <span class=\"sc-score-tied\">" +
            esc(block.score_status) +
            "</span>"
          : "") +
        "</p>" +
        '<table class="mono" style="width:100%;border-collapse:collapse">' +
        "<thead><tr><th>#</th><th>Moneda</th><th>Score (pts)</th><th>Familia</th><th>Aviso</th></tr></thead>" +
        "<tbody>" +
        rowsHtml +
        "</tbody></table>";
      outEl.querySelectorAll(".sc-row").forEach(function (tr) {
        tr.addEventListener("click", function () {
          outEl.querySelectorAll(".sc-row").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          renderDetail(parseInt(tr.getAttribute("data-idx"), 10) || 0);
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
        '<p style="margin:0 0 0.4rem;font-size:0.85em">' +
        esc(prop.text || "") +
        "</p>" +
        (voteTxt
          ? '<p class="muted" style="margin:0 0 0.35rem;font-size:0.72em">Votos top: ' +
            esc(voteTxt) +
            "</p>"
          : "") +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem;margin-bottom:0.25rem">' +
        stratChips +
        "</div>" +
        '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem">' +
        tfChips +
        "</div>" +
        '<p class="muted" style="margin:0.35rem 0 0;font-size:0.72em">' +
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
          ? '<p style="margin:0 0 0.45rem;font-size:0.85em"><strong>' +
            esc(cmp.headline) +
            "</strong></p>"
          : "") +
        '<table class="mono" style="width:100%;font-size:0.78em;border-collapse:collapse;margin-bottom:0.45rem">' +
        "<thead><tr><th>Venue</th><th>Top moneda</th><th>Top pts</th><th>Media top pts</th></tr></thead>" +
        "<tbody>" +
        summaryRows +
        "</tbody></table>" +
        (cross
          ? '<p class="muted" style="margin:0 0 0.2rem;font-size:0.75em">Misma moneda · ventaja del mejor venue</p><ul style="margin:0 0 0.35rem 1.1rem;padding:0;font-size:0.78em">' +
            cross +
            "</ul>"
          : '<p class="muted" style="font-size:0.75em">Pocas monedas en común entre venues para cruzar.</p>') +
        '<p class="muted" style="margin:0;font-size:0.72em">' +
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
            '<p class="muted" style="font-size:0.75em;color:var(--bad,#c66)">Errores: ' +
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
    root.querySelector("#sc-window-mode").addEventListener("change", syncWindowModeUI);
    root.querySelector("#sc-limit").addEventListener("change", syncUniverseUI);
    var coinInp = root.querySelector("#sc-coin");
    coinInp.addEventListener("focus", function () {
      loadCoinCatalog();
      openCoinSuggest();
    });
    coinInp.addEventListener("input", function () {
      openCoinSuggest();
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
      if (root.querySelector("#sc-limit").value === "custom") {
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
          if (d.symbol_batches && d.symbol_batches.length) {
            var lim = root.querySelector("#sc-limit");
            var cur = lim.value;
            var optsHtml = d.symbol_batches
              .map(function (n) {
                return (
                  '<option value="' +
                  esc(n) +
                  '">' +
                  esc(n) +
                  " monedas</option>"
                );
              })
              .join("");
            optsHtml +=
              '<option value="0">Todas (universo disponible)</option>';
            optsHtml +=
              '<option value="custom">Moneda puntual…</option>';
            lim.innerHTML = optsHtml;
            if (cur === "custom") {
              lim.value = "custom";
            } else {
              lim.value = String(
                cur === "0" ? 0 : d.default_symbol_limit || cur || 30
              );
              if (!lim.value && lim.value !== "0") {
                lim.value = String(d.symbol_batches[1] || d.symbol_batches[0]);
              }
            }
            syncUniverseUI();
          }
        })
        .catch(function () {});
    }

    root.querySelector("#sc-export").addEventListener("click", exportScanAudit);

    if (global.QLRunGate) {
      QLRunGate.bindStopButton(root.querySelector("#sc-stop"), {
        kinds: ["scanner"],
        onStop: function () {
          setStatus(false, "detenido");
        },
      });
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
        } else {
          var venues = selectedVenues();
          if (!venues.length) {
            setStatus(false, "marcá al menos un venue");
            if (handle) handle.end();
            return;
          }
          var limitRaw = root.querySelector("#sc-limit").value;
          var customCoins = null;
          if (limitRaw === "custom") {
            customCoins = parseCustomCoins();
            if (!customCoins.length) {
              setStatus(false, "escribí al menos una moneda (ej. BTC)");
              syncUniverseUI();
              if (handle) handle.end();
              return;
            }
          }
          var opts = {
            venues: venues,
            market_type: root.querySelector("#sc-market").value,
            top_n: topN,
            symbol_limit: customCoins
              ? 0
              : limitRaw === "0"
                ? 0
                : parseInt(limitRaw, 10) || 30,
            interval: root.querySelector("#sc-interval").value,
            profile: root.querySelector("#sc-profile").value,
            fetchOpts: fetchOpts,
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
            setStatus(true, "OK");
          })
          .catch(function (err) {
            if (QLLabUI.isAbortError && QLLabUI.isAbortError(err)) {
              setStatus(false, "detenido");
            } else {
              setStatus(false, err.message || String(err));
            }
          })
          .then(function () {
            if (handle) handle.end();
          });
      }

      if (!global.QLRunGate) {
        startScan(null);
        return;
      }
      QLRunGate.begin({
        kind: "scanner",
        label: "Scanner",
        summary: summary,
      }).then(function (handle) {
        if (!handle) return;
        startScan(handle);
      });
    });

    root.refresh = async function () {
      refreshNBars();
    };
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createScannerPane = createScannerPane;
})(window);
