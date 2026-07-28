/** Simulador multi-venue — solapas Aprender / Histórico / Estrés / Practicar / Estrategias. */
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

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
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
      '<p class="muted" style="margin-top:0">Spot/Futuros · leverage · período · capital · fees · benchmark. LIVE bloqueado.</p>' +
      '<div class="sim-tabs" role="tablist">' +
      '<button type="button" class="sim-tab active" data-tab="aprender">Aprender</button>' +
      '<button type="button" class="sim-tab" data-tab="historico">Histórico</button>' +
      '<button type="button" class="sim-tab" data-tab="estres">Estrés</button>' +
      '<button type="button" class="sim-tab" data-tab="practicar">Practicar</button>' +
      '<button type="button" class="sim-tab" data-tab="estrategias">Estrategias</button>' +
      "</div></div>" +
      '<div class="pane-section sim-common">' +
      "<h4>Controles comunes</h4>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.45rem">' +
      '<label class="muted">Modo <select id="sim-market">' +
      '<option value="spot">Spot</option><option value="futures" selected>Futuros</option></select></label>' +
      '<label class="muted">Leverage <input type="range" id="sim-lev" min="1" max="125" value="1"> ' +
      '<span id="sim-lev-val" class="mono">1x</span></label>' +
      '<label class="muted"><input type="checkbox" id="sim-multi-x"> multi-x (1,2,5,10)</label>' +
      '<label class="muted">Período <select id="sim-period">' +
      optHtml(PERIODS, "30") +
      '</select></label>' +
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
      '<div class="pane-section sim-panel" data-panel="aprender">' +
      "<h4>Aprender (datos inventados)</h4>" +
      '<p class="muted">Badge INVENTADO — no es mercado real.</p>' +
      '<div class="pane-row"><label class="muted">Estrategia <select id="sim-strat-learn"></select></label>' +
      '<button type="button" class="btn" id="sim-run-learn">Ejecutar aprender</button></div>' +
      '<div class="mono" id="sim-out-learn">—</div></div>' +
      '<div class="pane-section sim-panel" data-panel="historico" style="display:none">' +
      "<h4>Histórico (mercados reales)</h4>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.35rem" id="sim-venues">' +
      VENUES.map(function (v) {
        return (
          '<label class="muted"><input type="checkbox" class="sim-venue" value="' +
          v +
          '" checked> ' +
          v +
          "</label>"
        );
      }).join("") +
      "</div>" +
      '<div class="pane-row"><label class="muted">Símbolos (coma) <input id="sim-symbols" value="BTC,ETH" style="width:12em"></label>' +
      '<label class="muted">Estrategia <select id="sim-strat-hist"></select></label>' +
      '<button type="button" class="btn" id="sim-run-hist">Correr y comparar</button></div>' +
      '<div class="mono" id="sim-out-hist">—</div></div>' +
      '<div class="pane-section sim-panel" data-panel="estres" style="display:none">' +
      "<h4>Estrés (Monte Carlo)</h4>" +
      '<p class="muted">No es otro backtest: dispersión bajo shocks. Abrí el panel Monte Carlo con el último report.</p>' +
      '<button type="button" class="btn" id="sim-open-mc">Abrir Monte Carlo</button></div>' +
      '<div class="pane-section sim-panel" data-panel="practicar" style="display:none">' +
      "<h4>Practicar (paper / demo)</h4>" +
      '<p class="muted">Órdenes de mentira — no horizonte de meses. Abrí Guided Lab demo o Paper Blotter.</p>' +
      '<button type="button" class="btn secondary" id="sim-open-gl">Guided Lab</button> ' +
      '<button type="button" class="btn secondary" id="sim-open-blotter">Paper Blotter</button></div>' +
      '<div class="pane-section sim-panel" data-panel="estrategias" style="display:none">' +
      "<h4>Catálogo de estrategias</h4>" +
      '<div id="sim-strat-list" class="mono" style="max-height:280px;overflow:auto">cargando…</div></div>';

    var extraCosts = [];
    var feeSchedules = [];

    function activeTab() {
      var t = root.querySelector(".sim-tab.active");
      return t ? t.getAttribute("data-tab") : "aprender";
    }

    function showTab(name) {
      root.querySelectorAll(".sim-tab").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === name);
      });
      root.querySelectorAll(".sim-panel").forEach(function (p) {
        p.style.display = p.getAttribute("data-panel") === name ? "" : "none";
      });
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
          el.textContent = d.n_bars_display || ("≈ " + d.n_bars + " velas");
          el.title = d.exceeds_lab_cap_3000 ? d.note || "excede tope lab 3000" : "";
          el.style.color = d.exceeds_lab_cap_3000 ? "#d4544a" : "";
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
      var checked = root.querySelector(".sim-venue:checked");
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

    function loadStrategies() {
      QLApi.labStrategies()
        .then(function (d) {
          var list = d.strategies || d.items || [];
          var opts = list
            .map(function (s) {
              var id = s.id || s.strategy_id;
              var lab = (s.name || id) + (s.runnable === false ? " [stub]" : "");
              return "<option value=\"" + esc(id) + "\">" + esc(lab) + "</option>";
            })
            .join("");
          root.querySelector("#sim-strat-learn").innerHTML = opts;
          root.querySelector("#sim-strat-hist").innerHTML = opts;
          var html = list
            .map(function (s) {
              var id = s.id || s.strategy_id;
              var runnable = s.runnable !== false;
              var kinds = runnable
                ? "Aprender · Histórico · Estrés · Practicar"
                : "Solo research (stub)";
              return (
                "<div style=\"margin:0.35rem 0;padding:0.35rem;border:1px solid rgba(255,255,255,0.08)\">" +
                "<strong>" +
                esc(s.name || id) +
                "</strong> <span class=\"muted\">" +
                esc(id) +
                "</span><br>" +
                "<span class=\"muted\">" +
                esc(s.description || "") +
                "</span><br>" +
                "Corridas: " +
                esc(kinds) +
                ' <button type="button" class="btn secondary sim-use-strat" data-id="' +
                esc(id) +
                '">Usar en Histórico</button></div>'
              );
            })
            .join("");
          root.querySelector("#sim-strat-list").innerHTML = html || "sin estrategias";
          root.querySelectorAll(".sim-use-strat").forEach(function (btn) {
            btn.addEventListener("click", function () {
              var id = btn.getAttribute("data-id");
              root.querySelector("#sim-strat-hist").value = id;
              showTab("historico");
            });
          });
        })
        .catch(function (e) {
          root.querySelector("#sim-strat-list").textContent = e.message || "error";
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

    function runCompare(venues, underlyings, strategyId) {
      var body = {
        venues: venues,
        underlyings: underlyings,
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
      };
      return QLApi.simCompare(body);
    }

    function formatRows(data) {
      var rows = data.rows || [];
      if (!rows.length) return "sin filas";
      return (
        "<table class=\"mono\" style=\"width:100%;font-size:0.75em\"><thead><tr>" +
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
    root.querySelectorAll(".sim-venue").forEach(function (c) {
      c.addEventListener("change", applyFeePreset);
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
    root.querySelector("#sim-run-learn").addEventListener("click", function () {
      var out = root.querySelector("#sim-out-learn");
      out.textContent = "corriendo (lab inventado vía binance path sintético)…";
      // Aprender: usa compare con venue lab-like — backtest sintético local
      QLApi.labBacktest({
        strategy_id: root.querySelector("#sim-strat-learn").value,
        n_bars: Math.min(2000, Math.max(24, periodDays() * 24)),
        initial_cash: root.querySelector("#sim-capital").value,
      })
        .then(function (d) {
          out.innerHTML =
            '<span class="data-badge data-badge-synth">INVENTADO</span> ' +
            "final=" +
            esc(d.final_equity) +
            " pnl=" +
            esc(d.pnl) +
            " fees=" +
            esc(d.total_fees);
        })
        .catch(function (e) {
          out.textContent = e.message || String(e);
        });
    });
    root.querySelector("#sim-run-hist").addEventListener("click", function () {
      var out = root.querySelector("#sim-out-hist");
      var venues = [];
      root.querySelectorAll(".sim-venue:checked").forEach(function (c) {
        venues.push(c.value);
      });
      var syms = root
        .querySelector("#sim-symbols")
        .value.split(",")
        .map(function (s) {
          return s.trim();
        })
        .filter(Boolean);
      out.textContent = "comparando…";
      runCompare(venues, syms, root.querySelector("#sim-strat-hist").value)
        .then(function (d) {
          out.innerHTML =
            '<span class="data-badge data-badge-real">HISTÓRICO</span> ' +
            formatRows(d);
        })
        .catch(function (e) {
          out.textContent = e.message || String(e);
        });
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
      loadStrategies();
      renderExtraCosts();
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSimulatorPane = createSimulatorPane;
})(window);
