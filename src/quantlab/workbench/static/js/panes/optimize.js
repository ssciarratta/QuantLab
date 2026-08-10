/** Panel Optimizer — grid histórico (moneda/período) + sintético · memos · reopen. */
(function (global) {
  "use strict";

  var INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];
  var PERIODS = [
    { id: "7", label: "1 semana", days: 7 },
    { id: "30", label: "1 mes", days: 30 },
    { id: "90", label: "3 meses", days: 90 },
    { id: "180", label: "6 meses", days: 180 },
    { id: "365", label: "1 año", days: 365 },
  ];
  var VENUES = ["binance", "okx", "bybit", "hyperliquid", "a3"];

  function optHtml(list, selected) {
    return list
      .map(function (x) {
        var id = typeof x === "string" ? x : String(x.id);
        var label = typeof x === "string" ? x : x.label;
        var sel = id === String(selected) ? " selected" : "";
        return (
          '<option value="' +
          id.replace(/"/g, "&quot;") +
          '"' +
          sel +
          ">" +
          label +
          "</option>"
        );
      })
      .join("");
  }

  function stampNow() {
    var d = new Date();
    function p(n) {
      return n < 10 ? "0" + n : String(n);
    }
    return (
      d.getFullYear() +
      p(d.getMonth() + 1) +
      p(d.getDate()) +
      "-" +
      p(d.getHours()) +
      p(d.getMinutes())
    );
  }

  function createOptimizePane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-optimize";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head">' +
      "<h3>Optimizer</h3>" +
      '<p class="muted pane-sub" id="op-head-sub">' +
      '<span class="data-badge data-badge-real" id="op-mode-badge">HISTÓRICO</span> ' +
      "grid lookback×qty · una moneda · período · LIVE bloqueado</p>" +
      "</div>" +
      '<div class="pane-row pane-actions">' +
      '<label class="field">Datos<select id="op-mode">' +
      '<option value="historical" selected>Histórico (MD público)</option>' +
      '<option value="synthetic">Sintético (debug lab)</option>' +
      "</select></label>" +
      '<label class="field" id="op-venue-wrap">Mercado<select id="op-venue">' +
      optHtml(VENUES, "binance") +
      "</select></label>" +
      '<label class="field" id="op-market-wrap">Tipo<select id="op-market">' +
      '<option value="futures" selected>Futuros</option>' +
      '<option value="spot">Spot</option>' +
      "</select></label>" +
      '<label class="field" id="op-coin-wrap">Moneda' +
      '<input id="op-coin" type="search" placeholder="BTC, ETH, APT…" ' +
      'autocomplete="off" spellcheck="false" /></label>' +
      "</div>" +
      '<div class="pane-row pane-actions">' +
      '<label class="field" id="op-period-wrap">Período<select id="op-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label class="field" id="op-interval-wrap">TF<select id="op-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<label class="field" id="op-nbars-wrap" hidden>n_bars' +
      '<input id="op-bars" type="number" class="mono" min="8" max="60" value="20" /></label>' +
      '<label class="field">Capital USDT' +
      '<input id="op-capital" type="number" value="10000" min="1" /></label>' +
      '<span class="mono muted" id="op-nbars-hint">≈ —</span>' +
      "</div>" +
      '<div class="pane-toolbar">' +
      '<label>lookbacks <input type="text" id="op-lb" class="mono" value="2,3"></label>' +
      '<label>qty <input type="text" id="op-qty" class="mono" value="1"></label>' +
      '<span class="muted mono" style="font-size:0.75em">estrategia: momentum (grid)</span>' +
      "</div>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn" id="op-run">Optimizar</button>' +
      '<button type="button" class="btn secondary stop-run" id="op-stop" hidden disabled ' +
      'title="Detener optimización">Stop</button>' +
      '<button type="button" class="btn secondary" id="op-memo" disabled ' +
      'title="Ver memorando de la última corrida">Ver memorando</button>' +
      '<button type="button" class="btn secondary" id="op-refresh">Actualizar</button>' +
      '<button type="button" class="btn secondary" id="op-to-bt" ' +
      'title="Abrir Backtest con esta moneda/params">→ Backtest</button>' +
      '<button type="button" class="btn secondary" id="op-to-sim" ' +
      'title="Abrir Simulador con esta moneda">→ Simulador</button>' +
      '<span class="mono" id="op-status">—</span>' +
      "</div>" +
      '<p class="mono muted" id="op-context" style="margin:0.35rem 0">Elegí moneda + período</p>' +
      '<p class="muted mono" id="op-meta">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Mejor trial</h3>" +
      '<p class="mono" id="op-best">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Resultados</h3>" +
      '<div id="op-table"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Pareto (sharpe ↑ · MDD ↓)</h3>" +
      '<p class="mono" id="op-pareto-meta">—</p>' +
      '<div id="op-pareto-chart"></div>' +
      '<div id="op-pareto"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Historial sesión</h3>" +
      '<div id="op-runs"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<details class="pane-more muted"><summary>Datos técnicos (JSON)</summary>' +
      '<div id="op-out" style="margin-top:0.35rem"></div></details>' +
      "</div>";

    const status = root.querySelector("#op-status");
    const meta = root.querySelector("#op-meta");
    const bestEl = root.querySelector("#op-best");
    const tableEl = root.querySelector("#op-table");
    const paretoMeta = root.querySelector("#op-pareto-meta");
    const paretoChart = root.querySelector("#op-pareto-chart");
    const paretoEl = root.querySelector("#op-pareto");
    const runsEl = root.querySelector("#op-runs");
    const out = root.querySelector("#op-out");
    const ctxEl = root.querySelector("#op-context");
    const btnMemo = root.querySelector("#op-memo");
    let lastResult = null;
    let lastParams = null;

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function money(v) {
      if (v == null || v === "") return "—";
      var n = Number(v);
      if (!isFinite(n)) return esc(v);
      return n.toLocaleString("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }

    function parseCsvInts(raw) {
      return String(raw || "")
        .split(",")
        .map(function (x) {
          return parseInt(x.trim(), 10);
        })
        .filter(function (n) {
          return !isNaN(n);
        });
    }

    function parseCsvStrs(raw) {
      return String(raw || "")
        .split(",")
        .map(function (x) {
          return x.trim();
        })
        .filter(Boolean);
    }

    function isHistorical() {
      return root.querySelector("#op-mode").value !== "synthetic";
    }

    function syncModeUI() {
      var hist = isHistorical();
      [
        "#op-venue-wrap",
        "#op-market-wrap",
        "#op-coin-wrap",
        "#op-period-wrap",
        "#op-interval-wrap",
      ].forEach(function (sel) {
        var el = root.querySelector(sel);
        if (el) el.hidden = !hist;
      });
      var nb = root.querySelector("#op-nbars-wrap");
      if (nb) nb.hidden = hist;
      var badge = root.querySelector("#op-mode-badge");
      var sub = root.querySelector("#op-head-sub");
      if (badge) {
        badge.className =
          "data-badge " + (hist ? "data-badge-real" : "data-badge-synth");
        badge.textContent = hist ? "HISTÓRICO" : "SINTÉTICO";
      }
      if (sub) {
        sub.innerHTML =
          '<span class="data-badge ' +
          (hist ? "data-badge-real" : "data-badge-synth") +
          '" id="op-mode-badge">' +
          (hist ? "HISTÓRICO" : "SINTÉTICO") +
          "</span> " +
          (hist
            ? "grid lookback×qty · una moneda · período · LIVE bloqueado"
            : "velas inventadas · debug grid");
      }
      refreshNBarsHint();
      updateContextLine();
    }

    function refreshNBarsHint() {
      var hint = root.querySelector("#op-nbars-hint");
      if (!hint) return;
      if (!isHistorical()) {
        hint.textContent =
          "≈ " +
          (root.querySelector("#op-bars").value || "?") +
          " velas sintéticas";
        return;
      }
      var days = Number(root.querySelector("#op-period").value) || 30;
      var iv = root.querySelector("#op-interval").value || "1h";
      if (QLApi.simPeriod) {
        QLApi.simPeriod(days, iv)
          .then(function (d) {
            hint.textContent =
              "≈ " +
              (d.n_bars != null ? d.n_bars : "?") +
              " velas · " +
              days +
              "d × " +
              iv;
          })
          .catch(function () {
            hint.textContent = "≈ ? · " + days + "d × " + iv;
          });
      } else {
        hint.textContent = "≈ ? · " + days + "d × " + iv;
      }
    }

    function updateContextLine() {
      if (!isHistorical()) {
        ctxEl.textContent =
          "Sintético · momentum grid · " +
          (root.querySelector("#op-bars").value || "?") +
          " velas inventadas (no es mercado real)";
        return;
      }
      var coin = (root.querySelector("#op-coin").value || "").trim().toUpperCase();
      var venue = root.querySelector("#op-venue").value;
      var mt = root.querySelector("#op-market").value;
      var days = root.querySelector("#op-period").value;
      var iv = root.querySelector("#op-interval").value;
      if (!coin) {
        ctxEl.textContent =
          "Elegí moneda · " + venue + " " + mt + " · " + days + "d · " + iv;
        return;
      }
      ctxEl.textContent =
        coin +
        " · " +
        venue +
        " / " +
        mt +
        " · " +
        days +
        "d · " +
        iv +
        " · momentum · capital " +
        money(root.querySelector("#op-capital").value);
    }

    function readFormParams() {
      var hist = isHistorical();
      var coin = (root.querySelector("#op-coin").value || "").trim().toUpperCase();
      var venue = root.querySelector("#op-venue").value;
      var lookbacks = parseCsvInts(root.querySelector("#op-lb").value);
      var quantities = parseCsvStrs(root.querySelector("#op-qty").value);
      return {
        kind: "optimize",
        mode: hist ? "historical" : "synthetic",
        strategy_id: "momentum",
        lookbacks: lookbacks.length ? lookbacks : [2, 3],
        quantities: quantities.length ? quantities : ["1"],
        venue: hist ? venue : null,
        underlying: hist ? coin : null,
        coin: hist ? coin : null,
        market_type: hist ? root.querySelector("#op-market").value : null,
        interval: hist ? root.querySelector("#op-interval").value : null,
        period_days: hist
          ? Number(root.querySelector("#op-period").value) || 30
          : null,
        n_bars: hist
          ? null
          : parseInt(root.querySelector("#op-bars").value, 10) || 20,
        initial_cash: Number(root.querySelector("#op-capital").value) || 10000,
        pairs:
          hist && coin
            ? [{ venue: venue, underlying: coin, ticker: coin }]
            : [],
      };
    }

    function buildOpMemo(data, formParams) {
      var p = formParams || readFormParams();
      var ctx = (data && data.context) || {};
      var br = (data && data.bar_range) || ctx.bar_range || {};
      var best = (data && data.best) || {};
      var lines = [];
      lines.push("QUANTLAB — MEMORANDO DE OPTIMIZER");
      lines.push("Fecha: " + new Date().toLocaleString("es-AR"));
      lines.push("");
      lines.push("=== QUÉ SE CORRIÓ ===");
      lines.push(
        "Modo: " +
          (ctx.mode === "synthetic" || p.mode === "synthetic"
            ? "SINTÉTICO (velas inventadas)"
            : "HISTÓRICO (MD público)")
      );
      lines.push("Moneda: " + (ctx.underlying || p.underlying || p.coin || "—"));
      lines.push(
        "Mercado: " +
          (ctx.venue || p.venue || "—") +
          " / " +
          (ctx.market_type || p.market_type || "—")
      );
      lines.push(
        "TF / período: " +
          (ctx.interval || p.interval || "—") +
          " · " +
          (ctx.period_days != null
            ? ctx.period_days + " días"
            : p.period_days != null
              ? p.period_days + " días"
              : p.n_bars
                ? p.n_bars + " velas"
                : "—")
      );
      lines.push(
        "Velas usadas: " +
          (data && data.n_bars != null ? data.n_bars : "—") +
          (br.start ? " · " + br.start + " → " + (br.end || "") : "")
      );
      lines.push(
        "Fuente: " + (ctx.data_source || (data && data.data_source) || "—")
      );
      lines.push("Estrategia: momentum (grid lookback × quantity)");
      lines.push(
        "lookbacks: " +
          JSON.stringify(
            (data && data.params && data.params.lookbacks) || p.lookbacks
          )
      );
      lines.push(
        "quantities: " +
          JSON.stringify(
            (data && data.params && data.params.quantities) || p.quantities
          )
      );
      lines.push(
        "Capital: " +
          money(
            data && data.initial_cash != null ? data.initial_cash : p.initial_cash
          )
      );
      lines.push("");
      lines.push("=== MEJOR TRIAL ===");
      lines.push("trial_id: " + (best.trial_id != null ? best.trial_id : "—"));
      lines.push("score (sharpe): " + (best.score != null ? best.score : "—"));
      lines.push("params: " + JSON.stringify(best.params || {}));
      if (best.metrics) {
        lines.push("metrics: " + JSON.stringify(best.metrics));
      }
      lines.push(
        "trials: " + (data && data.n_trials != null ? data.n_trials : "—")
      );
      if (data && data.pareto) {
        lines.push(
          "Pareto front: " +
            (data.pareto.n_front != null ? data.pareto.n_front : "?")
        );
      }
      lines.push("run_id: " + ((data && data.run_id) || "—"));
      lines.push("");
      lines.push("LIVE_BLOCKED=True · sin órdenes al venue");

      var csv = [
        "campo,valor",
        "mode," + (ctx.mode || p.mode || ""),
        "moneda," + (ctx.underlying || p.underlying || ""),
        "venue," + (ctx.venue || p.venue || ""),
        "market_type," + (ctx.market_type || p.market_type || ""),
        "interval," + (ctx.interval || p.interval || ""),
        "period_days," +
          (ctx.period_days != null ? ctx.period_days : p.period_days || ""),
        "n_bars," + ((data && data.n_bars) || ""),
        "lookbacks," + JSON.stringify(p.lookbacks || []),
        "quantities," + JSON.stringify(p.quantities || []),
        "best_score," + (best.score != null ? best.score : ""),
        "best_params," + JSON.stringify(best.params || {}),
        "n_trials," + ((data && data.n_trials) || ""),
        "run_id," + ((data && data.run_id) || ""),
      ].join("\n");

      var coin = ctx.underlying || p.underlying || p.coin || "synth";
      return {
        kind: "optimize",
        title: "Optimizer · " + coin + " · momentum",
        text: lines.join("\n"),
        csv: csv,
        filenameBase:
          "quantlab-optimize-" +
          String(coin).toLowerCase() +
          "-" +
          stampNow(),
      };
    }

    function presentOpMemo(data, formParams, doRegister) {
      if (!data) return;
      var params = formParams || readFormParams();
      var memo = buildOpMemo(data, params);
      if (
        doRegister &&
        global.QLSimRegistry &&
        typeof global.QLSimRegistry.add === "function"
      ) {
        try {
          var best = data.best || {};
          global.QLSimRegistry.add({
            kind: "optimize",
            title: memo.title,
            summary:
              (params.underlying || params.coin || params.mode || "") +
              " · trials=" +
              (data.n_trials != null ? data.n_trials : "?") +
              " · best=" +
              (best.score != null ? best.score : "?"),
            params: params,
            memo: memo,
          });
        } catch (e) {}
      }
      if (
        !doRegister &&
        global.QLSimRegistry &&
        typeof global.QLSimRegistry.openMemo === "function"
      ) {
        global.QLSimRegistry.openMemo(memo, params);
      }
    }

    function renderParetoSvg(front, dominated) {
      const pts = (front || []).concat(dominated || []);
      if (!pts.length) {
        paretoChart.innerHTML = "";
        return;
      }
      const xs = pts.map(function (p) {
        return (p.objectives && p.objectives.sharpe) != null
          ? Number(p.objectives.sharpe)
          : 0;
      });
      const ys = pts.map(function (p) {
        return (p.objectives && p.objectives.max_drawdown) != null
          ? Number(p.objectives.max_drawdown)
          : 0;
      });
      const minX = Math.min.apply(null, xs);
      const maxX = Math.max.apply(null, xs);
      const minY = Math.min.apply(null, ys);
      const maxY = Math.max.apply(null, ys);
      const pad = 18;
      const w = 280;
      const h = 140;
      function sx(v) {
        if (maxX === minX) return w / 2;
        return pad + ((v - minX) / (maxX - minX)) * (w - 2 * pad);
      }
      function sy(v) {
        if (maxY === minY) return h / 2;
        return h - pad - ((v - minY) / (maxY - minY)) * (h - 2 * pad);
      }
      const frontIds = {};
      (front || []).forEach(function (p) {
        frontIds[p.trial_id] = true;
      });
      const dots = pts
        .map(function (p) {
          const ox = p.objectives || {};
          const x = sx(Number(ox.sharpe || 0));
          const y = sy(Number(ox.max_drawdown || 0));
          const isFront = !!frontIds[p.trial_id];
          return (
            '<circle cx="' +
            x.toFixed(1) +
            '" cy="' +
            y.toFixed(1) +
            '" r="' +
            (isFront ? "4.5" : "3") +
            '" fill="' +
            (isFront ? "var(--accent, #2a6)" : "var(--muted, #888)") +
            '" opacity="' +
            (isFront ? "0.95" : "0.55") +
            '"><title>t' +
            esc(p.trial_id) +
            " sharpe=" +
            esc(ox.sharpe) +
            " mdd=" +
            esc(ox.max_drawdown) +
            "</title></circle>"
          );
        })
        .join("");
      paretoChart.innerHTML =
        '<svg class="optimize-pareto-svg" width="' +
        w +
        '" height="' +
        h +
        '" viewBox="0 0 ' +
        w +
        " " +
        h +
        '" role="img" aria-label="Pareto scatter">' +
        '<rect x="0" y="0" width="' +
        w +
        '" height="' +
        h +
        '" fill="transparent" stroke="currentColor" opacity="0.15"/>' +
        '<text x="' +
        pad +
        '" y="12" class="mono" font-size="9" fill="currentColor" opacity="0.6">sharpe →</text>' +
        '<text x="4" y="' +
        (h - 4) +
        '" class="mono" font-size="9" fill="currentColor" opacity="0.6">MDD ↑</text>' +
        dots +
        "</svg>";
    }

    function renderResult(data) {
      if (!data) {
        bestEl.textContent = "sin corridas — corré optimizar";
        tableEl.innerHTML = "";
        paretoMeta.textContent = "—";
        paretoEl.innerHTML = "";
        paretoChart.innerHTML = "";
        out.innerHTML = "";
        btnMemo.disabled = true;
        return;
      }
      const ok = data.ok !== false;
      const nFront =
        data.pareto && data.pareto.n_front != null ? data.pareto.n_front : 0;
      QLLabUI.setStatus(
        status,
        ok,
        ok
          ? "OK · trials " +
              (data.n_trials != null ? data.n_trials : "?") +
              " · pareto " +
              nFront
          : "FAIL"
      );
      var ctx = data.context || {};
      meta.textContent =
        (ctx.mode === "synthetic" || data.mode === "synthetic"
          ? "SINTÉTICO"
          : "HISTÓRICO") +
        " · " +
        (ctx.underlying || data.underlying || "—") +
        " · " +
        (ctx.venue || data.venue || ctx.data_source || data.data_source || "") +
        " · " +
        (data.method || "grid") +
        " · n_bars=" +
        (data.n_bars != null ? data.n_bars : "?") +
        (data.run_id ? " · " + data.run_id : "") +
        (data.persisted ? " · persisted" : "");

      if (ctx.underlying || data.underlying) {
        ctxEl.textContent =
          (ctx.underlying || data.underlying) +
          " · " +
          (ctx.venue || "") +
          "/" +
          (ctx.market_type || "") +
          " · " +
          (data.n_bars != null ? data.n_bars + " velas" : "") +
          (ctx.bar_range && ctx.bar_range.start
            ? " · " + ctx.bar_range.start + " → " + (ctx.bar_range.end || "")
            : "");
      }

      const best = data.best || {};
      const bm = best.metrics || {};
      bestEl.textContent =
        "trial=" +
        (best.trial_id != null ? best.trial_id : "?") +
        " · score=" +
        (best.score != null ? best.score : "?") +
        " · params=" +
        JSON.stringify(best.params || {}) +
        (bm.max_drawdown != null ? " · mdd=" + bm.max_drawdown : "");

      const hist = data.history || [];
      if (!hist.length) {
        tableEl.innerHTML = '<p class="muted mono">sin trials</p>';
      } else {
        tableEl.innerHTML =
          '<table class="data-table optimize-table"><thead><tr>' +
          "<th>id</th><th>params</th><th>score</th><th>sharpe</th><th>MDD</th>" +
          "</tr></thead><tbody>" +
          hist
            .map(function (t) {
              const m = t.metrics || {};
              return (
                "<tr>" +
                '<td class="num">' +
                esc(t.trial_id) +
                "</td>" +
                '<td class="mono">' +
                esc(JSON.stringify(t.params || {})) +
                "</td>" +
                '<td class="num">' +
                esc(t.score) +
                "</td>" +
                '<td class="num">' +
                esc(m.sharpe != null ? m.sharpe : t.score) +
                "</td>" +
                '<td class="num">' +
                esc(m.max_drawdown != null ? m.max_drawdown : "—") +
                "</td>" +
                "</tr>"
              );
            })
            .join("") +
          "</tbody></table>";
      }

      const pareto = data.pareto;
      if (!pareto) {
        paretoMeta.textContent = "sin multi-objetivo (necesita ≥2 trials)";
        paretoEl.innerHTML = "";
        paretoChart.innerHTML = "";
      } else {
        paretoMeta.textContent =
          "front=" +
          (pareto.n_front != null ? pareto.n_front : "?") +
          " · dominated=" +
          (pareto.n_dominated != null ? pareto.n_dominated : "?");
        const front = pareto.front || [];
        renderParetoSvg(front, pareto.dominated || []);
        if (!front.length) {
          paretoEl.innerHTML = '<p class="muted mono">frente vacío</p>';
        } else {
          paretoEl.innerHTML =
            '<table class="data-table optimize-table"><thead><tr>' +
            "<th>id</th><th>params</th><th>sharpe</th><th>MDD</th>" +
            "</tr></thead><tbody>" +
            front
              .map(function (p) {
                const o = p.objectives || {};
                return (
                  "<tr>" +
                  '<td class="num">' +
                  esc(p.trial_id) +
                  "</td>" +
                  '<td class="mono">' +
                  esc(JSON.stringify(p.params || {})) +
                  "</td>" +
                  '<td class="num">' +
                  esc(o.sharpe) +
                  "</td>" +
                  '<td class="num">' +
                  esc(o.max_drawdown) +
                  "</td>" +
                  "</tr>"
                );
              })
              .join("") +
            "</tbody></table>";
        }
      }

      out.innerHTML = QLLabUI.preJson(data);
      btnMemo.disabled = false;
    }

    function renderRuns(listPayload) {
      const runs = (listPayload && listPayload.runs) || [];
      if (!runs.length) {
        runsEl.innerHTML =
          '<p class="muted mono">sin corridas — corré optimizar</p>';
        return;
      }
      runsEl.innerHTML =
        '<table class="data-table optimize-table"><thead><tr>' +
        "<th>run_id</th><th>trials</th><th>best</th><th>pareto</th>" +
        "</tr></thead><tbody>" +
        runs
          .map(function (r) {
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(r.run_id) +
              "</td>" +
              '<td class="num">' +
              esc(r.n_trials != null ? r.n_trials : "—") +
              "</td>" +
              '<td class="num">' +
              esc(r.best_score != null ? r.best_score : "—") +
              "</td>" +
              '<td class="num">' +
              esc(r.pareto_n_front != null ? r.pareto_n_front : "—") +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    }

    async function refresh() {
      const data = await QLApi.labOptimizeHistory();
      const source = data.latest || null;
      if (source) renderResult(source);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    root.querySelector("#op-mode").addEventListener("change", syncModeUI);
    ["#op-period", "#op-interval", "#op-bars", "#op-capital", "#op-venue", "#op-market"].forEach(
      function (sel) {
        var el = root.querySelector(sel);
        if (!el) return;
        el.addEventListener("change", function () {
          refreshNBarsHint();
          updateContextLine();
        });
        el.addEventListener("input", updateContextLine);
      }
    );
    root.querySelector("#op-coin").addEventListener("input", updateContextLine);
    root.querySelector("#op-coin").addEventListener("change", updateContextLine);

    root.querySelector("#op-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    btnMemo.addEventListener("click", function () {
      if (!lastResult) {
        QLLabUI.setStatus(status, false, "sin corrida — optimizá primero");
        return;
      }
      presentOpMemo(lastResult, lastParams || readFormParams(), false);
    });

    root.querySelector("#op-to-bt").addEventListener("click", function () {
      var p = readFormParams();
      if (!global.QLShell) return;
      global.QLShell.open("backtest", {
        prefill: {
          mode: p.mode,
          venue: p.venue,
          underlying: p.underlying,
          market_type: p.market_type,
          interval: p.interval,
          period_days: p.period_days,
          n_bars: p.n_bars,
          initial_cash: p.initial_cash,
          strategy_id: "momentum",
          message: "Desde Optimizer",
        },
      });
    });

    root.querySelector("#op-to-sim").addEventListener("click", function () {
      var p = readFormParams();
      if (!global.QLShell) return;
      global.QLShell.open("simulator", {
        prefill: {
          pairs: p.pairs,
          venue: p.venue,
          market_type: p.market_type,
          interval: p.interval,
          period_days: p.period_days,
          strategy_id: "momentum",
          message: "Desde Optimizer",
        },
      });
    });

    QLLabUI.bindRun(
      root,
      "#op-run",
      "#op-status",
      "#op-out",
      function (signal) {
        var formParams = readFormParams();
        if (formParams.mode === "historical" && !formParams.underlying) {
          return Promise.reject(new Error("escribí una moneda (ej. BTC)"));
        }
        var body;
        if (formParams.mode === "historical") {
          body = {
            mode: "historical",
            lookbacks: formParams.lookbacks,
            quantities: formParams.quantities,
            venue: formParams.venue,
            underlying: formParams.underlying,
            market_type: formParams.market_type,
            interval: formParams.interval,
            period_days: formParams.period_days,
            initial_cash: formParams.initial_cash,
          };
        } else {
          body = {
            mode: "synthetic",
            lookbacks: formParams.lookbacks,
            quantities: formParams.quantities,
            n_bars: formParams.n_bars,
            initial_cash: formParams.initial_cash,
          };
        }
        return QLApi.labOptimize(
          body,
          signal ? { signal: signal } : undefined
        ).then(function (data) {
          lastResult = data;
          lastParams = formParams;
          renderResult(data);
          presentOpMemo(data, formParams, true);
          refresh().catch(function () {});
          return data;
        });
      },
      {
        kind: "optimize",
        label: "Optimizar",
        summary: function () {
          var p = readFormParams();
          if (p.mode === "historical") {
            return (
              (p.underlying || "?") +
              " · " +
              (p.venue || "") +
              " · " +
              (p.period_days || "") +
              "d · lb " +
              (root.querySelector("#op-lb").value || "")
            );
          }
          return (
            "sintético · lb " +
            (root.querySelector("#op-lb").value || "") +
            " · " +
            (root.querySelector("#op-bars").value || "") +
            " bars"
          );
        },
        stopSel: "#op-stop",
        renderJson: false,
      }
    );

    root.applyPrefill = function (prefill) {
      if (!prefill || typeof prefill !== "object") return;
      if (prefill.mode === "synthetic") {
        root.querySelector("#op-mode").value = "synthetic";
      } else if (
        prefill.mode === "historical" ||
        prefill.underlying ||
        prefill.coin ||
        (prefill.pairs && prefill.pairs.length)
      ) {
        root.querySelector("#op-mode").value = "historical";
      }
      syncModeUI();
      if (prefill.venue) root.querySelector("#op-venue").value = prefill.venue;
      if (prefill.market_type) {
        root.querySelector("#op-market").value = prefill.market_type;
      }
      var coin =
        prefill.underlying ||
        prefill.coin ||
        (prefill.pairs &&
          prefill.pairs[0] &&
          (prefill.pairs[0].underlying || prefill.pairs[0].ticker));
      if (coin) root.querySelector("#op-coin").value = String(coin).toUpperCase();
      if (prefill.interval) {
        root.querySelector("#op-interval").value = prefill.interval;
      }
      if (prefill.period_days != null) {
        root.querySelector("#op-period").value = String(prefill.period_days);
      }
      if (prefill.n_bars != null) {
        root.querySelector("#op-bars").value = String(prefill.n_bars);
      }
      if (prefill.initial_cash != null) {
        root.querySelector("#op-capital").value = String(prefill.initial_cash);
      }
      if (prefill.lookbacks) {
        root.querySelector("#op-lb").value = Array.isArray(prefill.lookbacks)
          ? prefill.lookbacks.join(",")
          : String(prefill.lookbacks);
      }
      if (prefill.quantities) {
        root.querySelector("#op-qty").value = Array.isArray(prefill.quantities)
          ? prefill.quantities.join(",")
          : String(prefill.quantities);
      }
      refreshNBarsHint();
      updateContextLine();
      if (prefill.message) {
        QLLabUI.setStatus(status, true, prefill.message);
      }
    };

    root.applyNavFocus = function () {
      if (!global.QLNav) return;
      var focus = global.QLNav.takeFocus("optimize");
      if (!focus) return;
      if (focus.prefill) root.applyPrefill(focus.prefill);
      if (focus.message) QLLabUI.setStatus(status, true, focus.message);
    };

    root.refresh = refresh;
    syncModeUI();
    if (root.applyNavFocus) root.applyNavFocus();
    refresh().catch(function () {});
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createOptimizePane = createOptimizePane;
})(window);
