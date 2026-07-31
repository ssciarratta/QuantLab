/** Panel Monte Carlo — robustez trazable (schema v2+ / corrección post-mini-lab). */
(function (global) {
  "use strict";

  var CONFIRM_LARGE_N = 100000;
  var ASYNC_N = 5000;
  var ESTIMATE_N = 1000;
  var MAX_TRAJECTORIES = 16;
  var POLL_MS = 500;

  var SCENARIO_PRESETS = [
    { id: "rapido", label: "Rápido", n: 100 },
    { id: "exploratorio", label: "Exploratorio", n: 1000 },
    { id: "estandar", label: "Estándar", n: 10000 },
    { id: "profundo", label: "Profundo", n: 100000 },
    { id: "extremo", label: "Extremo", n: 1000000 },
  ];

  function createMonteCarloPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-montecarlo";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head">' +
      "<h3>Monte Carlo</h3>" +
      '<p class="muted pane-sub">Robustez bajo supuestos · no predice precios</p>' +
      "</div>" +
      '<div id="mc-source-banner" class="mc-source-banner" role="status">' +
      '<strong>Origen:</strong> <span id="mc-source-summary">Sin simulación ligada — modo técnico demo.</span>' +
      '<div id="mc-source-detail" class="mc-source-detail muted mono"></div>' +
      "</div>" +
      '<div class="pane-toolbar">' +
      '<label title="Cantidad de escenarios independientes">Escenarios' +
      '<input id="mc-n" type="number" value="1000" min="2" max="1000000" step="1" /></label>' +
      '<label title="Velas perturbadas por escenario">Velas/esc.' +
      '<input id="mc-bars" type="number" value="60" min="8" max="500" /></label>' +
      '<label title="10 bps = 0,10 %">Ruido bps' +
      '<input id="mc-noise" type="number" value="10" min="0" max="500" step="1" /></label>' +
      '<label title="Misma seed = mismo resultado">Seed' +
      '<input id="mc-seed" type="number" value="42" /></label>' +
      '<label title="Opcional — vincula Scan">scan_id' +
      '<input id="mc-scan" type="text" placeholder="opcional" /></label>' +
      '<label title="Opcional — vincula Backtest">backtest_id' +
      '<input id="mc-bt" type="text" placeholder="opcional" /></label>' +
      "</div>" +
      '<div class="pane-row" id="mc-presets" style="gap:0.25rem;flex-wrap:wrap;margin:0.15rem 0"></div>' +
      '<div class="pane-actions">' +
      '<label class="muted" title="Guarda hasta 16 curvas. No limita escenarios.">' +
      '<input type="checkbox" id="mc-paths" /> trayectorias</label>' +
      '<button type="button" class="btn" id="mc-run">Simular</button>' +
      '<button type="button" class="btn secondary" id="mc-memo" title="Reabrir memorando de la última corrida">Ver memorando</button> ' +
      '<button type="button" class="btn secondary" id="mc-refresh">Actualizar</button>' +
      '<button type="button" class="btn secondary" id="mc-copy-id">Copiar ID</button>' +
      '<button type="button" class="btn secondary" id="mc-cancel" disabled hidden>Cancelar</button>' +
      '<span class="mono muted" id="mc-bars-duration"></span>' +
      '<span class="mono" id="mc-status">—</span>' +
      "</div>" +
      '<p class="muted" id="mc-warn" style="margin:0.25rem 0 0"></p>' +
      '<div id="mc-cost" class="mono muted"></div>' +
      '<div id="mc-progress"></div>' +
      "</div>" +
      '<div class="pane-section" id="mc-ctx-section">' +
      "<h3>Contexto</h3>" +
      '<div class="mono" id="mc-context">—</div>' +
      '<div class="pane-actions">' +
      '<button type="button" class="btn secondary" id="mc-open-bt" disabled title="Sin backtest_id">Backtest</button>' +
      '<button type="button" class="btn secondary" id="mc-open-scan" disabled title="Sin scan_id">Scan</button>' +
      '<button type="button" class="btn secondary" id="mc-open-ds" disabled title="Sin dataset">Dataset</button>' +
      '<span class="muted mono" id="mc-nav-hint"></span>' +
      "</div>" +
      '<div id="mc-dataset-detail" style="margin-top:0.35rem;display:none"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>¿Qué simulamos?</h3>" +
      '<div id="mc-explain">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Resultados</h3>" +
      '<div id="mc-cards" class="mc-cards"></div>' +
      '<p class="mono" id="mc-ci">—</p>' +
      '<div id="mc-ci-bar"></div>' +
      '<canvas id="mc-hist" width="480" height="140" style="max-width:100%;margin-top:0.5rem;background:rgba(127,127,127,0.08)"></canvas>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Historial sesión</h3>" +
      '<div id="mc-runs"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<details><summary>Datos técnicos (RAW JSON)</summary>" +
      '<div id="mc-out" style="margin-top:0.5rem"></div>' +
      "</details>" +
      "</div>";

    const status = root.querySelector("#mc-status");
    const warnEl = root.querySelector("#mc-warn");
    const ctxEl = root.querySelector("#mc-context");
    const explainEl = root.querySelector("#mc-explain");
    const cardsEl = root.querySelector("#mc-cards");
    const ciEl = root.querySelector("#mc-ci");
    const ciBar = root.querySelector("#mc-ci-bar");
    const hist = root.querySelector("#mc-hist");
    const runsEl = root.querySelector("#mc-runs");
    const out = root.querySelector("#mc-out");
    const navHint = root.querySelector("#mc-nav-hint");
    const costEl = root.querySelector("#mc-cost");
    const progressEl = root.querySelector("#mc-progress");
    const barsDurEl = root.querySelector("#mc-bars-duration");
    const dsDetail = root.querySelector("#mc-dataset-detail");
    const cancelBtn = root.querySelector("#mc-cancel");
    const nInput = root.querySelector("#mc-n");
    const presetsEl = root.querySelector("#mc-presets");

    let lastData = null;
    let lastRunsPayload = null;
    let activeJobId = null;
    let pollTimer = null;
    let runBusy = false;
    /** Contexto heredado del Simulador (moneda + params). */
    let simContext = null;

    function setSimContext(ctx, opts) {
      opts = opts || {};
      if (!ctx || typeof ctx !== "object") {
        simContext = null;
      } else {
        simContext = ctx;
      }
      // Al ligar desde Simulador, no arrastrar backtest_id de Guided Lab
      if (simContext && opts.clearLabIds !== false) {
        var scanEl = root.querySelector("#mc-scan");
        var btEl = root.querySelector("#mc-bt");
        if (scanEl) scanEl.value = "";
        if (btEl) btEl.value = "";
      }
      renderSourceBanner();
    }

    function pullSimHandoff() {
      if (simContext && simContext.pairs && simContext.pairs.length) {
        return simContext;
      }
      try {
        if (global.QLShell && typeof global.QLShell.getSimHandoff === "function") {
          var h = global.QLShell.getSimHandoff();
          if (h && h.pairs && h.pairs.length) {
            setSimContext(h);
            return h;
          }
        }
      } catch (e) {}
      return simContext;
    }

    function formatConfirmIdentity(ctx) {
      if (!ctx) return "";
      var lines = [
        "Vas a estresar ESTA simulación (no un activo al azar):",
        "",
        "Moneda: " + (ctx.coin || (ctx.coins && ctx.coins.join(", ")) || "—"),
        "Mercado(s): " + ((ctx.venues && ctx.venues.join(", ")) || "—"),
        "Estrategia: " + (ctx.strategy_label || ctx.strategy_id || "—"),
        "Tipo: " + (ctx.market_type || "—"),
        "TF / período: " +
          (ctx.interval || "—") +
          " · " +
          (ctx.period_days != null ? ctx.period_days + " días" : "—"),
        "Leverage: x" + (ctx.leverage != null ? ctx.leverage : "—"),
        "Capital: " +
          (ctx.capital_mode || "—") +
          " · inicial=" +
          (ctx.initial_capital != null ? ctx.initial_capital : "—") +
          " · por trade=" +
          (ctx.per_trade_usd != null ? ctx.per_trade_usd : "—"),
        "Pares: " +
          ((ctx.pairs || [])
            .map(function (p) {
              return (p.venue || "?") + "/" + (p.ticker || p.underlying || "?");
            })
            .join(", ") || "—"),
        "",
        "Monte Carlo usará la moneda y la estrategia de arriba (velas reales + ruido).",
        "",
        "¿Confirmás correr con estos parámetros?",
      ];
      return lines.join("\n");
    }

    function confirmRunIdentity() {
      var ctx = pullSimHandoff();
      if (ctx && ctx.pairs && ctx.pairs.length) {
        return window.confirm(formatConfirmIdentity(ctx));
      }
      var goDemo = window.confirm(
        "NO hay simulación ligada.\n\n" +
          "Monte Carlo no sabe qué moneda ni qué estrategia estresar.\n\n" +
          "OK = modo DEMO sintético (WB:SYN / BuyOnce) — NO es tu simulación\n" +
          "Cancelar = volvé al Simulador, elegí moneda+estrategia y abrí Monte Carlo desde allí"
      );
      return goDemo;
    }

    function renderSourceBanner() {
      var sumEl = root.querySelector("#mc-source-summary");
      var detEl = root.querySelector("#mc-source-detail");
      var ban = root.querySelector("#mc-source-banner");
      if (!sumEl || !detEl || !ban) return;
      if (!simContext) {
        ban.classList.remove("mc-source-linked");
        ban.classList.add("mc-source-orphan");
        sumEl.textContent =
          "Sin simulación ligada — modo técnico demo (no está atado a una moneda del Simulador).";
        detEl.textContent =
          "Abrí Monte Carlo desde Simulador (botón Monte Carlo) con mercados y moneda elegidos.";
        return;
      }
      ban.classList.add("mc-source-linked");
      ban.classList.remove("mc-source-orphan");
      sumEl.textContent =
        simContext.summary_line ||
        ((simContext.kind === "rank" ? "Ranking" : "Comparar") +
          " · " +
          (simContext.coin || "—") +
          " · " +
          (simContext.strategy_label || simContext.strategy_id || "—"));
      var bits = [];
      bits.push("Moneda: " + (simContext.coin || "—"));
      bits.push(
        "Mercados: " +
          ((simContext.venues && simContext.venues.join(", ")) || "—")
      );
      bits.push(
        "Estrategia: " +
          (simContext.strategy_label || simContext.strategy_id || "—")
      );
      bits.push(
        "TF " +
          (simContext.interval || "—") +
          " · " +
          (simContext.period_days != null
            ? simContext.period_days + "d"
            : "—") +
          " · x" +
          (simContext.leverage != null ? simContext.leverage : "—")
      );
      bits.push(
        "Capital: " +
          (simContext.capital_mode || "—") +
          " / " +
          (simContext.initial_capital != null
            ? simContext.initial_capital
            : "—")
      );
      if (simContext.pairs && simContext.pairs.length) {
        bits.push(
          "Pares: " +
            simContext.pairs
              .map(function (p) {
                return (p.venue || "?") + "/" + (p.ticker || p.underlying || "?");
              })
              .join(", ")
        );
      }
      detEl.textContent = bits.join(" · ");
    }

    function formatSimContextLines(ctx) {
      if (!ctx) {
        return [
          "— CONTEXTO ORIGEN —",
          "Sin simulación del Simulador ligada (modo técnico demo).",
          "",
        ];
      }
      return [
        "— CONTEXTO ORIGEN (SIMULADOR) —",
        "Resumen: " + (ctx.summary_line || "—"),
        "Tipo corrida: " + (ctx.kind === "rank" ? "Ranking" : "Comparar"),
        "Moneda(s): " + (ctx.coin || (ctx.coins && ctx.coins.join(", ")) || "—"),
        "Mercado(s): " + ((ctx.venues && ctx.venues.join(", ")) || "—"),
        "Estrategia: " + (ctx.strategy_label || ctx.strategy_id || "—"),
        "Tipo mercado: " + (ctx.market_type || "—"),
        "TF / período: " +
          (ctx.interval || "—") +
          " · " +
          (ctx.period_days != null ? ctx.period_days + " días" : "—"),
        "Leverage: x" + (ctx.leverage != null ? ctx.leverage : "—"),
        "Capital: " +
          (ctx.capital_mode || "—") +
          " · inicial=" +
          (ctx.initial_capital != null ? ctx.initial_capital : "—") +
          " · por trade=" +
          (ctx.per_trade_usd != null ? ctx.per_trade_usd : "—"),
        "Pares: " +
          ((ctx.pairs || [])
            .map(function (p) {
              return (p.venue || "?") + "/" + (p.ticker || p.underlying || "?");
            })
            .join(", ") || "—"),
        "",
      ];
    }

    function esc(s) {
      return QLLabUI.escapeHtml(s);
    }

    function firstDefined() {
      for (var i = 0; i < arguments.length; i++) {
        var v = arguments[i];
        if (v != null && v !== "") return v;
      }
      return null;
    }

    function na(v) {
      return v == null || v === "" ? "No disponible" : String(v);
    }

    function money(v) {
      if (v == null || !isFinite(Number(v))) return "No disponible";
      return Number(v).toLocaleString("es-AR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }

    function pctFromInitial(v, initial) {
      if (v == null || initial == null || !initial) return "No disponible";
      const p = ((Number(v) - Number(initial)) / Number(initial)) * 100;
      const sign = p >= 0 ? "+" : "";
      return sign + p.toFixed(2) + " %";
    }

    function pctProb(v) {
      if (v == null || !isFinite(Number(v))) return "No disponible";
      return (
        (Number(v) * 100).toLocaleString("es-AR", {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        }) + " %"
      );
    }

    /** Parsea enteros con formato es-AR ("1.000") o plain ("1000"). */
    function parseIntEs(raw) {
      var s = String(raw == null ? "" : raw).trim();
      if (!s) return NaN;
      s = s.replace(/\s/g, "").replace(/\./g, "").replace(/,/g, "");
      var n = parseInt(s, 10);
      return isFinite(n) ? n : NaN;
    }

    function formatIntEs(n) {
      if (!isFinite(n)) return "";
      return Math.trunc(n).toLocaleString("es-AR");
    }

    function clampScenarios(n) {
      if (!isFinite(n)) return 1000;
      return Math.max(2, Math.min(1000000, Math.trunc(n)));
    }

    function clampBars(n) {
      if (!isFinite(n)) return 60;
      return Math.max(8, Math.min(500, Math.trunc(n)));
    }

    function readScenarios() {
      return clampScenarios(parseIntEs(nInput.value));
    }

    function setScenarios(n) {
      var v = clampScenarios(n);
      nInput.value = String(v);
      return v;
    }

    function confirmLargeCost(n) {
      var msg =
        "N=" +
        formatIntEs(n) +
        " escenarios es una corrida costosa (CPU/tiempo/memoria). " +
        "Puede demorar varios minutos. ¿Continuar?";
      return window.confirm(msg);
    }

    function scenarioWarning(n) {
      if (n < 100) {
        return (
          "Advertencia: N=" +
          n +
          " es exploratorio. No es garantía estadística."
        );
      }
      if (n >= CONFIRM_LARGE_N) {
        return (
          "Corrida grande: N=" +
          formatIntEs(n) +
          ". Batching + memoria acotada; trayectorias ≤ " +
          MAX_TRAJECTORIES +
          "."
        );
      }
      return "";
    }

    function row(label, value) {
      return (
        "<div><span class=\"muted\">" +
        esc(label) +
        "</span> · <span class=\"mono\">" +
        esc(value) +
        "</span></div>"
      );
    }

    function canOpenPane(paneId) {
      return (
        global.QLShell &&
        typeof global.QLShell.open === "function" &&
        global.QLShell.openers &&
        typeof global.QLShell.openers[paneId] === "function"
      );
    }

    function openWorkbenchPane(paneId, opts) {
      if (global.QLNav && typeof global.QLNav.open === "function") {
        return !!global.QLNav.open(paneId, opts || {});
      }
      if (canOpenPane(paneId)) {
        return !!global.QLShell.open(paneId, opts || {});
      }
      return false;
    }

    function jobGet(jobId) {
      if (QLApi.labMontecarloJob) return QLApi.labMontecarloJob(jobId);
      return fetch("/api/lab/montecarlo/jobs/" + encodeURIComponent(jobId), {
        headers: { Accept: "application/json" },
      }).then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw new Error((data && data.error) || res.statusText);
          return data;
        });
      });
    }

    function jobCancel(jobId) {
      if (QLApi.labMontecarloCancel) return QLApi.labMontecarloCancel(jobId);
      return fetch(
        "/api/lab/montecarlo/jobs/" + encodeURIComponent(jobId) + "/cancel",
        {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json" },
          body: "{}",
        }
      ).then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw new Error((data && data.error) || res.statusText);
          return data;
        });
      });
    }

    function stopPoll() {
      if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
      }
    }

    function setCancelVisible(visible) {
      cancelBtn.hidden = !visible;
      cancelBtn.disabled = !visible || !activeJobId;
    }

    function renderProgress(job) {
      if (!job) {
        progressEl.innerHTML = "";
        return;
      }
      var p = job.progress || {};
      var pct = p.pct != null ? Number(p.pct) : null;
      var completed = p.completed != null ? p.completed : "—";
      var total = p.total != null ? p.total : "—";
      var eta = p.eta_seconds != null ? p.eta_seconds + " s" : "—";
      var sps = p.scenarios_per_second != null ? p.scenarios_per_second : "—";
      var barW = pct != null ? Math.max(0, Math.min(100, pct)) : 0;
      progressEl.innerHTML =
        '<div class="muted">Job <span class="mono">' +
        esc(job.job_id || "") +
        "</span> · " +
        esc(job.status || "") +
        " · " +
        esc(String(completed)) +
        "/" +
        esc(String(total)) +
        (pct != null ? " (" + pct + "%)" : "") +
        " · " +
        esc(String(sps)) +
        " esc/s · ETA " +
        esc(String(eta)) +
        "</div>" +
        '<div style="height:8px;background:rgba(127,127,127,0.2);margin-top:0.25rem">' +
        '<div style="height:100%;width:' +
        barW +
        '%;background:var(--accent,#2a6)"></div></div>' +
        (job.error
          ? '<p class="status-bad" style="margin:0.25rem 0 0">' + esc(job.error) + "</p>"
          : "");
    }

    function renderCostEstimate(est, requiresConfirm) {
      if (!est) {
        costEl.textContent = "";
        return;
      }
      var range = est.estimated_seconds_range || [];
      costEl.innerHTML =
        "Estimación coste · N=" +
        esc(formatIntEs(est.n_scenarios)) +
        " · barras=" +
        esc(String(est.n_bars)) +
        " · ops≈" +
        esc(formatIntEs(est.approx_bar_operations)) +
        " · ~" +
        esc(String(est.estimated_seconds)) +
        " s (rango " +
        esc(String(range[0] != null ? range[0] : "?")) +
        "–" +
        esc(String(range[1] != null ? range[1] : "?")) +
        " s) · storage=" +
        esc(String(est.storage_mode || "")) +
        " · trayectorias=" +
        esc(String(est.trajectories_persisted != null ? est.trajectories_persisted : 0)) +
        (requiresConfirm ? " · <strong>requiere confirmación</strong>" : "") +
        (est.note ? '<div class="muted">' + esc(est.note) + "</div>" : "");
    }

    function updateBarsDurationHint(data) {
      var meta = data && data.bars_meta;
      if (meta && meta.duration_label) {
        barsDurEl.textContent =
          "Duración equiv.: " +
          meta.duration_label +
          (meta.timeframe ? " (" + meta.n_bars + " × " + meta.timeframe + ")" : "");
        return;
      }
      var bars = clampBars(parseInt(root.querySelector("#mc-bars").value, 10));
      barsDurEl.textContent = "≈ " + bars + " min (1m sintético)";
    }

    function fillFormFromRun(data) {
      if (!data) return;
      const cfg = data.config || {};
      const ctx = data.context || {};
      if (data.n_scenarios != null) setScenarios(data.n_scenarios);
      else if (cfg.n_scenarios != null) setScenarios(cfg.n_scenarios);
      if (data.n_bars != null) root.querySelector("#mc-bars").value = data.n_bars;
      else if (cfg.n_bars != null) root.querySelector("#mc-bars").value = cfg.n_bars;
      if (data.noise_bps != null) root.querySelector("#mc-noise").value = data.noise_bps;
      else if (cfg.noise_bps != null) root.querySelector("#mc-noise").value = cfg.noise_bps;
      if (data.seed != null) root.querySelector("#mc-seed").value = data.seed;
      else if (cfg.seed != null) root.querySelector("#mc-seed").value = cfg.seed;
      root.querySelector("#mc-scan").value =
        ctx.scan_id || (data.relations && data.relations.scan_id) || "";
      root.querySelector("#mc-bt").value =
        ctx.backtest_id || (data.relations && data.relations.backtest_id) || "";
      root.querySelector("#mc-paths").checked = !!(
        data.equity_paths && data.equity_paths.length
      );
      updateBarsDurationHint(data);
    }

    function copyText(text, okMsg) {
      if (!text) {
        QLLabUI.setStatus(status, false, "sin texto");
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () {
            QLLabUI.setStatus(status, true, okMsg || "copiado");
          },
          function () {
            QLLabUI.setStatus(status, false, "no se pudo copiar");
          }
        );
      } else {
        QLLabUI.setStatus(status, false, "clipboard no disponible");
      }
    }

    function renderDatasetDetail(ds) {
      if (!ds) {
        dsDetail.style.display = "none";
        dsDetail.innerHTML = "";
        return;
      }
      dsDetail.style.display = "block";
      dsDetail.innerHTML =
        "<details open><summary>Dataset · " +
        esc(firstDefined(ds.label_es, ds.dataset_id, "detalle")) +
        "</summary>" +
        '<div class="mono" style="margin-top:0.35rem">' +
        row("dataset_id", na(ds.dataset_id)) +
        row("Fuente", na(ds.source)) +
        row("Símbolo", na(ds.symbol || ds.normalized_instrument)) +
        row("Venue", na(ds.venue)) +
        row("Network", na(ds.network)) +
        row("Mercado", na(ds.market_type)) +
        row("Timeframe", na(ds.timeframe)) +
        row("Barras", na(ds.bars)) +
        row("Duración", na(ds.duration_label)) +
        row("Inicio", na(ds.start_time)) +
        row("Fin", na(ds.end_time)) +
        row("Hash", na(ds.hash)) +
        row("Sintético", ds.synthetic === true ? "sí" : ds.synthetic === false ? "no" : "—") +
        row("Seed gen.", na(ds.seed)) +
        "</div></details>";
    }

    function updateNavButtons(data) {
      const ctx = (data && data.context) || {};
      const rel = (data && data.relations) || {};
      const ds = (data && data.dataset) || null;
      const btId = firstDefined(ctx.backtest_id, rel.backtest_id);
      const scanId = firstDefined(ctx.scan_id, rel.scan_id);
      const dsId = firstDefined(
        ds && ds.dataset_id,
        ctx.dataset_id,
        rel.dataset_id
      );
      const btnBt = root.querySelector("#mc-open-bt");
      const btnScan = root.querySelector("#mc-open-scan");
      const btnDs = root.querySelector("#mc-open-ds");

      btnBt.disabled = !btId;
      btnBt.title = btId
        ? "Abrir panel Reports/Backtest · " + btId
        : "Sin backtest_id en contexto";
      btnScan.disabled = !scanId;
      btnScan.title = scanId
        ? "Abrir panel Scanner/Guided Lab · " + scanId
        : "Sin scan_id en contexto";
      btnDs.disabled = !ds && !dsId;
      btnDs.title =
        ds || dsId
          ? "Ver metadata del dataset" + (dsId ? " · " + dsId : "")
          : "Sin dataset en la respuesta";

      const hints = [];
      if (btId) {
        hints.push(
          canOpenPane("reports") || canOpenPane("backtest")
            ? "Backtest: abre panel Reports/Backtest"
            : "backtest_id=" + btId + " — abrí Reports/Backtest manualmente"
        );
      }
      if (scanId) {
        hints.push(
          canOpenPane("scanner") || canOpenPane("guided_lab")
            ? "Scan: abre panel Scanner/Guided Lab"
            : "scan_id=" + scanId + " — abrí Scanner/Guided Lab manualmente"
        );
      }
      if (dsId) hints.push("dataset=" + dsId);
      navHint.textContent = hints.join(" · ");
    }

    function renderContext(data) {
      const ctx = (data && data.context) || {};
      const cfg = (data && data.config) || {};
      const cap = (data && data.capital_summary) || {};
      const ds = (data && data.dataset) || {};
      const rel = (data && data.relations) || {};

      const strategy = firstDefined(
        ctx.strategy_name,
        ctx.strategy_id,
        cfg.strategy_id
      );
      const symbols = firstDefined(
        (ctx.symbols && ctx.symbols.length && ctx.symbols.join(", ")) || null,
        ds.symbol,
        ds.normalized_instrument
      );
      const venue = firstDefined(ctx.venue, ds.venue);
      const timeframe = firstDefined(ctx.timeframe, cfg.timeframe_hint, ds.timeframe);
      const datasetId = firstDefined(ctx.dataset_id, ds.dataset_id, rel.dataset_id);
      const initial = firstDefined(
        cap.initial_equity,
        data && data.initial_equity,
        ctx.initial_equity
      );
      const currency = firstDefined(
        cap.currency,
        data && data.equity_currency,
        ctx.equity_currency,
        "LAB"
      );
      const btId = firstDefined(ctx.backtest_id, rel.backtest_id);
      const scanId = firstDefined(ctx.scan_id, rel.scan_id);

      ctxEl.innerHTML =
        (simContext
          ? row(
              "Origen Simulador",
              na(simContext.summary_line || simContext.coin)
            ) +
            row("Moneda origen", na(simContext.coin)) +
            row(
              "Estrategia origen",
              na(simContext.strategy_label || simContext.strategy_id)
            )
          : row("Origen Simulador", "— (modo técnico demo)")
        ) +
        row("Estrategia", na(strategy)) +
        row("Símbolos", na(symbols)) +
        row("Venue", na(venue)) +
        row("Network", na(firstDefined(ctx.network, ds.network))) +
        row("Mercado", na(firstDefined(ctx.market_type, ds.market_type))) +
        row("Timeframe", na(timeframe)) +
        row("Dataset", na(datasetId)) +
        row(
          "Fuente dataset",
          na(firstDefined(ctx.dataset_source, ds.source, ds.label_es))
        ) +
        row(
          "Capital inicial",
          (initial != null ? money(initial) : "No disponible") + " (" + na(currency) + ")"
        ) +
        row("Backtest origen", na(btId)) +
        row("Scan origen", na(scanId)) +
        row("run_id", na(data && data.run_id)) +
        row("schema", na(data && data.schema_version)) +
        (ctx.orphan_technical_mode && !ctx.sim_linked && !simContext
          ? '<p class="status-bad" style="margin-top:0.4rem">' +
            esc(ctx.orphan_warning || "Modo técnico huérfano") +
            "</p>"
          : ctx.sim_linked || simContext
            ? '<p class="status-ok" style="margin-top:0.4rem">Ligado al Simulador · no es modo huérfano</p>'
            : "");
      updateNavButtons(data);
    }

    function renderExplain(data) {
      const cfg = (data && data.config) || {};
      const n = data && data.n_scenarios != null ? data.n_scenarios : cfg.n_scenarios;
      const bars = data && data.n_bars != null ? data.n_bars : cfg.n_bars;
      const noise = data && data.noise_bps != null ? data.noise_bps : cfg.noise_bps;
      const horizon =
        (data && data.bar_horizon_label) ||
        (data && data.bars_meta && data.bars_meta.duration_label) ||
        (cfg.bar_horizon_label ? cfg.bar_horizon_label : bars + " × 1m");
      explainEl.innerHTML =
        (simContext
          ? "<p><strong>Identidad:</strong> estrés ligado a " +
            esc(simContext.coin || "moneda") +
            " · " +
            esc(simContext.strategy_label || simContext.strategy_id || "estrategia") +
            " · " +
            esc((simContext.venues && simContext.venues.join(", ")) || "mercados") +
            " (desde Simulador).</p>"
          : "<p class=\"status-bad\"><strong>Sin origen:</strong> no hay moneda/estrategia del Simulador. " +
            "Abrí MC desde el botón Monte Carlo del Simulador.</p>") +
        "<p><strong>Método:</strong> " +
        esc(na(data && data.method)) +
        " — perturbación OHLC gaussiana + re-ejecución del backtester.</p>" +
        "<p>Se generan <strong>" +
        esc(na(n)) +
        "</strong> escenarios; cada uno re-ejecuta la estrategia sobre <strong>" +
        esc(na(bars)) +
        "</strong> velas (" +
        esc(na(horizon)) +
        "). Ruido σ = " +
        esc(na(noise)) +
        " bps (" +
        esc(noise != null ? (Number(noise) / 100).toFixed(2) + " %" : "—") +
        "). Seed=" +
        esc(na(data && data.seed)) +
        ". CI = IC de la <em>media</em> (Wald), no banda de un escenario individual.</p>" +
        (data && data.fee_summary
          ? "<p><strong>Fees:</strong> " +
            esc(data.fee_summary.fee_per_side_note || "") +
            " · as_of " +
            esc(na(data.fee_summary.as_of)) +
            " · media fees/escenario=" +
            esc(money(data.fee_summary.mean_total_fees)) +
            "</p>"
          : "") +
        '<p class="muted">' +
        esc((data && data.disclaimer) || "") +
        "</p>";
    }

    function card(title, main, sub) {
      return (
        '<div style="min-width:9rem;padding:0.5rem 0.65rem;border:1px solid rgba(127,127,127,0.25)">' +
        '<div class="muted" style="font-size:0.8em">' +
        esc(title) +
        "</div>" +
        '<div class="mono" style="font-size:1.05em">' +
        esc(main) +
        "</div>" +
        (sub
          ? '<div class="muted" style="font-size:0.8em">' + esc(sub) + "</div>"
          : "") +
        "</div>"
      );
    }

    function renderCards(data) {
      const m = (data && data.metrics) || {};
      const ctx = (data && data.context) || {};
      const cap = (data && data.capital_summary) || {};
      const fee = (data && data.fee_summary) || {};
      const initial = firstDefined(
        cap.initial_equity,
        data.initial_equity,
        ctx.initial_equity
      );
      const currency = firstDefined(
        cap.currency,
        data.equity_currency,
        ctx.equity_currency,
        "LAB"
      );
      const finals = (data && data.final_equities) || [];
      const minE = firstDefined(
        cap.min_final_equity,
        finals.length ? Math.min.apply(null, finals.map(Number)) : null
      );
      const maxE = firstDefined(
        cap.max_final_equity,
        finals.length ? Math.max.apply(null, finals.map(Number)) : null
      );
      const mean = firstDefined(
        cap.mean_final_equity,
        m.mean_equity,
        data.mean_equity
      );
      const med = firstDefined(cap.median_final_equity, m.median_equity);
      const feeSide =
        fee.fee_per_side_note ||
        (fee.taker_bps != null
          ? "taker " +
            fee.taker_bps +
            " bps (" +
            fee.taker_pct +
            "%) / maker " +
            fee.maker_bps +
            " bps"
          : "VIP0 Spot 10 bps/lado");
      cardsEl.style.display = "flex";
      cardsEl.style.flexWrap = "wrap";
      cardsEl.style.gap = "0.5rem";
      cardsEl.innerHTML =
        card("Capital inicial", money(initial), currency + " lab") +
        card(
          "Capital final (media escenarios)",
          money(mean),
          pctFromInitial(mean, initial)
        ) +
        card("Mediana final", money(med), pctFromInitial(med, initial)) +
        card("Mejor escenario", money(maxE), pctFromInitial(maxE, initial)) +
        card("Peor escenario", money(minE), pctFromInitial(minE, initial)) +
        card(
          "Fee por operación (lado)",
          fee.taker_bps != null ? fee.taker_bps + " bps" : "10 bps",
          feeSide
        ) +
        card(
          "Fees totales (media escenarios)",
          money(fee.mean_total_fees),
          fee.mean_fee_per_fill != null
            ? "media/fill " + money(fee.mean_fee_per_fill)
            : "as_of " + na(fee.as_of)
        ) +
        card("Prob. ganancia", pctProb(m.prob_profit), "final > inicial") +
        card("Prob. pérdida", pctProb(m.prob_loss), "final < inicial") +
        card(
          "Prob. ≥ equity inicial",
          pctProb(m.prob_above_initial),
          "final ≥ inicial"
        ) +
        card(
          "IC media (CI95)",
          money(data.ci_low) + " → " + money(data.ci_high),
          "Wald sobre la media"
        ) +
        card("Desvío", money(data.std_equity), "pstdev equities finales");
    }

    function renderHistogram(finals) {
      const ctx2d = hist.getContext("2d");
      if (!ctx2d) return;
      const w = hist.width;
      const h = hist.height;
      ctx2d.clearRect(0, 0, w, h);
      if (!finals || finals.length < 2) {
        ctx2d.fillStyle = "#888";
        ctx2d.fillText("Histograma requiere ≥2 equities finales", 8, 20);
        return;
      }
      const vals = finals.map(Number);
      const lo = Math.min.apply(null, vals);
      const hi = Math.max.apply(null, vals);
      const bins = Math.min(12, vals.length);
      const counts = new Array(bins).fill(0);
      const span = hi - lo || 1;
      vals.forEach(function (v) {
        let i = Math.floor(((v - lo) / span) * bins);
        if (i >= bins) i = bins - 1;
        counts[i] += 1;
      });
      const maxC = Math.max.apply(null, counts) || 1;
      const bw = w / bins;
      ctx2d.fillStyle = "rgba(42,160,96,0.7)";
      counts.forEach(function (c, i) {
        const bh = (c / maxC) * (h - 16);
        ctx2d.fillRect(i * bw + 1, h - bh - 4, bw - 2, bh);
      });
      ctx2d.fillStyle = "#888";
      ctx2d.font = "11px monospace";
      ctx2d.fillText("Histograma capital final", 6, 12);
    }

    function renderCiBar(data) {
      const low = data && data.ci_low != null ? Number(data.ci_low) : null;
      const high = data && data.ci_high != null ? Number(data.ci_high) : null;
      const mean = data && data.mean_equity != null ? Number(data.mean_equity) : null;
      if (low == null || high == null || mean == null || !(high > low)) {
        ciBar.innerHTML = "";
        return;
      }
      const pad = high - low || 1;
      const pct = Math.max(0, Math.min(100, ((mean - low) / pad) * 100));
      ciBar.innerHTML =
        '<div class="mc-ci-track" style="position:relative;height:10px;background:rgba(127,127,127,0.2);margin-top:0.35rem">' +
        '<div style="position:absolute;left:0;top:0;bottom:0;width:100%;opacity:0.35;background:var(--accent,#2a6)"></div>' +
        '<div style="position:absolute;left:' +
        pct.toFixed(1) +
        '%;top:-2px;width:2px;height:14px;background:currentColor" title="mean"></div>' +
        "</div>";
    }

    function buildMcMemo(data, formParams) {
      formParams = formParams || {};
      var ctx =
        formParams.sim_context ||
        simContext ||
        (data && data.context && data.context.sim_context) ||
        null;
      if (
        !ctx &&
        data &&
        data.context &&
        data.context.sim_linked &&
        data.context.coin
      ) {
        ctx = {
          coin: data.context.coin,
          strategy_id: data.context.strategy_id || data.context.strategy_name,
          strategy_label: data.context.strategy_name,
          venues: data.context.venue ? [data.context.venue] : [],
          market_type: data.context.market_type,
          interval: data.context.timeframe,
          summary_line: data.context.sim_summary || "",
          kind: "compare",
        };
      }
      var lines = [];
      var n = data && data.n_scenarios != null ? data.n_scenarios : formParams.n_scenarios;
      lines.push("QUANTLAB — MEMORANDO MONTE CARLO");
      lines.push("Generado: " + new Date().toLocaleString("es-AR"));
      lines.push("LIVE_BLOCKED=true · research / no predice precios");
      lines.push("");
      lines = lines.concat(formatSimContextLines(ctx));
      lines.push("— PARA QUÉ SIRVE —");
      lines.push(
        "Estrés de robustez: N escenarios con ruido en precios; " +
          "mirá media / desvío / IC95 de la media de equity final. " +
          "No es predicción del mercado ni garantía de PnL."
      );
      if (ctx && (ctx.coin || ctx.strategy_id)) {
        lines.push(
          "Esta corrida está identificada sobre: " +
            (ctx.coin || "—") +
            " / " +
            (ctx.strategy_label || ctx.strategy_id || "estrategia") +
            " (contexto Simulador)."
        );
      }
      lines.push("");
      lines.push("— PARÁMETROS MONTE CARLO —");
      lines.push("Escenarios (N): " + (n != null ? n : "—"));
      lines.push(
        "Velas por escenario: " +
          (formParams.n_bars != null
            ? formParams.n_bars
            : data && data.n_bars != null
              ? data.n_bars
              : "—")
      );
      lines.push(
        "Ruido bps: " +
          (formParams.noise_bps != null
            ? formParams.noise_bps
            : data && data.noise_bps != null
              ? data.noise_bps
              : "—")
      );
      lines.push(
        "Seed: " +
          (formParams.seed != null
            ? formParams.seed
            : data && data.seed != null
              ? data.seed
              : "—")
      );
      lines.push(
        "strategy_id: " +
          ((ctx && (ctx.strategy_id || ctx.strategy_label)) ||
            (data && data.context && (data.context.strategy_id || data.context.strategy_name)) ||
            "—")
      );
      lines.push(
        "símbolo/dataset: " +
          ((data && data.dataset && (data.dataset.symbol || data.dataset.dataset_id)) ||
            "—")
      );
      lines.push("scan_id: " + (formParams.scan_id || "—"));
      lines.push("backtest_id: " + (formParams.backtest_id || "—"));
      lines.push(
        "Trayectorias guardadas: " + (formParams.store_paths ? "sí" : "no")
      );
      lines.push(
        "Modo: " +
          ((data && data.mode) ||
            (data && data.context && data.context.lab_mode) ||
            (ctx ? "sim_linked" : formParams.backtest_id ? "normal" : "technical_lab"))
      );
      lines.push("run_id: " + ((data && data.run_id) || "—"));
      lines.push("");
      lines.push("— RESULTADOS —");
      lines.push(
        "Media equity final: " +
          (data && data.mean_equity != null
            ? Number(data.mean_equity).toLocaleString("es-AR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })
            : "—")
      );
      lines.push(
        "Std equity: " +
          (data && data.std_equity != null
            ? Number(data.std_equity).toLocaleString("es-AR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })
            : "—")
      );
      if (data && data.ci_low != null && data.ci_high != null) {
        lines.push(
          "CI95 media: [" +
            Number(data.ci_low).toLocaleString("es-AR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) +
            ", " +
            Number(data.ci_high).toLocaleString("es-AR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) +
            "]"
        );
      }
      lines.push("");
      lines.push("— FIN MEMORANDO —");
      var csvLines = [
        [
          "coin",
          "strategy_id",
          "venues",
          "n_scenarios",
          "n_bars",
          "noise_bps",
          "seed",
          "scan_id",
          "backtest_id",
          "mean_equity",
          "std_equity",
          "ci_low",
          "ci_high",
          "run_id",
        ].join(","),
        [
          (ctx && (ctx.coin || "")) || "",
          (ctx && (ctx.strategy_id || "")) || "",
          (ctx && ctx.venues && ctx.venues.join("|")) || "",
          n != null ? n : "",
          formParams.n_bars != null ? formParams.n_bars : "",
          formParams.noise_bps != null ? formParams.noise_bps : "",
          formParams.seed != null ? formParams.seed : "",
          formParams.scan_id || "",
          formParams.backtest_id || "",
          data && data.mean_equity != null ? data.mean_equity : "",
          data && data.std_equity != null ? data.std_equity : "",
          data && data.ci_low != null ? data.ci_low : "",
          data && data.ci_high != null ? data.ci_high : "",
          (data && data.run_id) || "",
        ].join(","),
      ];
      var coinTag = (ctx && ctx.coin) || "run";
      return {
        kind: "montecarlo",
        title:
          "Memorando · MC " +
          coinTag +
          " · N=" +
          (n != null ? n : "?"),
        text: lines.join("\n"),
        csv: csvLines.join("\n"),
        filenameBase:
          "quantlab-mc-" +
          String(coinTag).replace(/[^a-zA-Z0-9_-]+/g, "_") +
          "-" +
          (n != null ? n : "run") +
          "-" +
          Date.now(),
        nRows: 1,
      };
    }

    function readMcFormParams() {
      return {
        n_scenarios: readScenarios(),
        n_bars: clampBars(parseInt(root.querySelector("#mc-bars").value, 10)),
        noise_bps: parseFloat(root.querySelector("#mc-noise").value),
        seed: parseInt(root.querySelector("#mc-seed").value, 10),
        scan_id: (root.querySelector("#mc-scan").value || "").trim(),
        backtest_id: (root.querySelector("#mc-bt").value || "").trim(),
        store_paths: root.querySelector("#mc-paths").checked,
        sim_context: simContext || null,
      };
    }

    function presentMcMemo(data, formParams, doRegister) {
      if (!data) return;
      var params = formParams || readMcFormParams();
      if (!params.sim_context && simContext) params.sim_context = simContext;
      var memo = buildMcMemo(data, params);
      if (doRegister && global.QLSimRegistry && typeof global.QLSimRegistry.add === "function") {
        try {
          var coin = (params.sim_context && params.sim_context.coin) || "";
          global.QLSimRegistry.add({
            kind: "montecarlo",
            title: memo.title,
            summary:
              (coin ? coin + " · " : "") +
              "N=" +
              (params.n_scenarios != null ? params.n_scenarios : "?") +
              " · media=" +
              money(data.mean_equity),
            params: params,
            memo: memo,
          });
        } catch (e) {}
      }
      if (global.QLSimRegistry && typeof global.QLSimRegistry.openMemo === "function") {
        global.QLSimRegistry.openMemo(memo, params);
      }
    }

    function renderResult(data) {
      lastData = data;
      if (!data) {
        ctxEl.textContent = "—";
        explainEl.textContent = "—";
        cardsEl.innerHTML = "";
        ciEl.textContent = "sin corridas — corré simular";
        ciBar.innerHTML = "";
        out.innerHTML = "";
        warnEl.textContent = "";
        navHint.textContent = "";
        renderDatasetDetail(null);
        updateNavButtons(null);
        updateBarsDurationHint(null);
        return;
      }
      const ok = data.ok !== false;
      const n = data.n_scenarios != null ? data.n_scenarios : "?";
      QLLabUI.setStatus(status, ok, ok ? "OK · N=" + n : "FAIL");
      warnEl.textContent = scenarioWarning(Number(n) || 0);
      if (data.warnings && data.warnings.length) {
        warnEl.textContent =
          (warnEl.textContent ? warnEl.textContent + " · " : "") +
          data.warnings.join(" · ");
      }
      if (data.context && data.context.sim_context) {
        setSimContext(data.context.sim_context, { clearLabIds: true });
      }
      renderContext(data);
      renderExplain(data);
      renderCards(data);
      updateBarsDurationHint(data);
      ciEl.textContent =
        "Media escenarios=" +
        money(data.mean_equity) +
        " · std=" +
        money(data.std_equity) +
        " · CI95 media=[" +
        money(data.ci_low) +
        ", " +
        money(data.ci_high) +
        "]";
      renderCiBar(data);
      renderHistogram(data.final_equities || data.sample_final_equities || []);
      out.innerHTML = QLLabUI.preJson(data);
    }

    function bindRunActions() {
      runsEl.querySelectorAll(".mc-open-run").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          QLApi.labMonteCarloRun(id)
            .then(function (data) {
              renderResult(data);
              fillFormFromRun(data);
            })
            .catch(function (err) {
              QLLabUI.setStatus(status, false, err.message);
            });
        });
      });
      runsEl.querySelectorAll(".mc-repeat-run").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          QLApi.labMonteCarloRun(id)
            .then(function (data) {
              fillFormFromRun(data);
              root.querySelector("#mc-run").click();
            })
            .catch(function (err) {
              QLLabUI.setStatus(status, false, err.message);
            });
        });
      });
      runsEl.querySelectorAll(".mc-copy-run").forEach(function (btn) {
        btn.addEventListener("click", function () {
          copyText(btn.getAttribute("data-id"), "run_id copiado");
        });
      });
      runsEl.querySelectorAll(".mc-delete-run").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          if (!id) return;
          if (!window.confirm("¿Eliminar corrida Monte Carlo " + id + "?")) return;
          QLApi.labMonteCarloDelete(id)
            .then(function () {
              if (lastData && lastData.run_id === id) {
                renderResult(null);
              }
              return refresh();
            })
            .then(function () {
              QLLabUI.setStatus(status, true, "eliminado " + id);
            })
            .catch(function (err) {
              QLLabUI.setStatus(status, false, err.message);
            });
        });
      });
    }

    function renderRuns(listPayload) {
      lastRunsPayload = listPayload;
      const runs = (listPayload && listPayload.runs) || [];
      if (!runs.length) {
        runsEl.innerHTML = '<p class="muted mono">sin corridas — corré simular</p>';
        return;
      }
      runsEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>fecha</th><th>run</th><th>estrategia</th><th>símbolo</th>" +
        "<th>N</th><th>barras</th><th>media</th><th>CI</th><th></th>" +
        "</tr></thead><tbody>" +
        runs
          .map(function (r) {
            const sym = (r.symbols && r.symbols[0]) || "—";
            return (
              "<tr>" +
              '<td class="mono">' +
              esc(na(r.created_at)) +
              "</td>" +
              '<td class="mono">' +
              esc(r.run_id) +
              "</td>" +
              "<td>" +
              esc(na(r.strategy_id)) +
              "</td>" +
              "<td>" +
              esc(sym) +
              "</td>" +
              '<td class="num">' +
              esc(na(r.n_scenarios)) +
              "</td>" +
              '<td class="num">' +
              esc(na(r.n_bars)) +
              "</td>" +
              '<td class="num">' +
              esc(money(r.mean_equity)) +
              "</td>" +
              '<td class="num">' +
              esc(money(r.ci_low) + "–" + money(r.ci_high)) +
              "</td>" +
              '<td style="white-space:nowrap">' +
              '<button type="button" class="btn secondary mc-open-run" data-id="' +
              esc(r.run_id) +
              '">abrir</button> ' +
              '<button type="button" class="btn secondary mc-repeat-run" data-id="' +
              esc(r.run_id) +
              '" title="Misma seed/config">repetir</button> ' +
              '<button type="button" class="btn secondary mc-copy-run" data-id="' +
              esc(r.run_id) +
              '">copiar id</button> ' +
              '<button type="button" class="btn secondary mc-delete-run" data-id="' +
              esc(r.run_id) +
              '">eliminar</button>' +
              "</td>" +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
      bindRunActions();
    }

    async function refresh() {
      const data = await QLApi.labMonteCarloHistory();
      renderResult(data.latest || null);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    function pollJob(jobId) {
      stopPoll();
      activeJobId = jobId;
      setCancelVisible(true);
      function tick() {
        jobGet(jobId)
          .then(function (job) {
            renderProgress(job);
            out.innerHTML = QLLabUI.preJson(job);
            var st = job.status || "";
            if (st === "completed" || st === "cancelled" || st === "failed") {
              stopPoll();
              activeJobId = null;
              setCancelVisible(false);
              runBusy = false;
              if (st === "failed") {
                QLLabUI.setStatus(status, false, job.error || "job failed");
                return;
              }
              var result = job.result;
              if (result) {
                renderResult(result);
                presentMcMemo(result, readMcFormParams(), true);
                refresh().catch(function () {});
              } else {
                QLLabUI.setStatus(
                  status,
                  st === "cancelled",
                  st === "cancelled" ? "cancelado" : "job sin result"
                );
              }
              return;
            }
            QLLabUI.setStatus(status, true, "job " + st);
            pollTimer = setTimeout(tick, POLL_MS);
          })
          .catch(function (err) {
            stopPoll();
            activeJobId = null;
            setCancelVisible(false);
            runBusy = false;
            QLLabUI.setStatus(status, false, err.message || String(err));
          });
      }
      tick();
    }

    function buildBody(n, bars, noise, seed, scan, bt, storePaths, confirmLarge, asyncFlag) {
      var ctx = simContext || null;
      var sid =
        (ctx && ctx.strategy_id) ||
        null;
      var body = {
        n_scenarios: n,
        n_bars: bars,
        noise_bps: isFinite(noise) ? noise : 10,
        seed: isFinite(seed) ? seed : 42,
        scan_id: ctx ? null : scan || null,
        backtest_id: ctx ? null : bt || null,
        store_paths: storePaths,
        confirm_large: !!confirmLarge,
        mode: ctx ? "technical_lab" : bt ? "normal" : "technical_lab",
        max_persisted_trajectories: MAX_TRAJECTORIES,
      };
      if (sid) body.strategy_id = sid;
      if (ctx) {
        body.sim_context = ctx;
        // El backend fuerza mode=sim_linked al ver sim_context.
        // No mandar "sim_linked" en el wire: evita 400 si el proceso
        // Workbench no se reinició aún (validación vieja solo lab/normal).
      }
      if (asyncFlag) body.async = true;
      return body;
    }

    async function runSimulation() {
      if (runBusy) return;
      if (!confirmRunIdentity()) {
        QLLabUI.setStatus(status, false, "cancelado — confirmá moneda/estrategia");
        return;
      }
      var n = readScenarios();
      setScenarios(n);
      var bars = clampBars(parseInt(root.querySelector("#mc-bars").value, 10));
      root.querySelector("#mc-bars").value = String(bars);
      var noise = parseFloat(root.querySelector("#mc-noise").value);
      var seed = parseInt(root.querySelector("#mc-seed").value, 10);
      var scan = (root.querySelector("#mc-scan").value || "").trim();
      var bt = (root.querySelector("#mc-bt").value || "").trim();
      var storePaths = root.querySelector("#mc-paths").checked;
      // Con sim ligada, no mandar BT residual de Guided Lab
      if (simContext) {
        scan = "";
        bt = "";
        root.querySelector("#mc-scan").value = "";
        root.querySelector("#mc-bt").value = "";
      }

      var confirmLarge = false;
      if (n >= CONFIRM_LARGE_N) {
        if (!confirmLargeCost(n)) {
          QLLabUI.setStatus(status, false, "cancelado por usuario");
          return;
        }
        confirmLarge = true;
      }

      runBusy = true;
      QLLabUI.setStatus(
        status,
        true,
        simContext
          ? "ejecutando · " +
              (simContext.coin || "sim") +
              " · " +
              (simContext.strategy_id || "?")
          : "ejecutando (demo)…"
      );
      status.className = "mono muted";
      warnEl.textContent = scenarioWarning(n);
      progressEl.innerHTML = "";

      try {
        if (n >= ESTIMATE_N) {
          var estResp = await QLApi.labMonteCarlo(
            Object.assign(
              buildBody(n, bars, noise, seed, scan, bt, storePaths, confirmLarge, false),
              { estimate_only: true }
            )
          );
          renderCostEstimate(
            estResp && estResp.estimate,
            !!(estResp && estResp.requires_confirm)
          );
        } else {
          costEl.textContent = "";
        }

        var useAsync = n >= ASYNC_N;
        var data = await QLApi.labMonteCarlo(
          buildBody(n, bars, noise, seed, scan, bt, storePaths, confirmLarge, useAsync)
        );

        if (data && data.kind === "montecarlo_job") {
          activeJobId = data.job_id;
          renderProgress(data);
          out.innerHTML = QLLabUI.preJson(data);
          QLLabUI.setStatus(status, true, "job " + (data.status || "queued"));
          pollJob(data.job_id);
          return;
        }

        runBusy = false;
        setCancelVisible(false);
        renderResult(data);
        presentMcMemo(data, readMcFormParams(), true);
        refresh().catch(function () {});
      } catch (err) {
        runBusy = false;
        setCancelVisible(false);
        stopPoll();
        QLLabUI.setStatus(status, false, err.message || String(err));
        out.innerHTML = "";
      }
    }

    // --- presets ---
    SCENARIO_PRESETS.forEach(function (p) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn secondary";
      btn.textContent = p.label + " " + formatIntEs(p.n);
      btn.title = "Preset " + p.label + ": " + formatIntEs(p.n) + " escenarios";
      btn.addEventListener("click", function () {
        if (p.id === "extremo" || p.n >= CONFIRM_LARGE_N) {
          if (!confirmLargeCost(p.n)) return;
        }
        setScenarios(p.n);
        warnEl.textContent = scenarioWarning(p.n);
      });
      presetsEl.appendChild(btn);
    });

    nInput.addEventListener("change", function () {
      var n = readScenarios();
      setScenarios(n);
      warnEl.textContent = scenarioWarning(n);
    });
    nInput.addEventListener("blur", function () {
      var n = readScenarios();
      setScenarios(n);
      warnEl.textContent = scenarioWarning(n);
    });

    root.querySelector("#mc-bars").addEventListener("change", function () {
      updateBarsDurationHint(lastData);
    });

    root.querySelector("#mc-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    root.querySelector("#mc-copy-id").addEventListener("click", function () {
      copyText(lastData && lastData.run_id, "run_id copiado");
    });

    cancelBtn.addEventListener("click", function () {
      if (!activeJobId) return;
      cancelBtn.disabled = true;
      jobCancel(activeJobId)
        .then(function (job) {
          renderProgress(job);
          QLLabUI.setStatus(status, true, "cancelando…");
        })
        .catch(function (err) {
          cancelBtn.disabled = false;
          QLLabUI.setStatus(status, false, err.message);
        });
    });

    root.querySelector("#mc-open-bt").addEventListener("click", function () {
      const id =
        lastData &&
        firstDefined(
          lastData.context && lastData.context.backtest_id,
          lastData.relations && lastData.relations.backtest_id
        );
      if (!id) return;
      const opened = openWorkbenchPane("reports", {
        focusId: id,
        message: "Deep-link desde Monte Carlo → report " + id,
      });
      if (opened) {
        QLLabUI.setStatus(status, true, "abriendo report " + id);
      } else {
        QLLabUI.setStatus(
          status,
          false,
          "no se pudo abrir Reports · backtest_id=" + id
        );
      }
    });

    root.querySelector("#mc-open-scan").addEventListener("click", function () {
      const id =
        lastData &&
        firstDefined(
          lastData.context && lastData.context.scan_id,
          lastData.relations && lastData.relations.scan_id
        );
      if (!id) return;
      const opened = openWorkbenchPane("guided_lab", {
        focusId: id,
        message: "Deep-link desde Monte Carlo → scan " + id,
      });
      if (opened) {
        QLLabUI.setStatus(status, true, "abriendo Guided Lab · scan " + id);
      } else {
        QLLabUI.setStatus(
          status,
          false,
          "no se pudo abrir Guided Lab · scan_id=" + id
        );
      }
    });

    root.querySelector("#mc-open-ds").addEventListener("click", function () {
      const ds = lastData && lastData.dataset;
      if (ds) {
        renderDatasetDetail(ds);
        dsDetail.scrollIntoView({ block: "nearest", behavior: "smooth" });
        QLLabUI.setStatus(
          status,
          true,
          "dataset " + (ds.dataset_id || "") + " · detalle inline"
        );
        return;
      }
      const dsId =
        lastData &&
        firstDefined(
          lastData.context && lastData.context.dataset_id,
          lastData.relations && lastData.relations.dataset_id
        );
      if (!dsId) return;
      dsDetail.style.display = "block";
      dsDetail.innerHTML =
        "<details open><summary>Dataset · " +
        esc(dsId) +
        "</summary>" +
        '<p class="muted">Solo id en contexto; metadata completa no incluida en la respuesta.</p>' +
        row("dataset_id", dsId) +
        "</details>";
      QLLabUI.setStatus(status, true, "dataset_id=" + dsId);
    });

    root.querySelector("#mc-run").addEventListener("click", function () {
      runSimulation();
    });
    var memoBtn = root.querySelector("#mc-memo");
    if (memoBtn) {
      memoBtn.addEventListener("click", function () {
        if (!lastData) {
          QLLabUI.setStatus(status, false, "sin corrida aún — simulá primero");
          return;
        }
        presentMcMemo(lastData, readMcFormParams(), false);
      });
    }

    setScenarios(1000);
    updateBarsDurationHint(null);
    setCancelVisible(false);

    root.refresh = refresh;
    root.applyNavFocus = function () {
      if (!global.QLNav) return;
      const focus = global.QLNav.takeFocus("montecarlo");
      if (!focus) return;
      if (focus.prefill) {
        const p = focus.prefill;
        if (p.sim_context) setSimContext(p.sim_context, { clearLabIds: true });
        if (p.n_scenarios != null) setScenarios(p.n_scenarios);
        if (p.n_bars != null) root.querySelector("#mc-bars").value = p.n_bars;
        if (p.noise_bps != null) root.querySelector("#mc-noise").value = p.noise_bps;
        if (p.seed != null) root.querySelector("#mc-seed").value = p.seed;
        if (!p.sim_context) {
          if (p.scan_id) root.querySelector("#mc-scan").value = p.scan_id;
          if (p.backtest_id) root.querySelector("#mc-bt").value = p.backtest_id;
        }
        if (p.store_paths != null) {
          var pathsEl = root.querySelector("#mc-paths");
          if (pathsEl) pathsEl.checked = !!p.store_paths;
        }
        updateBarsDurationHint(null);
      }
      if (focus.message) {
        QLLabUI.setStatus(status, true, focus.message);
        if (warnEl) warnEl.textContent = focus.message;
      }
    };
    root.applyPrefill = function (prefill) {
      if (!prefill || typeof prefill !== "object") return;
      if (prefill.sim_context) setSimContext(prefill.sim_context, { clearLabIds: true });
      if (prefill.n_scenarios != null) setScenarios(prefill.n_scenarios);
      if (prefill.n_bars != null) root.querySelector("#mc-bars").value = prefill.n_bars;
      if (prefill.noise_bps != null) root.querySelector("#mc-noise").value = prefill.noise_bps;
      if (prefill.seed != null) root.querySelector("#mc-seed").value = prefill.seed;
      // Solo aplicar scan/bt si NO viene sim_context (evita residuo TRXUSDT de Guided Lab)
      if (!prefill.sim_context) {
        if (prefill.scan_id) root.querySelector("#mc-scan").value = prefill.scan_id;
        if (prefill.backtest_id) root.querySelector("#mc-bt").value = prefill.backtest_id;
      }
      updateBarsDurationHint(null);
      if (prefill.message && warnEl) warnEl.textContent = prefill.message;
    };
    renderSourceBanner();
    root.applyNavFocus();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonteCarloPane = createMonteCarloPane;
})(window);
