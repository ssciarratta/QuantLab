/** Panel Backtest — histórico (moneda/período) + sintético debug · memos · reopen. */
(function (global) {
  "use strict";

  var INTERVALS = [
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
  ];
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

  function esc(s) {
    return global.QLLabUI && QLLabUI.escapeHtml
      ? QLLabUI.escapeHtml(s)
      : String(s == null ? "" : s)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
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

  function createBacktestPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-backtest";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head">' +
      "<h3>Backtest</h3>" +
      '<p class="muted pane-sub" id="bt-head-sub">' +
      '<span class="data-badge data-badge-real" id="bt-mode-badge">HISTÓRICO</span> ' +
      "una moneda · estrategia · período · LIVE bloqueado</p>" +
      "</div>" +
      '<div class="pane-row pane-actions" id="bt-mode-row">' +
      '<label class="field">Datos<select id="bt-mode">' +
      '<option value="historical" selected>Histórico (MD público)</option>' +
      '<option value="synthetic">Sintético (debug lab)</option>' +
      "</select></label>" +
      '<label class="field" id="bt-venue-wrap">Mercado<select id="bt-venue">' +
      optHtml(VENUES, "binance") +
      "</select></label>" +
      '<label class="field" id="bt-market-wrap">Tipo<select id="bt-market">' +
      '<option value="futures" selected>Futuros</option>' +
      '<option value="spot">Spot</option>' +
      "</select></label>" +
      '<label class="field" id="bt-coin-wrap">Moneda' +
      '<input id="bt-coin" type="search" placeholder="BTC, ETH, APT…" ' +
      'autocomplete="off" spellcheck="false" /></label>' +
      "</div>" +
      '<div class="pane-row pane-actions">' +
      '<label class="field" id="bt-period-wrap">Período<select id="bt-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label class="field" id="bt-interval-wrap">TF<select id="bt-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<label class="field" id="bt-nbars-wrap" hidden>n_bars' +
      '<input id="bt-nbars" type="number" value="120" min="4" max="2000" /></label>' +
      '<label class="field">Capital USDT' +
      '<input id="bt-capital" type="number" value="10000" min="1" /></label>' +
      '<span class="mono muted" id="bt-nbars-hint">≈ —</span>' +
      "</div>" +
      '<div class="pane-row pane-actions">' +
      '<label class="field">Estrategia<select id="bt-strategy"></select></label>' +
      '<button type="button" class="btn" id="bt-run">Correr</button>' +
      '<button type="button" class="btn secondary stop-run" id="bt-stop" hidden disabled ' +
      'title="Detener backtest">Stop</button>' +
      '<button type="button" class="btn secondary" id="bt-memo" disabled ' +
      'title="Ver memorando de la última corrida">Ver memorando</button>' +
      '<button type="button" class="btn secondary" id="bt-to-mc" disabled ' +
      'title="Requiere un backtest corrido con report_id">→ Monte Carlo</button>' +
      '<button type="button" class="btn secondary" id="bt-to-sim" ' +
      'title="Abrir Simulador con esta moneda/mercado">→ Simulador</button>' +
      '<span class="mono" id="bt-status">—</span>' +
      "</div>" +
      '<div class="pane-row" id="bt-params-row"></div>' +
      '<p class="mono muted" id="bt-context" style="margin:0.35rem 0">Elegí moneda + período</p>' +
      '<div id="bt-summary" class="bt-summary"></div>' +
      '<details class="pane-more muted"><summary>Datos técnicos (JSON)</summary>' +
      '<div id="bt-out" style="margin-top:0.35rem"></div></details>' +
      "</div>";

    const selectEl = root.querySelector("#bt-strategy");
    const paramsRow = root.querySelector("#bt-params-row");
    const btnMc = root.querySelector("#bt-to-mc");
    const btnMemo = root.querySelector("#bt-memo");
    const status = root.querySelector("#bt-status");
    const out = root.querySelector("#bt-out");
    const summaryEl = root.querySelector("#bt-summary");
    const ctxEl = root.querySelector("#bt-context");
    let catalog = [];
    let lastResult = null;
    let lastParams = null;
    let coinSuggest = [];

    function isHistorical() {
      return root.querySelector("#bt-mode").value !== "synthetic";
    }

    function currentMeta() {
      const id = selectEl.value;
      for (let i = 0; i < catalog.length; i++) {
        if (catalog[i].id === id) return catalog[i];
      }
      return null;
    }

    function renderParams() {
      const meta = currentMeta();
      paramsRow.innerHTML = "";
      if (!meta || !meta.default_params) return;
      Object.keys(meta.default_params).forEach(function (key) {
        const val = meta.default_params[key];
        const label = document.createElement("label");
        label.className = "field";
        label.textContent = key;
        const input = document.createElement("input");
        input.dataset.paramKey = key;
        input.type = typeof val === "number" ? "number" : "text";
        input.value = val == null ? "" : String(val);
        label.appendChild(input);
        paramsRow.appendChild(label);
      });
    }

    function collectParams() {
      const params = {};
      paramsRow.querySelectorAll("input[data-param-key]").forEach(function (input) {
        const key = input.dataset.paramKey;
        const raw = input.value.trim();
        if (!raw) return;
        if (input.type === "number") {
          const n = Number(raw);
          params[key] = Number.isFinite(n) ? n : raw;
        } else {
          params[key] = raw;
        }
      });
      return params;
    }

    function applyParamValues(obj) {
      if (!obj || typeof obj !== "object") return;
      paramsRow.querySelectorAll("input[data-param-key]").forEach(function (input) {
        var k = input.dataset.paramKey;
        if (obj[k] != null) input.value = String(obj[k]);
      });
    }

    function fillSelect(strategies) {
      catalog = strategies || [];
      selectEl.innerHTML = "";
      const list = catalog.length
        ? catalog
        : [
            {
              id: "momentum",
              name: "momentum",
              family: "momentum",
              runnable: true,
            },
            {
              id: "buy_once",
              name: "buy_once",
              family: "demo",
              runnable: true,
            },
            {
              id: "inventory_mm",
              name: "inventory_mm",
              family: "market_making",
              runnable: true,
            },
          ];
      const byFamily = {};
      list.forEach(function (s) {
        const fam = s.family || "other";
        if (!byFamily[fam]) byFamily[fam] = [];
        byFamily[fam].push(s);
      });
      Object.keys(byFamily)
        .sort(function (a, b) {
          const la = (byFamily[a][0] && byFamily[a][0].family_label_es) || a;
          const lb = (byFamily[b][0] && byFamily[b][0].family_label_es) || b;
          return String(la).localeCompare(String(lb), "es");
        })
        .forEach(function (fam) {
          const group = document.createElement("optgroup");
          const sample = byFamily[fam][0];
          group.label = (sample && sample.family_label_es) || fam;
          byFamily[fam].forEach(function (s) {
            const opt = document.createElement("option");
            opt.value = s.id;
            const stub = s.runnable === false ? " [stub]" : "";
            opt.textContent = (s.name || s.id) + stub;
            opt.disabled = s.runnable === false;
            if (s.description) opt.title = s.description;
            group.appendChild(opt);
          });
          selectEl.appendChild(group);
        });
      if (!catalog.length) catalog = list;
      renderParams();
    }

    function syncModeUI() {
      var hist = isHistorical();
      var badge = root.querySelector("#bt-mode-badge");
      var sub = root.querySelector("#bt-head-sub");
      [
        "#bt-venue-wrap",
        "#bt-market-wrap",
        "#bt-coin-wrap",
        "#bt-period-wrap",
        "#bt-interval-wrap",
      ].forEach(function (sel) {
        var el = root.querySelector(sel);
        if (el) el.hidden = !hist;
      });
      var nb = root.querySelector("#bt-nbars-wrap");
      if (nb) nb.hidden = hist;
      if (badge) {
        badge.className =
          "data-badge " + (hist ? "data-badge-real" : "data-badge-synth");
        badge.textContent = hist ? "HISTÓRICO" : "SINTÉTICO";
      }
      if (sub) {
        sub.innerHTML =
          '<span class="data-badge ' +
          (hist ? "data-badge-real" : "data-badge-synth") +
          '" id="bt-mode-badge">' +
          (hist ? "HISTÓRICO" : "SINTÉTICO") +
          "</span> " +
          (hist
            ? "una moneda · estrategia · período · LIVE bloqueado"
            : "velas inventadas · debug estrategia");
      }
      refreshNBarsHint();
      updateContextLine();
    }

    function refreshNBarsHint() {
      var hint = root.querySelector("#bt-nbars-hint");
      if (!hint) return;
      if (!isHistorical()) {
        hint.textContent =
          "≈ " + (root.querySelector("#bt-nbars").value || "?") + " velas sintéticas";
        return;
      }
      var days = Number(root.querySelector("#bt-period").value) || 30;
      var iv = root.querySelector("#bt-interval").value || "1h";
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
          "Sintético · " +
          (selectEl.value || "?") +
          " · " +
          (root.querySelector("#bt-nbars").value || "?") +
          " velas inventadas (no es mercado real)";
        return;
      }
      var coin = (root.querySelector("#bt-coin").value || "").trim().toUpperCase();
      var venue = root.querySelector("#bt-venue").value;
      var mt = root.querySelector("#bt-market").value;
      var days = root.querySelector("#bt-period").value;
      var iv = root.querySelector("#bt-interval").value;
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
        " · " +
        (selectEl.value || "?") +
        " · capital " +
        money(root.querySelector("#bt-capital").value);
    }

    function readFormParams() {
      var hist = isHistorical();
      var coin = (root.querySelector("#bt-coin").value || "").trim().toUpperCase();
      var venue = root.querySelector("#bt-venue").value;
      return {
        kind: "backtest",
        mode: hist ? "historical" : "synthetic",
        strategy_id: selectEl.value,
        strategy_params: collectParams(),
        venue: hist ? venue : null,
        underlying: hist ? coin : null,
        coin: hist ? coin : null,
        market_type: hist ? root.querySelector("#bt-market").value : null,
        interval: hist ? root.querySelector("#bt-interval").value : null,
        period_days: hist
          ? Number(root.querySelector("#bt-period").value) || 30
          : null,
        n_bars: hist
          ? null
          : parseInt(root.querySelector("#bt-nbars").value, 10) || 120,
        initial_cash: Number(root.querySelector("#bt-capital").value) || 10000,
        pairs: hist && coin
          ? [{ venue: venue, underlying: coin, ticker: coin }]
          : [],
      };
    }

    function buildBtMemo(data, formParams) {
      var p = formParams || readFormParams();
      var ctx = (data && data.context) || {};
      var br = (data && data.bar_range) || {};
      var lines = [];
      lines.push("QUANTLAB — MEMORANDO DE BACKTEST");
      lines.push("Fecha: " + new Date().toLocaleString("es-AR"));
      lines.push("");
      lines.push("=== QUÉ SE CORRIÓ ===");
      lines.push(
        "Modo: " +
          (p.mode === "synthetic" || ctx.mode === "synthetic"
            ? "SINTÉTICO (velas inventadas)"
            : "HISTÓRICO (MD público)")
      );
      lines.push(
        "Moneda: " +
          (ctx.underlying || p.underlying || p.coin || "—")
      );
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
          (br.start
            ? " · " + br.start + " → " + (br.end || "")
            : "")
      );
      lines.push(
        "Fuente datos: " +
          (ctx.data_source || (data && data.data_source) || "—")
      );
      lines.push(
        "Instrumento: " +
          (ctx.instrument_id || (data && data.instrument_id) || "—")
      );
      lines.push(
        "Estrategia: " +
          (data && data.strategy_id ? data.strategy_id : p.strategy_id || "—")
      );
      lines.push(
        "Params: " +
          JSON.stringify(
            (data && data.params) || p.strategy_params || {}
          )
      );
      lines.push(
        "Capital inicial: " +
          money(data && data.initial_equity != null ? data.initial_equity : p.initial_cash)
      );
      lines.push("");
      lines.push("=== RESULTADO ===");
      lines.push("Capital final: " + money(data && data.final_equity));
      lines.push("PnL: " + money(data && data.pnl));
      lines.push("Fees: " + money(data && data.total_fees));
      lines.push(
        "Fills / órdenes: " +
          (data && data.n_fills != null ? data.n_fills : "—") +
          " / " +
          (data && data.n_orders != null ? data.n_orders : "—")
      );
      lines.push("Veredicto: " + ((data && data.verdict_es) || "—"));
      lines.push(
        "report_id: " + ((data && data.report_id) || "—")
      );
      lines.push("");
      lines.push("LIVE_BLOCKED=True · sin órdenes al venue");

      var csv = [
        "campo,valor",
        "mode," + (ctx.mode || p.mode || ""),
        "moneda," + (ctx.underlying || p.underlying || ""),
        "venue," + (ctx.venue || p.venue || ""),
        "market_type," + (ctx.market_type || p.market_type || ""),
        "interval," + (ctx.interval || p.interval || ""),
        "period_days," + (ctx.period_days != null ? ctx.period_days : p.period_days || ""),
        "n_bars," + ((data && data.n_bars) || ""),
        "data_source," + ((data && data.data_source) || ""),
        "strategy_id," + ((data && data.strategy_id) || p.strategy_id || ""),
        "initial_equity," + ((data && data.initial_equity) || ""),
        "final_equity," + ((data && data.final_equity) || ""),
        "pnl," + ((data && data.pnl) || ""),
        "total_fees," + ((data && data.total_fees) || ""),
        "n_fills," + ((data && data.n_fills) || ""),
        "report_id," + ((data && data.report_id) || ""),
      ].join("\n");

      var coin = ctx.underlying || p.underlying || p.coin || "synth";
      return {
        kind: "backtest",
        title:
          "Backtest · " +
          coin +
          " · " +
          ((data && data.strategy_id) || p.strategy_id || ""),
        text: lines.join("\n"),
        csv: csv,
        filenameBase:
          "quantlab-backtest-" +
          String(coin).toLowerCase() +
          "-" +
          stampNow(),
      };
    }

    function presentBtMemo(data, formParams, doRegister) {
      if (!data) return;
      var params = formParams || readFormParams();
      var memo = buildBtMemo(data, params);
      if (doRegister && global.QLSimRegistry && typeof global.QLSimRegistry.add === "function") {
        try {
          global.QLSimRegistry.add({
            kind: "backtest",
            title: memo.title,
            summary:
              (params.underlying || params.coin || params.mode || "") +
              " · " +
              (params.strategy_id || "") +
              " · PnL " +
              money(data.pnl),
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

    function renderSummary(data) {
      if (!data) {
        summaryEl.innerHTML = "";
        return;
      }
      var ctx = data.context || {};
      var br = data.bar_range || {};
      var badge =
        ctx.mode === "synthetic" || data.mode === "synthetic"
          ? '<span class="data-badge data-badge-synth">SINTÉTICO</span>'
          : '<span class="data-badge data-badge-real">HISTÓRICO</span>';
      summaryEl.innerHTML =
        '<div class="bt-cards mono">' +
        badge +
        " <strong>" +
        esc(ctx.underlying || data.underlying || "—") +
        "</strong> · " +
        esc(ctx.venue || data.venue || "lab") +
        "/" +
        esc(ctx.market_type || data.market_type || data.data_source || "") +
        "<br/>" +
        "Estrategia <strong>" +
        esc(data.strategy_id || "—") +
        "</strong> · " +
        esc(String(data.n_bars != null ? data.n_bars : "?")) +
        " velas" +
        (br.start
          ? " · " + esc(br.start) + " → " + esc(br.end || "")
          : "") +
        "<br/>" +
        "Inicial " +
        money(data.initial_equity) +
        " → Final " +
        money(data.final_equity) +
        " · PnL " +
        money(data.pnl) +
        " · Fees " +
        money(data.total_fees) +
        "<br/>" +
        "Fills " +
        esc(String(data.n_fills != null ? data.n_fills : "—")) +
        " · " +
        esc(data.verdict_es || "") +
        (data.report_id
          ? '<br/><span class="muted">report_id=' +
            esc(data.report_id) +
            "</span>"
          : "") +
        "</div>";
    }

    function loadCoinSuggest() {
      if (!QLApi.simUniverse) return;
      var mt = root.querySelector("#bt-market").value || "futures";
      QLApi.simUniverse({ market_type: mt, hl_live: true })
        .then(function (d) {
          var venues = (d && d.venues) || {};
          var set = {};
          Object.keys(venues).forEach(function (vid) {
            var list = venues[vid] || [];
            list.forEach(function (row) {
              var u =
                (row && (row.underlying || row.ticker || row.symbol)) || "";
              u = String(u).toUpperCase().replace(/USDT$/, "");
              if (u) set[u] = true;
            });
          });
          coinSuggest = Object.keys(set).sort();
        })
        .catch(function () {
          coinSuggest = [];
        });
    }

    selectEl.addEventListener("change", function () {
      renderParams();
      updateContextLine();
    });
    root.querySelector("#bt-mode").addEventListener("change", syncModeUI);
    ["#bt-period", "#bt-interval", "#bt-nbars", "#bt-capital", "#bt-venue", "#bt-market"].forEach(
      function (sel) {
        var el = root.querySelector(sel);
        if (!el) return;
        el.addEventListener("change", function () {
          if (sel === "#bt-market") loadCoinSuggest();
          refreshNBarsHint();
          updateContextLine();
        });
        el.addEventListener("input", updateContextLine);
      }
    );
    root.querySelector("#bt-coin").addEventListener("input", updateContextLine);
    root.querySelector("#bt-coin").addEventListener("change", updateContextLine);

    root.querySelector("#bt-run").addEventListener("click", function () {
      const strategy = selectEl.value;
      const hist = isHistorical();
      const formParams = readFormParams();

      if (hist && !formParams.underlying) {
        QLLabUI.setStatus(status, false, "escribí una moneda (ej. BTC)");
        return;
      }

      function startBt(handle) {
        status.textContent = "ejecutando…";
        status.className = "mono muted";
        btnMc.disabled = true;
        btnMemo.disabled = true;
        var fetchOpts =
          handle && handle.signal ? { signal: handle.signal } : undefined;
        var body;
        if (hist) {
          body = {
            mode: "historical",
            strategy_id: strategy,
            params: formParams.strategy_params,
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
            strategy_id: strategy,
            n_bars: formParams.n_bars,
            params: formParams.strategy_params,
            initial_cash: formParams.initial_cash,
          };
        }
        QLApi.labBacktest(body, fetchOpts)
          .then(function (data) {
            lastResult = data;
            lastParams = formParams;
            QLLabUI.setStatus(status, true, "OK");
            renderSummary(data);
            out.innerHTML = QLLabUI.preJson(data);
            const rid = data.report_id || null;
            btnMc.disabled = !rid;
            btnMemo.disabled = false;
            presentBtMemo(data, formParams, true);
            updateContextLine();
            if (data.context) {
              var c = data.context;
              ctxEl.textContent =
                (c.underlying || formParams.underlying || "synth") +
                " · " +
                (c.venue || c.data_source || "") +
                " · " +
                (c.n_bars != null ? c.n_bars + " velas" : "") +
                (c.bar_range && c.bar_range.start
                  ? " · " + c.bar_range.start + " → " + (c.bar_range.end || "")
                  : "");
            }
          })
          .catch(function (err) {
            lastResult = null;
            if (QLLabUI.isAbortError && QLLabUI.isAbortError(err)) {
              QLLabUI.setStatus(status, false, "detenido");
            } else {
              QLLabUI.setStatus(status, false, err.message || String(err));
            }
            out.innerHTML = "";
            summaryEl.innerHTML = "";
            btnMc.disabled = true;
            btnMemo.disabled = true;
          })
          .then(function () {
            if (handle) handle.end();
          });
      }

      var summary =
        (hist
          ? formParams.underlying +
            " · " +
            formParams.venue +
            " · " +
            formParams.period_days +
            "d"
          : "sintético · " + formParams.n_bars + " bars") +
        " · " +
        strategy;

      if (!global.QLRunGate) {
        startBt(null);
        return;
      }
      QLRunGate.begin({
        kind: "backtest",
        label: "Backtest",
        summary: summary,
        busyRoot: root,
      }).then(function (handle) {
        if (!handle) return;
        startBt(handle);
      });
    });

    if (global.QLRunGate) {
      QLRunGate.bindStopButton(root.querySelector("#bt-stop"), {
        kinds: ["backtest"],
      });
      QLRunGate.bindBusyHost(root, { kinds: ["backtest"] });
    }

    btnMemo.addEventListener("click", function () {
      if (!lastResult) {
        QLLabUI.setStatus(status, false, "sin corrida — corré primero");
        return;
      }
      presentBtMemo(lastResult, lastParams || readFormParams(), false);
    });

    btnMc.addEventListener("click", function () {
      if (!lastResult || !lastResult.report_id) return;
      const p = lastParams || readFormParams();
      const prefill = {
        backtest_id: lastResult.report_id,
        strategy_id: lastResult.strategy_id || selectEl.value,
        n_bars: lastResult.n_bars || null,
        mode: "normal",
      };
      if (p.mode === "historical" && p.underlying) {
        prefill.sim_context = {
          kind: "backtest",
          coin: p.underlying,
          strategy_id: p.strategy_id,
          strategy_params: p.strategy_params,
          market_type: p.market_type,
          interval: p.interval,
          period_days: p.period_days,
          pairs: p.pairs,
          initial_capital: p.initial_cash,
          capital_mode: "fixed",
        };
        // Preferir handoff histórico sobre BT residual sintético
        prefill.backtest_id = "";
        prefill.mode = "technical_lab";
      }
      if (global.QLNav) {
        global.QLNav.open("montecarlo", {
          prefill: prefill,
          message:
            "Desde Backtest " +
            (p.underlying || lastResult.report_id || ""),
        });
      } else if (global.QLShell) {
        global.QLShell.open("montecarlo", { prefill: prefill });
      }
    });

    root.querySelector("#bt-to-sim").addEventListener("click", function () {
      var p = readFormParams();
      if (!global.QLShell) return;
      global.QLShell.open("simulator", {
        prefill: {
          pairs: p.pairs,
          venue: p.venue,
          market_type: p.market_type,
          interval: p.interval,
          period_days: p.period_days,
          strategy_id: p.strategy_id,
          message: "Desde Backtest",
        },
      });
    });

    root.applyPrefill = function (prefill) {
      if (!prefill || typeof prefill !== "object") return;
      if (prefill.mode === "synthetic") {
        root.querySelector("#bt-mode").value = "synthetic";
      } else if (
        prefill.mode === "historical" ||
        prefill.underlying ||
        prefill.coin ||
        (prefill.pairs && prefill.pairs.length)
      ) {
        root.querySelector("#bt-mode").value = "historical";
      }
      syncModeUI();
      if (prefill.venue) root.querySelector("#bt-venue").value = prefill.venue;
      if (prefill.market_type) {
        root.querySelector("#bt-market").value = prefill.market_type;
      }
      var coin =
        prefill.underlying ||
        prefill.coin ||
        (prefill.pairs &&
          prefill.pairs[0] &&
          (prefill.pairs[0].underlying || prefill.pairs[0].ticker));
      if (coin) root.querySelector("#bt-coin").value = String(coin).toUpperCase();
      if (prefill.interval) {
        root.querySelector("#bt-interval").value = prefill.interval;
      }
      if (prefill.period_days != null) {
        root.querySelector("#bt-period").value = String(prefill.period_days);
      }
      if (prefill.n_bars != null) {
        root.querySelector("#bt-nbars").value = String(prefill.n_bars);
      }
      if (prefill.initial_cash != null) {
        root.querySelector("#bt-capital").value = String(prefill.initial_cash);
      }
      if (prefill.strategy_id) {
        selectEl.value = prefill.strategy_id;
        renderParams();
      }
      if (prefill.strategy_params) applyParamValues(prefill.strategy_params);
      if (prefill.params) applyParamValues(prefill.params);
      refreshNBarsHint();
      updateContextLine();
      if (prefill.message) {
        QLLabUI.setStatus(status, true, prefill.message);
      }
    };

    root.applyNavFocus = function () {
      if (!global.QLNav) return;
      var focus = global.QLNav.takeFocus("backtest");
      if (!focus) return;
      if (focus.prefill) root.applyPrefill(focus.prefill);
      if (focus.message) QLLabUI.setStatus(status, true, focus.message);
    };

    root.refresh = async function () {
      try {
        const res = await QLApi.labStrategies();
        fillSelect(res.strategies || []);
      } catch (err) {
        fillSelect([]);
      }
      loadCoinSuggest();
      syncModeUI();
    };

    root.refresh();
    if (root.applyNavFocus) root.applyNavFocus();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBacktestPane = createBacktestPane;
})(window);
