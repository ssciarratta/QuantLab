/** Registro acumulable de simulaciones — ventana WM (arrastrar / tamaño / min / ×). */
(function (global) {
  "use strict";

  var STORAGE_KEY = "ql_sim_registry_v1";
  var WIN_ID = "sim_registry";
  var MAX_ENTRIES = 80;
  var contentEl = null;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function save(list) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ENTRIES)));
    } catch (e) {}
  }

  function stampId(kind) {
    return kind + "_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  function kindLabel(kind) {
    if (kind === "compare") return "Comparar";
    if (kind === "rank") return "Ranking";
    if (kind === "montecarlo") return "Monte Carlo";
    if (kind === "backtest") return "Backtest";
    if (kind === "optimize") return "Optimizer";
    return kind || "?";
  }

  function syncBadge() {
    var n = load().length;
    var btn = document.getElementById("sb-sim-registry");
    if (btn) {
      btn.textContent = n ? "Sims (" + n + ")" : "Sims";
      btn.classList.toggle("sb-sim-registry-hot", n > 0);
    }
  }

  function getWm() {
    return global.QLShell && global.QLShell.wm ? global.QLShell.wm : null;
  }

  function openMemo(memo, params) {
    if (!memo) return;
    var wm = getWm();
    var winId = "sim_memo_" + (memo.kind || "run") + "_view";
    var csvName = (memo.filenameBase || "quantlab-memo") + ".csv";
    var txtName = (memo.filenameBase || "quantlab-memo") + ".txt";
    var fullText = memo.text || "";
    if (params && typeof params === "object" && Object.keys(params).length) {
      fullText +=
        "\n\n— PARÁMETROS SELECCIONADOS (JSON) —\n" +
        JSON.stringify(params, null, 2);
    }
    var csvUrl = URL.createObjectURL(
      new Blob(["\ufeff" + (memo.csv || "")], { type: "text/csv;charset=utf-8" })
    );
    var txtUrl = URL.createObjectURL(
      new Blob([fullText], { type: "text/plain;charset=utf-8" })
    );
    var waText =
      fullText.length > 3500
        ? fullText.slice(0, 3400) +
          "\n\n…(recortado)\nDescargá el CSV/TXT completo para verificación."
        : fullText;
    var waHref =
      "https://api.whatsapp.com/send?text=" + encodeURIComponent(waText);

    var pane = document.createElement("div");
    pane.className = "pane-sim-memo";
    pane.innerHTML =
      '<div class="sim-memo-toolbar">' +
      '<a class="btn" href="' +
      csvUrl +
      '" download="' +
      esc(csvName) +
      '">Descargar CSV</a> ' +
      '<a class="btn secondary" href="' +
      txtUrl +
      '" download="' +
      esc(txtName) +
      '">Descargar TXT</a> ' +
      '<button type="button" class="btn secondary" id="reg-memo-copy">Copiar texto</button> ' +
      '<a class="btn secondary" href="' +
      waHref +
      '" target="_blank" rel="noopener noreferrer">Compartir WhatsApp</a>' +
      (memo.nRows != null
        ? '<span class="muted mono" style="font-size:0.72em">' +
          esc(memo.nRows) +
          " filas CSV</span>"
        : "") +
      "</div>" +
      '<p class="muted" style="font-size:0.75em;margin:0.35rem 0">' +
      "Memorando + parámetros · arrastrá bordes · × cierra." +
      "</p>" +
      '<pre class="sim-memo-body mono"></pre>';
    pane.querySelector(".sim-memo-body").textContent = fullText;
    var copyBtn = pane.querySelector("#reg-memo-copy");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var done = function () {
          copyBtn.textContent = "Copiado ✓";
          setTimeout(function () {
            copyBtn.textContent = "Copiar texto";
          }, 1600);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(fullText).then(done).catch(function () {
            window.prompt("Copiá:", fullText);
          });
        } else {
          window.prompt("Copiá:", fullText);
        }
      });
    }

    if (wm && typeof wm.open === "function") {
      if (wm.windows && wm.windows.has(winId)) wm.close(winId);
      var ws = wm.workspace;
      var ww = (ws && ws.clientWidth) || 900;
      var wh = (ws && ws.clientHeight) || 700;
      var w = Math.min(640, Math.max(420, ww - 80));
      var h = Math.min(560, Math.max(360, wh - 100));
      var x = Math.max(24, Math.floor((ww - w) / 2));
      var y = Math.max(24, Math.floor((wh - h) / 3));
      wm.open(winId, memo.title || "Memorando", pane, { x: x, y: y, w: w, h: h });
      if (typeof wm.focus === "function") wm.focus(winId);
      if (typeof wm.bringToFront === "function") {
        try {
          wm.bringToFront(winId);
        } catch (e) {}
      }
    } else {
      document.body.appendChild(pane);
    }
  }

  function findEntry(id) {
    return load().find(function (x) {
      return x.id === id;
    });
  }

  /** Prefill limpio para Simulador a partir de params guardados en el registro. */
  function buildSimulatorPrefill(params) {
    params = params || {};
    var meta = params.meta || {};
    var common = params.common || {};
    var ctx = params.sim_context && typeof params.sim_context === "object"
      ? params.sim_context
      : {};
    function pick() {
      for (var i = 0; i < arguments.length; i++) {
        if (arguments[i] != null && arguments[i] !== "") return arguments[i];
      }
      return null;
    }
    var pairs = [];
    if (Array.isArray(params.pairs) && params.pairs.length) {
      pairs = params.pairs.slice();
    } else if (Array.isArray(ctx.pairs) && ctx.pairs.length) {
      pairs = ctx.pairs.map(function (p) {
        return {
          venue: p.venue,
          underlying: p.underlying || p.ticker,
          ticker: p.ticker || p.underlying,
        };
      });
    }
    var prefill = {
      kind: params.kind || ctx.kind || "compare",
      market_type: pick(
        meta.market_type,
        common.market_type,
        params.market_type,
        ctx.market_type
      ),
      interval: pick(meta.interval, common.interval, params.interval, ctx.interval),
      period_days: pick(
        meta.period_days,
        common.period_days,
        params.period_days,
        ctx.period_days
      ),
      leverage: pick(meta.leverage, common.leverage, params.leverage, ctx.leverage),
      capital_mode: pick(
        meta.capital_mode,
        common.capital_mode,
        params.capital_mode,
        ctx.capital_mode
      ),
      initial_capital: pick(
        meta.initial_capital,
        common.initial_capital,
        params.initial_capital,
        ctx.initial_capital
      ),
      per_trade_usd: pick(
        meta.per_trade_usd,
        common.per_trade_usd,
        params.per_trade_usd,
        ctx.per_trade_usd
      ),
      bench_pct: pick(meta.bench_pct, params.bench_pct, ctx.bench_pct),
      annual_bench_rate: pick(common.annual_bench_rate, params.annual_bench_rate),
      liq: pick(meta.liq, common.simulate_liquidation, params.liq, ctx.liq),
      funding: pick(meta.funding, common.apply_funding, params.funding, ctx.funding),
      strategy_id: pick(
        params.strategy_id,
        common.strategy_id,
        ctx.strategy_id
      ),
      pairs: pairs,
      _from_registry: true,
    };
    if ((!prefill.pairs || !prefill.pairs.length) && params.venue && params.underlying) {
      prefill.venue = params.venue;
      prefill.underlying = params.underlying;
    }
    return prefill;
  }

  function focusPane(paneId) {
    try {
      var wm = getWm();
      if (!wm) return;
      if (wm.windows && wm.windows.has(paneId)) {
        var rec = wm.windows.get(paneId);
        if (
          rec &&
          rec.el &&
          rec.el.classList.contains("minimized") &&
          typeof wm.restore === "function"
        ) {
          wm.restore(paneId);
        }
        if (typeof wm.focus === "function") wm.focus(paneId);
        if (typeof wm.bringToFront === "function") wm.bringToFront(paneId);
      }
    } catch (e) {}
  }

  /**
   * Reabre Simulador o Monte Carlo con los mismos parámetros de esa corrida.
   * No re-ejecuta sola: deja el form listo para seguir trabajando.
   */
  function reopen(entry) {
    if (!entry) return;
    var params = entry.params || {};
    var kind =
      entry.kind || params.kind || (entry.memo && entry.memo.kind) || "run";
    if (!global.QLShell || typeof global.QLShell.open !== "function") {
      window.alert("Shell no listo — reintentá en un segundo.");
      return;
    }
    if (kind === "montecarlo") {
      var mcPrefill = {
        n_scenarios: params.n_scenarios,
        n_bars: params.n_bars,
        noise_bps: params.noise_bps,
        seed: params.seed,
        scan_id: params.scan_id,
        backtest_id: params.backtest_id,
        store_paths: params.store_paths,
        sim_context: params.sim_context || null,
        message:
          "Reabierto desde Mis simulaciones · " +
          (entry.title || "Monte Carlo"),
      };
      global.QLShell.open("montecarlo", { prefill: mcPrefill });
      focusPane("montecarlo");
      return;
    }
    if (kind === "backtest") {
      var btPrefill = {
        mode: params.mode || "historical",
        venue: params.venue,
        underlying: params.underlying || params.coin,
        coin: params.coin || params.underlying,
        market_type: params.market_type,
        interval: params.interval,
        period_days: params.period_days,
        n_bars: params.n_bars,
        initial_cash: params.initial_cash,
        strategy_id: params.strategy_id,
        strategy_params: params.strategy_params || params.params,
        pairs: params.pairs,
        message:
          "Reabierto desde Mis simulaciones · " +
          (entry.title || "Backtest"),
      };
      global.QLShell.open("backtest", { prefill: btPrefill });
      focusPane("backtest");
      return;
    }
    if (kind === "optimize") {
      var opPrefill = {
        mode: params.mode || "historical",
        venue: params.venue,
        underlying: params.underlying || params.coin,
        coin: params.coin || params.underlying,
        market_type: params.market_type,
        interval: params.interval,
        period_days: params.period_days,
        n_bars: params.n_bars,
        initial_cash: params.initial_cash,
        lookbacks: params.lookbacks,
        quantities: params.quantities,
        pairs: params.pairs,
        message:
          "Reabierto desde Mis simulaciones · " +
          (entry.title || "Optimizer"),
      };
      global.QLShell.open("optimize", { prefill: opPrefill });
      focusPane("optimize");
      return;
    }
    var prefill = buildSimulatorPrefill(params);
    if ((!prefill.pairs || !prefill.pairs.length) && !prefill.venue) {
      window.alert(
        "Esta entrada no tiene mercado/moneda guardados.\n" +
          "Abrí el memorando o volvé a correr Comparar/Ranking."
      );
    }
    global.QLShell.open("simulator", { prefill: prefill });
    focusPane("simulator");
  }

  function parseCsv(text) {
    if (!text || typeof text !== "string") return { headers: [], rows: [] };
    var lines = text.replace(/^\ufeff/, "").split(/\r?\n/).filter(function (ln) {
      return ln.trim().length > 0;
    });
    if (!lines.length) return { headers: [], rows: [] };
    function splitLine(ln) {
      var out = [];
      var cur = "";
      var inQ = false;
      for (var i = 0; i < ln.length; i++) {
        var ch = ln.charAt(i);
        if (ch === '"') {
          inQ = !inQ;
          continue;
        }
        if (ch === "," && !inQ) {
          out.push(cur);
          cur = "";
          continue;
        }
        cur += ch;
      }
      out.push(cur);
      return out;
    }
    var headers = splitLine(lines[0]);
    var rows = lines.slice(1).map(splitLine);
    return { headers: headers, rows: rows };
  }

  function fmtNum(v, digits) {
    if (v == null || v === "" || v === "undefined" || v === "null") return "—";
    var n = Number(v);
    if (!isFinite(n)) return String(v);
    return n.toLocaleString("es-AR", {
      minimumFractionDigits: digits != null ? digits : 2,
      maximumFractionDigits: digits != null ? digits : 2,
    });
  }

  function fmtPct(v) {
    if (v == null || v === "" || v === "undefined") return "—";
    var n = Number(v);
    if (!isFinite(n)) return String(v);
    return (
      n.toLocaleString("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + "%"
    );
  }

  function fmtDif(v) {
    if (v == null || v === "" || v === "undefined") return "—";
    var n = Number(v);
    if (!isFinite(n)) return String(v);
    var s = n.toLocaleString("es-AR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return (n > 0 ? "+" : "") + s;
  }

  function yesNo(v) {
    if (v === true || v === "true" || v === "1" || v === "sí" || v === "si") {
      return '<span class="status-bad">sí</span>';
    }
    if (v === false || v === "false" || v === "0" || v === "no" || v === "") {
      return '<span class="status-ok">no</span>';
    }
    var n = Number(v);
    if (isFinite(n) && n > 0) {
      return '<span class="status-bad">req ' + fmtNum(n) + "</span>";
    }
    return esc(String(v));
  }

  function entryMetaBits(e) {
    var p = e.params || {};
    var ctx = p.sim_context || {};
    var meta = p.meta || {};
    var common = p.common || {};
    return {
      coin:
        ctx.coin ||
        (ctx.coins && ctx.coins.join(", ")) ||
        p.coin ||
        (p.pairs && p.pairs[0] && (p.pairs[0].underlying || p.pairs[0].ticker)) ||
        "—",
      venues:
        (ctx.venues && ctx.venues.join(", ")) ||
        (p.markets && p.markets.join(", ")) ||
        p.venue ||
        (p.pairs &&
          p.pairs
            .map(function (x) {
              return x.venue;
            })
            .filter(Boolean)
            .join(", ")) ||
        "—",
      strategy:
        ctx.strategy_label ||
        ctx.strategy_id ||
        p.strategy_id ||
        common.strategy_id ||
        "—",
      leverage: ctx.leverage || meta.leverage || common.leverage || "—",
      interval: ctx.interval || meta.interval || common.interval || "—",
      period: ctx.period_days || meta.period_days || common.period_days || "—",
      capital_mode:
        ctx.capital_mode || meta.capital_mode || common.capital_mode || "—",
      initial:
        ctx.initial_capital != null
          ? ctx.initial_capital
          : meta.initial_capital != null
            ? meta.initial_capital
            : "—",
    };
  }

  function renderCompareTable(e) {
    var parsed = parseCsv(e.memo && e.memo.csv);
    var idx = {};
    parsed.headers.forEach(function (h, i) {
      idx[h] = i;
    });
    function cell(row, key) {
      var i = idx[key];
      return i == null ? "" : row[i];
    }
    if (!parsed.rows.length) {
      var m = entryMetaBits(e);
      return (
        '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
        "<th>Mercado</th><th>Modo</th><th>Moneda</th><th>x</th>" +
        "<th>Estrategia</th><th>TF</th><th>Período</th><th>Capital</th>" +
        "<th>Resumen</th></tr></thead><tbody><tr>" +
        "<td>" +
        esc(m.venues) +
        "</td><td>—</td><td>" +
        esc(m.coin) +
        "</td><td>" +
        esc(String(m.leverage)) +
        "</td><td>" +
        esc(m.strategy) +
        "</td><td>" +
        esc(String(m.interval)) +
        "</td><td>" +
        esc(String(m.period)) +
        "d</td><td>" +
        esc(String(m.capital_mode)) +
        "</td><td>" +
        esc(e.summary || "—") +
        "</td></tr></tbody></table>"
      );
    }
    var body = parsed.rows
      .map(function (row) {
        var falt = cell(row, "faltante");
        var liq = cell(row, "liquidated");
        return (
          "<tr>" +
          "<td>" +
          esc(cell(row, "venue") || "—") +
          "</td>" +
          "<td>" +
          esc(cell(row, "market_type") || "—") +
          "</td>" +
          "<td>" +
          esc(cell(row, "underlying") || "—") +
          "</td>" +
          "<td>" +
          esc(cell(row, "leverage") || "—") +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "capital_inicial")) +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "margen_trade")) +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "margen_pico")) +
          "</td>" +
          "<td>" +
          yesNo(falt) +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "capital_final_neto")) +
          "</td>" +
          "<td>" +
          fmtPct(cell(row, "pnl_pct")) +
          "</td>" +
          "<td>" +
          esc(cell(row, "n_ops") || "—") +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "fees_totales")) +
          "</td>" +
          "<td>" +
          fmtNum(cell(row, "fee_por_op")) +
          "</td>" +
          "<td>" +
          fmtDif(cell(row, "dif_vs_bench")) +
          "</td>" +
          "<td>" +
          yesNo(liq) +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
    return (
      '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
      "<th>Mercado</th><th>Modo</th><th>Moneda</th><th>x</th>" +
      "<th>Capital inicial</th><th>Margen/trade</th><th>Margen pico</th>" +
      "<th>¿Faltó?</th><th>Capital final (neto)</th><th>Rentab. %</th>" +
      "<th>Nº operaciones</th><th>Fees gastados</th><th>Fee/op</th>" +
      "<th>Dif. vs bench</th><th>Liq.</th>" +
      "</tr></thead><tbody>" +
      body +
      "</tbody></table>"
    );
  }

  function renderMcTable(e) {
    var p = e.params || {};
    var ctx = p.sim_context || {};
    var m = entryMetaBits(e);
    var media = "—";
    var sum = e.summary || "";
    var mm = sum.match(/media=([0-9.,]+)/i);
    if (mm) media = mm[1];
    return (
      '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
      "<th>Moneda</th><th>Mercado(s)</th><th>Estrategia</th><th>x</th>" +
      "<th>N escenarios</th><th>Velas/esc.</th><th>Media equity</th>" +
      "<th>Resumen</th></tr></thead><tbody><tr>" +
      "<td>" +
      esc(m.coin) +
      "</td><td>" +
      esc(m.venues) +
      "</td><td>" +
      esc(m.strategy) +
      "</td><td>" +
      esc(String(m.leverage)) +
      "</td><td>" +
      esc(String(p.n_scenarios != null ? p.n_scenarios : "—")) +
      "</td><td>" +
      esc(String(p.n_bars != null ? p.n_bars : "—")) +
      "</td><td>" +
      esc(media) +
      "</td><td>" +
      esc(sum || "—") +
      "</td></tr></tbody></table>"
    );
  }

  function renderBacktestTable(e) {
    var p = e.params || {};
    var m = entryMetaBits(e);
    var mode = p.mode === "synthetic" ? "sintético" : "histórico";
    return (
      '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
      "<th>Modo</th><th>Moneda</th><th>Mercado</th><th>Tipo</th>" +
      "<th>TF</th><th>Período</th><th>Estrategia</th><th>Resumen</th>" +
      "</tr></thead><tbody><tr>" +
      "<td>" +
      esc(mode) +
      "</td><td>" +
      esc(m.coin) +
      "</td><td>" +
      esc(p.venue || m.venues || "—") +
      "</td><td>" +
      esc(p.market_type || "—") +
      "</td><td>" +
      esc(String(m.interval)) +
      "</td><td>" +
      esc(
        p.period_days != null
          ? p.period_days + "d"
          : p.n_bars != null
            ? p.n_bars + " velas"
            : "—"
      ) +
      "</td><td>" +
      esc(m.strategy) +
      "</td><td>" +
      esc(e.summary || "—") +
      "</td></tr></tbody></table>"
    );
  }

  function renderOptimizeTable(e) {
    var p = e.params || {};
    var m = entryMetaBits(e);
    var mode = p.mode === "synthetic" ? "sintético" : "histórico";
    return (
      '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
      "<th>Modo</th><th>Moneda</th><th>Mercado</th><th>TF</th>" +
      "<th>Período</th><th>lookbacks</th><th>qty</th><th>Resumen</th>" +
      "</tr></thead><tbody><tr>" +
      "<td>" +
      esc(mode) +
      "</td><td>" +
      esc(m.coin) +
      "</td><td>" +
      esc(p.venue || m.venues || "—") +
      "</td><td>" +
      esc(String(m.interval)) +
      "</td><td>" +
      esc(
        p.period_days != null
          ? p.period_days + "d"
          : p.n_bars != null
            ? p.n_bars + " velas"
            : "—"
      ) +
      "</td><td>" +
      esc(
        Array.isArray(p.lookbacks) ? p.lookbacks.join(",") : p.lookbacks || "—"
      ) +
      "</td><td>" +
      esc(
        Array.isArray(p.quantities)
          ? p.quantities.join(",")
          : p.quantities || "—"
      ) +
      "</td><td>" +
      esc(e.summary || "—") +
      "</td></tr></tbody></table>"
    );
  }

  function renderRankTable(e) {
    var m = entryMetaBits(e);
    return (
      '<table class="sim-summary-table mono ql-sim-reg-table"><thead><tr>' +
      "<th>Moneda</th><th>Mercado(s)</th><th>x</th><th>TF</th>" +
      "<th>Período</th><th>Resumen</th></tr></thead><tbody><tr>" +
      "<td>" +
      esc(m.coin) +
      "</td><td>" +
      esc(m.venues) +
      "</td><td>" +
      esc(String(m.leverage)) +
      "</td><td>" +
      esc(String(m.interval)) +
      "</td><td>" +
      esc(String(m.period)) +
      "d</td><td>" +
      esc(e.summary || "—") +
      "</td></tr></tbody></table>"
    );
  }

  function renderEntryBlock(e) {
    var when = e.created_at
      ? new Date(e.created_at).toLocaleString("es-AR")
      : "—";
    var kind = e.kind || "run";
    var tableHtml =
      kind === "montecarlo"
        ? renderMcTable(e)
        : kind === "rank"
          ? renderRankTable(e)
          : kind === "backtest"
            ? renderBacktestTable(e)
            : kind === "optimize"
              ? renderOptimizeTable(e)
              : renderCompareTable(e);
    return (
      '<section class="ql-sim-reg-block" data-id="' +
      esc(e.id) +
      '">' +
      '<div class="ql-sim-reg-head">' +
      '<span class="data-badge data-badge-real">' +
      esc(kindLabel(kind).toUpperCase()) +
      "</span> " +
      '<span class="ql-sim-reg-title mono">' +
      esc(e.title || e.summary || e.id) +
      "</span> " +
      '<span class="muted mono ql-sim-reg-when">' +
      esc(when) +
      "</span>" +
      '<span class="ql-sim-reg-actions">' +
      '<button type="button" class="btn ql-sim-registry-reopen" data-id="' +
      esc(e.id) +
      '" title="Abrir Simulador/MC con los mismos parámetros">Reabrir</button> ' +
      '<button type="button" class="btn secondary ql-sim-registry-memo" data-id="' +
      esc(e.id) +
      '" title="Ver memorando">Memo</button>' +
      "</span></div>" +
      tableHtml +
      "</section>"
    );
  }

  function renderList() {
    if (!contentEl) return;
    var listEl = contentEl.querySelector(".ql-sim-registry-list");
    var countEl = contentEl.querySelector(".ql-sim-registry-count");
    var list = load();
    if (countEl) countEl.textContent = String(list.length);
    syncBadge();
    if (!listEl) return;
    if (!list.length) {
      listEl.innerHTML =
        '<p class="muted" style="font-size:0.78em;margin:0.5rem">' +
        "Todavía no hay corridas.<br/>Corré <strong>Comparar</strong>, " +
        "<strong>Ranking</strong>, <strong>Backtest</strong>, " +
        "<strong>Optimizer</strong> o <strong>Monte Carlo</strong>." +
        "</p>";
      return;
    }
    listEl.innerHTML = list.map(renderEntryBlock).join("");
    listEl.querySelectorAll(".ql-sim-registry-reopen").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var hit = findEntry(btn.getAttribute("data-id"));
        if (hit) reopen(hit);
      });
    });
    listEl.querySelectorAll(".ql-sim-registry-memo").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var hit = findEntry(btn.getAttribute("data-id"));
        if (hit && hit.memo) openMemo(hit.memo, hit.params);
      });
    });
  }

  function buildContent() {
    var root = document.createElement("div");
    root.className = "pane-sim-registry";
    root.innerHTML =
      '<div class="ql-sim-registry-toolbar">' +
      '<span class="muted" style="font-size:0.72em;flex:1">' +
      "Mis simulaciones · vista tipo HISTÓRICO · Reabrir = params · Memo" +
      "</span>" +
      '<span class="mono muted ql-sim-registry-count">0</span> ' +
      '<button type="button" class="btn secondary ql-sim-registry-clear" title="Vaciar historial">Vaciar</button>' +
      "</div>" +
      '<div class="ql-sim-registry-list"></div>';
    root.querySelector(".ql-sim-registry-clear").addEventListener("click", function () {
      if (!window.confirm("¿Vaciar el historial de simulaciones de este navegador?")) {
        return;
      }
      save([]);
      renderList();
    });
    root.refresh = renderList;
    root.dispose = function () {
      if (contentEl === root) contentEl = null;
    };
    contentEl = root;
    renderList();
    return root;
  }

  /**
   * Abre / enfoca / restaura la ventana del registro (como cualquier panel QL).
   * @param {object} [opts] geometría {x,y,w,h,minimized,maximized,z}
   */
  function openWindow(opts) {
    var wm = getWm();
    if (!wm || typeof wm.open !== "function") {
      setTimeout(function () {
        openWindow(opts);
      }, 120);
      return null;
    }
    opts = opts || {};
    if (wm.windows && wm.windows.has(WIN_ID)) {
      if (typeof wm.focus === "function") wm.focus(WIN_ID);
      var rec = wm.windows.get(WIN_ID);
      if (rec && rec.el && rec.el.classList.contains("minimized") && typeof wm.restore === "function") {
        wm.restore(WIN_ID);
      }
      if (rec && rec.body && rec.body.firstElementChild) {
        contentEl = rec.body.firstElementChild;
        if (typeof contentEl.refresh === "function") contentEl.refresh();
        else renderList();
      }
      if (typeof wm.bringToFront === "function") {
        try {
          wm.bringToFront(WIN_ID);
        } catch (e) {}
      }
      syncBadge();
      return rec;
    }
    var pane = buildContent();
    var defaults = { x: 20, y: 40, w: 980, h: 560 };
    var geo = {
      x: opts.x != null ? opts.x : defaults.x,
      y: opts.y != null ? opts.y : defaults.y,
      w: opts.w != null ? opts.w : defaults.w,
      h: opts.h != null ? opts.h : defaults.h,
    };
    if (opts.z != null) geo.z = opts.z;
    if (opts.minimized) geo.minimized = true;
    if (opts.maximized) geo.maximized = true;
    return wm.open(WIN_ID, "Mis simulaciones", pane, geo);
  }

  function show() {
    return openWindow();
  }

  function add(entry) {
    if (!entry || !entry.memo) return null;
    var list = load();
    var item = {
      id: entry.id || stampId(entry.kind || "run"),
      kind: entry.kind || entry.memo.kind || "run",
      title: entry.title || entry.memo.title || "Simulación",
      summary: entry.summary || "",
      created_at: entry.created_at || new Date().toISOString(),
      params: entry.params || {},
      memo: entry.memo,
    };
    list.unshift(item);
    save(list);
    // Guardar en silencio: NO abrir ni traer al frente «Mis simulaciones».
    // El usuario se queda viendo el resultado en el panel que corrió.
    // Si la ventana ya está abierta detrás, solo refrescar la lista.
    if (wm && wm.windows && wm.windows.has(WIN_ID)) {
      var rec = wm.windows.get(WIN_ID);
      if (rec && rec.body && rec.body.firstElementChild) {
        contentEl = rec.body.firstElementChild;
        if (typeof contentEl.refresh === "function") contentEl.refresh();
        else renderList();
      } else {
        renderList();
      }
    }
    syncBadge();
    return item;
  }

  function init() {
    syncBadge();
    var sb = document.getElementById("sb-sim-registry");
    if (sb && !sb._qlSimBound) {
      sb._qlSimBound = true;
      sb.addEventListener("click", function () {
        if (global.QLShell && typeof global.QLShell.open === "function") {
          global.QLShell.open("sim_registry");
        } else {
          show();
        }
      });
    }
  }

  global.QLSimRegistry = {
    WIN_ID: WIN_ID,
    init: init,
    add: add,
    openMemo: openMemo,
    reopen: reopen,
    openWindow: openWindow,
    show: show,
    list: load,
    render: renderList,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
