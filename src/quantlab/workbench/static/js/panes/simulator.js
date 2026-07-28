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
  var VENUES = ["binance", "okx", "bybit", "hyperliquid"];
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

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
      "Compará venues (spot/futuros · leverage · capital · fees). " +
      "Aprender/paper → <strong>Guided Lab</strong>. Estrés → <strong>Monte Carlo</strong>. LIVE bloqueado." +
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
      '<label class="muted">Leverage <input type="range" id="sim-lev" min="1" max="125" value="1"> ' +
      '<span id="sim-lev-val" class="mono">1x</span></label>' +
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
      '<label class="muted">Capital USDT <input type="number" id="sim-capital" value="10000" min="1" style="width:6em"></label>' +
      '<label class="muted">Por trade USDT <input type="number" id="sim-per-trade" value="500" min="1" style="width:5em"></label>' +
      '<span class="mono muted" id="sim-size-hint">—</span>' +
      '<label class="muted">Bench anual % <input type="number" id="sim-bench" value="5" min="0" step="0.1" style="width:4em"></label>' +
      '<label class="muted"><input type="checkbox" id="sim-liq" checked> liquidación</label>' +
      '<label class="muted"><input type="checkbox" id="sim-funding" checked> funding</label>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.4rem;margin-top:0.35rem;align-items:center">' +
      '<span class="muted">Fees venue</span> <span class="mono" id="sim-fee-preset">—</span>' +
      '<label class="muted">maker bps <input id="sim-maker" type="number" step="0.1" style="width:4em"></label>' +
      '<label class="muted">taker bps <input id="sim-taker" type="number" step="0.1" style="width:4em"></label>' +
      '<button type="button" class="btn secondary" id="sim-add-cost">+ Gasto</button>' +
      "</div>" +
      '<div id="sim-extra-costs" class="mono muted" style="font-size:0.8em"></div>' +
      "</div>" +
      '<div class="pane-section sim-panel" data-panel="comparar">' +
      "<h4>Comparar mercados (histórico)</h4>" +
      '<p class="muted" style="font-size:0.8em;margin:0 0 0.4rem">' +
      "Activá un exchange y elegí monedas del menú (nombre completo + ticker). " +
      "Cada par exchange×moneda se corre por separado." +
      "</p>" +
      '<div id="sim-venue-picks" class="sim-venue-picks">cargando monedas…</div>' +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem;margin-top:0.45rem">' +
      '<label class="muted">Estrategia <select id="sim-strat-hist"></select></label>' +
      '<button type="button" class="btn secondary" id="sim-strat-info" title="Detalle de la estrategia seleccionada">¿Cómo opera?</button>' +
      '<button type="button" class="btn" id="sim-run-hist">Correr y comparar</button>' +
      "</div>" +
      '<p class="muted" style="font-size:0.8em;margin:0.35rem 0 0">' +
      'Atajos: <button type="button" class="btn secondary" id="sim-open-gl">Guided Lab</button> ' +
      '<button type="button" class="btn secondary" id="sim-open-mc">Monte Carlo</button> ' +
      '<button type="button" class="btn secondary" id="sim-open-blotter">Paper Blotter</button>' +
      "</p>" +
      '<div class="mono" id="sim-out-hist">—</div></div>' +
      '<div class="pane-section sim-panel" data-panel="estrategias" style="display:none">' +
      "<h4>Catálogo por familia</h4>" +
      '<p class="muted" style="margin-top:0">Desplegá una familia · elegí una estrategia · popup con operación paso a paso.</p>' +
      '<div id="sim-strat-list">cargando…</div></div>' +
      '<div id="sim-strat-modal" class="sim-modal" hidden>' +
      '<div class="sim-modal-backdrop" data-close="1"></div>' +
      '<div class="sim-modal-card" role="dialog" aria-modal="true">' +
      '<div class="sim-modal-head">' +
      '<h3 id="sim-modal-title">Estrategia</h3>' +
      '<button type="button" class="btn secondary" id="sim-modal-close">Cerrar</button>' +
      "</div>" +
      '<div class="sim-modal-body mono" id="sim-modal-body"></div>' +
      '<div class="sim-modal-foot">' +
      '<button type="button" class="btn" id="sim-modal-use">Usar en Comparar</button>' +
      "</div></div></div>";

    var extraCosts = [];
    var feeSchedules = [];
    var strategiesCache = [];
    var familyLabels = {};
    var modalStrategyId = null;
    var coinsCache = [];
    var venueMeta = [];
    /** @type {Object.<string, string[]>} */
    var selectedByVenue = {};
    /** @type {Object.<string, boolean>} */
    var venueEnabled = { binance: true, okx: false, bybit: false, hyperliquid: false };

    function showTab(name) {
      root.querySelectorAll(".sim-tab").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === name);
      });
      root.querySelectorAll(".sim-panel").forEach(function (p) {
        p.style.display = p.getAttribute("data-panel") === name ? "" : "none";
      });
    }

    function coinLabel(id) {
      var c = coinsCache.find(function (x) {
        return x.id === id;
      });
      return c ? c.label || c.name + " (" + c.id + ")" : id;
    }

    function renderVenuePicks() {
      var box = root.querySelector("#sim-venue-picks");
      if (!venueMeta.length) {
        venueMeta = VENUES.map(function (v) {
          return { id: v, name: v, label: v };
        });
      }
      if (!coinsCache.length) {
        box.textContent = "sin catálogo de monedas";
        return;
      }
      box.innerHTML = venueMeta
        .map(function (vm) {
          var vid = vm.id;
          if (!selectedByVenue[vid]) {
            selectedByVenue[vid] = vid === "binance" ? ["BTC", "ETH"] : [];
          }
          if (venueEnabled[vid] == null) {
            venueEnabled[vid] = selectedByVenue[vid].length > 0;
          }
          var checked = !!venueEnabled[vid];
          var chips = (selectedByVenue[vid] || [])
            .map(function (cid) {
              return (
                '<span class="sim-coin-chip">' +
                esc(coinLabel(cid)) +
                ' <button type="button" class="sim-coin-rm" data-venue="' +
                esc(vid) +
                '" data-coin="' +
                esc(cid) +
                '" title="Quitar">×</button></span>'
              );
            })
            .join(" ");
          var opts = coinsCache
            .map(function (c) {
              return (
                "<option value=\"" +
                esc(c.id) +
                "\">" +
                esc(c.label || c.name + " (" + c.id + ")") +
                "</option>"
              );
            })
            .join("");
          return (
            '<div class="sim-venue-row" data-venue="' +
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
            '<select class="sim-coin-select" data-venue="' +
            esc(vid) +
            '"' +
            (checked ? "" : " disabled") +
            ">" +
            '<option value="">— elegir moneda —</option>' +
            opts +
            "</select>" +
            '<button type="button" class="btn secondary sim-coin-add" data-venue="' +
            esc(vid) +
            '"' +
            (checked ? "" : " disabled") +
            ">Agregar</button>" +
            "</div>" +
            '<div class="sim-coin-chips" data-venue="' +
            esc(vid) +
            '">' +
            (chips || '<span class="muted">ninguna moneda</span>') +
            "</div></div>"
          );
        })
        .join("");

      box.querySelectorAll(".sim-coin-add").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var vid = btn.getAttribute("data-venue");
          var sel = box.querySelector('.sim-coin-select[data-venue="' + vid + '"]');
          var cid = sel && sel.value;
          if (!cid) return;
          if (!selectedByVenue[vid]) selectedByVenue[vid] = [];
          if (selectedByVenue[vid].indexOf(cid) < 0) {
            selectedByVenue[vid].push(cid);
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
          venueEnabled[c.value] = c.checked;
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
            d.exceeds_lab_cap || d.exceeds_lab_cap_3000
              ? d.note || "excede tope lab " + (d.lab_kline_limit_max || 8760)
              : "";
          el.style.color =
            d.exceeds_lab_cap || d.exceeds_lab_cap_3000 ? "#d4544a" : "";
        })
        .catch(function () {
          el.textContent = "≈ —";
        });
    }

    function refreshSizing() {
      var hint = root.querySelector("#sim-size-hint");
      if (!QLApi.simSizing) return;
      QLApi.simSizing({
        initial_capital: root.querySelector("#sim-capital").value,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        leverage: root.querySelector("#sim-lev").value,
        market_type: root.querySelector("#sim-market").value,
      })
        .then(function (d) {
          if (d.ok) {
            hint.textContent =
              "margen " + d.margin + " · notional " + d.notional + " ✓";
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

    function applyFeePreset() {
      var venue = "binance";
      var checked = root.querySelector(".sim-venue-on:checked");
      if (checked) venue = checked.value;
      var mt = root.querySelector("#sim-market").value;
      var hit = feeSchedules.find(function (s) {
        return s.venue === venue && s.market_type === mt;
      });
      var presetEl = root.querySelector("#sim-fee-preset");
      if (hit) {
        presetEl.textContent =
          venue + "/" + mt + " maker=" + hit.maker_bps + " taker=" + hit.taker_bps;
        root.querySelector("#sim-maker").value = hit.maker_bps;
        root.querySelector("#sim-taker").value = hit.taker_bps;
      } else {
        presetEl.textContent = "sin preset";
      }
    }

    function loadUniverse() {
      var box = root.querySelector("#sim-venue-picks");
      if (!QLApi.simUniverse) {
        coinsCache = [
          { id: "BTC", name: "Bitcoin", label: "Bitcoin (BTC)" },
          { id: "ETH", name: "Ethereum", label: "Ethereum (ETH)" },
        ];
        renderVenuePicks();
        return;
      }
      QLApi.simUniverse()
        .then(function (d) {
          coinsCache = d.coins || [];
          venueMeta = d.venues || [];
          renderVenuePicks();
          applyFeePreset();
        })
        .catch(function (e) {
          box.textContent = e.message || "error cargando monedas";
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
        '<p><strong>Idea</strong></p><p>' +
        esc(g.idea || s.description || "—") +
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
        "<p><strong>Cuándo vende / flat</strong></p><p>" +
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

    function openStrategyModal(id) {
      var s = findStrategy(id);
      if (!s) return;
      modalStrategyId = id;
      root.querySelector("#sim-modal-title").textContent =
        (s.name || id) + (s.runnable === false ? " [stub]" : "");
      root.querySelector("#sim-modal-body").innerHTML = renderGuideHtml(s);
      var modal = root.querySelector("#sim-strat-modal");
      modal.hidden = false;
      modal.classList.add("open");
    }

    function closeStrategyModal() {
      var modal = root.querySelector("#sim-strat-modal");
      modal.hidden = true;
      modal.classList.remove("open");
      modalStrategyId = null;
    }

    function loadStrategies() {
      QLApi.labStrategies()
        .then(function (d) {
          strategiesCache = d.strategies || d.items || [];
          familyLabels = d.family_labels_es || {};
          var opts = strategiesCache
            .map(function (s) {
              var id = s.id || s.strategy_id;
              var lab =
                (s.name || id) + (s.runnable === false ? " [stub]" : "");
              return (
                "<option value=\"" + esc(id) + "\">" + esc(lab) + "</option>"
              );
            })
            .join("");
          root.querySelector("#sim-strat-hist").innerHTML = opts;

          var byFam = {};
          strategiesCache.forEach(function (s) {
            var f = s.family || "other";
            if (!byFam[f]) byFam[f] = [];
            byFam[f].push(s);
          });
          var famKeys = FAMILY_ORDER.filter(function (f) {
            return byFam[f];
          }).concat(
            Object.keys(byFam)
              .filter(function (f) {
                return FAMILY_ORDER.indexOf(f) < 0;
              })
              .sort()
          );

          var html = famKeys
            .map(function (fam, idx) {
              var label = familyLabels[fam] || fam;
              var items = byFam[fam] || [];
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
              openStrategyModal(btn.getAttribute("data-id"));
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
      return QLApi.simCompare({
        pairs: pairs,
        market_type: root.querySelector("#sim-market").value,
        leverages: leverages(),
        strategy_id: strategyId,
        interval: root.querySelector("#sim-interval").value,
        period_days: periodDays(),
        initial_capital: root.querySelector("#sim-capital").value,
        per_trade_usd: root.querySelector("#sim-per-trade").value,
        simulate_liquidation: root.querySelector("#sim-liq").checked,
        apply_funding: root.querySelector("#sim-funding").checked,
        annual_bench_rate: Number(root.querySelector("#sim-bench").value || 0) / 100,
        extra_costs: collectExtraCosts(),
        maker_bps: root.querySelector("#sim-maker").value || undefined,
        taker_bps: root.querySelector("#sim-taker").value || undefined,
      });
    }

    function formatRows(data) {
      var rows = data.rows || [];
      if (!rows.length) return "sin filas";
      return (
        '<table class="mono" style="width:100%;font-size:0.75em"><thead><tr>' +
        "<th>venue</th><th>modo</th><th>sym</th><th>x</th><th>final</th><th>pnl</th><th>bench</th><th>liq</th></tr></thead><tbody>" +
        rows
          .map(function (r) {
            var o = r.overlay || {};
            var b = (r.backtest && r.backtest.benchmark) || r.benchmark || {};
            return (
              "<tr><td>" +
              esc(r.venue) +
              "</td><td>" +
              esc(r.market_type) +
              "</td><td>" +
              esc(r.underlying || r.instrument_id) +
              "</td><td>" +
              esc(r.leverage) +
              "</td><td>" +
              esc(o.final_equity || "—") +
              "</td><td>" +
              esc(o.pnl || r.error || "—") +
              "</td><td>" +
              esc(b.period_return != null ? b.period_return : "—") +
              "</td><td>" +
              (o.liquidated ? "sí" : "no") +
              "</td></tr>"
            );
          })
          .join("") +
        "</tbody></table>"
      );
    }

    root.querySelectorAll(".sim-tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        showTab(btn.getAttribute("data-tab"));
      });
    });
    root.querySelector("#sim-lev").addEventListener("input", function () {
      root.querySelector("#sim-lev-val").textContent =
        root.querySelector("#sim-lev").value + "x";
      refreshSizing();
    });
    ["#sim-period", "#sim-interval"].forEach(function (sel) {
      root.querySelector(sel).addEventListener("change", refreshNBars);
    });
    ["#sim-capital", "#sim-per-trade", "#sim-market"].forEach(function (sel) {
      root.querySelector(sel).addEventListener("change", function () {
        refreshSizing();
        applyFeePreset();
      });
      root.querySelector(sel).addEventListener("input", refreshSizing);
    });
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
      openStrategyModal(root.querySelector("#sim-strat-hist").value);
    });
    root.querySelector("#sim-modal-close").addEventListener("click", closeStrategyModal);
    root.querySelector("#sim-strat-modal").addEventListener("click", function (ev) {
      if (ev.target && ev.target.getAttribute("data-close") === "1") {
        closeStrategyModal();
      }
    });
    root.querySelector("#sim-modal-use").addEventListener("click", function () {
      if (modalStrategyId) {
        root.querySelector("#sim-strat-hist").value = modalStrategyId;
      }
      closeStrategyModal();
      showTab("comparar");
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
      refreshSizing();
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
