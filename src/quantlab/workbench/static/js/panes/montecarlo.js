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
      "<h3>MONTE CARLO — ROBUSTEZ DE ESTRATEGIA</h3>" +
      '<p class="muted" style="margin-top:0">' +
      "Mide sensibilidad bajo supuestos elegidos. <strong>No predice precios futuros.</strong>" +
      "</p>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.5rem;align-items:flex-end">' +
      '<label class="field" title="Cantidad de escenarios independientes">Escenarios' +
      '<input id="mc-n" type="number" value="1000" min="2" max="1000000" step="1" /></label>' +
      '<div class="pane-row" id="mc-presets" style="gap:0.25rem;flex-wrap:wrap"></div>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.5rem;margin-top:0.4rem;align-items:flex-end">' +
      '<label class="field" title="Cada escenario vuelve a ejecutar la estrategia sobre estas N velas perturbadas.">' +
      "Velas utilizadas por escenario" +
      '<input id="mc-bars" type="number" value="60" min="8" max="500" /></label>' +
      '<span class="muted mono" id="mc-bars-duration" style="align-self:center"></span>' +
      '<label class="field" title="10 bps = 0,10 %">Ruido (bps)' +
      '<input id="mc-noise" type="number" value="10" min="0" max="500" step="1" /></label>' +
      '<label class="field" title="Misma seed + mismos datos = mismo resultado">Seed' +
      '<input id="mc-seed" type="number" value="42" /></label>' +
      '<label class="field" title="Opcional — vincula Scan">scan_id' +
      '<input id="mc-scan" type="text" placeholder="opcional" style="width:8em" /></label>' +
      '<label class="field" title="Opcional — vincula Backtest">backtest_id' +
      '<input id="mc-bt" type="text" placeholder="opcional" style="width:8em" /></label>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.5rem;margin-top:0.4rem;align-items:center">' +
      '<label class="muted" title="Guarda hasta 16 curvas completas para visualización. No limita la cantidad total de escenarios simulados.">' +
      '<input type="checkbox" id="mc-paths" /> Guardar muestra de trayectorias</label>' +
      '<button type="button" class="btn" id="mc-run">Simular</button>' +
      '<button type="button" class="btn secondary" id="mc-refresh">Actualizar</button>' +
      '<button type="button" class="btn secondary" id="mc-copy-id">Copiar run ID</button>' +
      '<button type="button" class="btn secondary" id="mc-cancel" disabled hidden>Cancelar</button>' +
      '<span class="mono" id="mc-status">—</span>' +
      "</div>" +
      '<p class="muted" id="mc-warn" style="margin:0.4rem 0 0"></p>' +
      '<div id="mc-cost" class="mono muted" style="margin-top:0.35rem"></div>' +
      '<div id="mc-progress" style="margin-top:0.35rem"></div>' +
      "</div>" +
      '<div class="pane-section" id="mc-ctx-section">' +
      "<h3>Contexto del experimento</h3>" +
      '<div class="mono" id="mc-context">—</div>' +
      '<div class="pane-row" style="margin-top:0.4rem;gap:0.4rem;flex-wrap:wrap">' +
      '<button type="button" class="btn secondary" id="mc-open-bt" disabled title="Sin backtest_id">Abrir backtest</button>' +
      '<button type="button" class="btn secondary" id="mc-open-scan" disabled title="Sin scan_id">Abrir scan</button>' +
      '<button type="button" class="btn secondary" id="mc-open-ds" disabled title="Sin dataset">Abrir dataset</button>' +
      '<span class="muted mono" id="mc-nav-hint" style="align-self:center"></span>' +
      "</div>" +
      '<div id="mc-dataset-detail" style="margin-top:0.5rem;display:none"></div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>¿Qué estamos simulando?</h3>" +
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
      return sign + p.toFixed(4) + " %";
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
        (ctx.orphan_technical_mode
          ? '<p class="status-bad" style="margin-top:0.4rem">' +
            esc(ctx.orphan_warning || "Modo técnico huérfano") +
            "</p>"
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
      var body = {
        n_scenarios: n,
        n_bars: bars,
        noise_bps: isFinite(noise) ? noise : 10,
        seed: isFinite(seed) ? seed : 42,
        scan_id: scan || null,
        backtest_id: bt || null,
        store_paths: storePaths,
        confirm_large: !!confirmLarge,
        mode: bt ? "normal" : "technical_lab",
        max_persisted_trajectories: MAX_TRAJECTORIES,
      };
      if (asyncFlag) body.async = true;
      return body;
    }

    async function runSimulation() {
      if (runBusy) return;
      var n = readScenarios();
      setScenarios(n);
      var bars = clampBars(parseInt(root.querySelector("#mc-bars").value, 10));
      root.querySelector("#mc-bars").value = String(bars);
      var noise = parseFloat(root.querySelector("#mc-noise").value);
      var seed = parseInt(root.querySelector("#mc-seed").value, 10);
      var scan = (root.querySelector("#mc-scan").value || "").trim();
      var bt = (root.querySelector("#mc-bt").value || "").trim();
      var storePaths = root.querySelector("#mc-paths").checked;

      var confirmLarge = false;
      if (n >= CONFIRM_LARGE_N) {
        if (!confirmLargeCost(n)) {
          QLLabUI.setStatus(status, false, "cancelado por usuario");
          return;
        }
        confirmLarge = true;
      }

      runBusy = true;
      QLLabUI.setStatus(status, true, "ejecutando…");
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
        if (p.n_scenarios != null) setScenarios(p.n_scenarios);
        if (p.n_bars != null) root.querySelector("#mc-bars").value = p.n_bars;
        if (p.seed != null) root.querySelector("#mc-seed").value = p.seed;
        if (p.scan_id) root.querySelector("#mc-scan").value = p.scan_id;
        if (p.backtest_id) root.querySelector("#mc-bt").value = p.backtest_id;
        updateBarsDurationHint(null);
      }
      if (focus.message) {
        QLLabUI.setStatus(status, true, focus.message);
        if (warnEl) warnEl.textContent = focus.message;
      }
    };
    root.applyNavFocus();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonteCarloPane = createMonteCarloPane;
})(window);
