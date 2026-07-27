/** Panel Monte Carlo — robustez trazable (schema v2). */
(function (global) {
  "use strict";

  function createMonteCarloPane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-montecarlo";
    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>MONTE CARLO — ROBUSTEZ DE ESTRATEGIA</h3>" +
      '<p class="muted" style="margin-top:0">' +
      "Mide sensibilidad bajo supuestos elegidos. <strong>No predice precios futuros.</strong>" +
      "</p>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.5rem">' +
      '<label class="field" title="Cantidad de escenarios independientes">Escenarios' +
      '<input id="mc-n" type="number" value="5" min="2" max="20" /></label>' +
      '<label class="field" title="Barras del dataset sintético 1m (horizonte)">Barras del dataset' +
      '<input id="mc-bars" type="number" value="16" min="8" max="60" /></label>' +
      '<label class="field" title="10 bps = 0,10 %">Ruido (bps)' +
      '<input id="mc-noise" type="number" value="10" min="0" max="500" step="1" /></label>' +
      '<label class="field" title="Misma seed + mismos datos = mismo resultado">Seed' +
      '<input id="mc-seed" type="number" value="42" /></label>' +
      '<label class="field" title="Opcional — vincula Scan">scan_id' +
      '<input id="mc-scan" type="text" placeholder="opcional" style="width:8em" /></label>' +
      '<label class="field" title="Opcional — vincula Backtest">backtest_id' +
      '<input id="mc-bt" type="text" placeholder="opcional" style="width:8em" /></label>' +
      '<label class="muted"><input type="checkbox" id="mc-paths" /> guardar trayectorias (máx 16)</label>' +
      '<button type="button" class="btn" id="mc-run">Simular</button>' +
      '<button type="button" class="btn secondary" id="mc-refresh">Actualizar</button>' +
      '<button type="button" class="btn secondary" id="mc-copy-id">Copiar run ID</button>' +
      '<span class="mono" id="mc-status">—</span>' +
      "</div>" +
      '<p class="muted" id="mc-warn" style="margin:0.4rem 0 0"></p>' +
      "</div>" +
      '<div class="pane-section" id="mc-ctx-section">' +
      "<h3>Contexto del experimento</h3>" +
      '<div class="mono" id="mc-context">—</div>' +
      '<div class="pane-row" style="margin-top:0.4rem;gap:0.4rem">' +
      '<button type="button" class="btn secondary" id="mc-open-bt" disabled>Abrir backtest</button>' +
      '<button type="button" class="btn secondary" id="mc-open-scan" disabled>Abrir scan</button>' +
      "</div>" +
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
    let lastData = null;

    function esc(s) {
      return QLLabUI.escapeHtml(s);
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

    function scenarioWarning(n) {
      if (n < 100) {
        return (
          "Advertencia: N=" +
          n +
          " es exploratorio (modo mini lab ≤20). No es garantía estadística."
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

    function renderContext(data) {
      const ctx = (data && data.context) || {};
      const cfg = (data && data.config) || {};
      ctxEl.innerHTML =
        row("Estrategia", na(ctx.strategy_name || ctx.strategy_id)) +
        row("Símbolos", na((ctx.symbols || []).join(", "))) +
        row("Venue", na(ctx.venue)) +
        row("Network", na(ctx.network)) +
        row("Mercado", na(ctx.market_type)) +
        row("Timeframe", na(ctx.timeframe || cfg.timeframe_hint)) +
        row("Dataset", na(ctx.dataset_id)) +
        row("Fuente dataset", na(ctx.dataset_source)) +
        row("Capital inicial", money(ctx.initial_equity) + " (lab)") +
        row("Backtest origen", na(ctx.backtest_id)) +
        row("Scan origen", na(ctx.scan_id)) +
        row("run_id", na(data && data.run_id)) +
        row("schema", na(data && data.schema_version)) +
        (ctx.orphan_technical_mode
          ? '<p class="status-bad" style="margin-top:0.4rem">' +
            esc(ctx.orphan_warning || "Modo técnico huérfano") +
            "</p>"
          : "");
      root.querySelector("#mc-open-bt").disabled = !ctx.backtest_id;
      root.querySelector("#mc-open-scan").disabled = !ctx.scan_id;
    }

    function renderExplain(data) {
      const cfg = (data && data.config) || {};
      const n = data && data.n_scenarios != null ? data.n_scenarios : cfg.n_scenarios;
      const bars = data && data.n_bars != null ? data.n_bars : cfg.n_bars;
      const noise = data && data.noise_bps != null ? data.noise_bps : cfg.noise_bps;
      const horizon =
        (data && data.bar_horizon_label) ||
        (cfg.bar_horizon_label ? cfg.bar_horizon_label : bars + " × 1m");
      explainEl.innerHTML =
        "<p><strong>Método:</strong> " +
        esc(na(data && data.method)) +
        " — perturbación OHLC gaussiana + re-ejecución del backtester.</p>" +
        "<p>Se generan <strong>" +
        esc(na(n)) +
        "</strong> versiones del dataset sintético (" +
        esc(na(horizon)) +
        "). Ruido σ = " +
        esc(na(noise)) +
        " bps (" +
        esc(noise != null ? (Number(noise) / 100).toFixed(2) + " %" : "—") +
        "). Seed=" +
        esc(na(data && data.seed)) +
        ". CI = IC de la <em>media</em> (Wald), no banda de un escenario individual.</p>" +
        "<p class=\"muted\">" +
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
      const initial = ctx.initial_equity;
      const finals = (data && data.final_equities) || [];
      const minE = finals.length ? Math.min.apply(null, finals.map(Number)) : null;
      const maxE = finals.length ? Math.max.apply(null, finals.map(Number)) : null;
      const mean = m.mean_equity != null ? m.mean_equity : data.mean_equity;
      const med = m.median_equity;
      cardsEl.style.display = "flex";
      cardsEl.style.flexWrap = "wrap";
      cardsEl.style.gap = "0.5rem";
      cardsEl.innerHTML =
        card("Capital inicial", money(initial), "lab") +
        card(
          "Media de los escenarios simulados",
          money(mean),
          pctFromInitial(mean, initial)
        ) +
        card("Mediana", money(med), pctFromInitial(med, initial)) +
        card("Mejor escenario", money(maxE), pctFromInitial(maxE, initial)) +
        card("Peor escenario", money(minE), pctFromInitial(minE, initial)) +
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
      renderHistogram(data.final_equities || []);
      out.innerHTML = QLLabUI.preJson(data);
    }

    function renderRuns(listPayload) {
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
              '<td><button type="button" class="btn secondary mc-open-run" data-id="' +
              esc(r.run_id) +
              '">abrir</button></td>' +
              "</tr>"
            );
          })
          .join("") +
        "</tbody></table>";
      runsEl.querySelectorAll(".mc-open-run").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          QLApi.labMonteCarloRun(id)
            .then(function (data) {
              renderResult(data);
            })
            .catch(function (err) {
              QLLabUI.setStatus(status, false, err.message);
            });
        });
      });
    }

    async function refresh() {
      const data = await QLApi.labMonteCarloHistory();
      renderResult(data.latest || null);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    root.querySelector("#mc-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    root.querySelector("#mc-copy-id").addEventListener("click", function () {
      const id = lastData && lastData.run_id;
      if (!id) {
        QLLabUI.setStatus(status, false, "sin run_id");
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(id).then(
          function () {
            QLLabUI.setStatus(status, true, "run_id copiado");
          },
          function () {
            QLLabUI.setStatus(status, false, "no se pudo copiar");
          }
        );
      }
    });

    root.querySelector("#mc-open-bt").addEventListener("click", function () {
      const id = lastData && lastData.context && lastData.context.backtest_id;
      if (id) QLLabUI.setStatus(status, true, "backtest_id=" + id + " (abrir panel Reports)");
    });
    root.querySelector("#mc-open-scan").addEventListener("click", function () {
      const id = lastData && lastData.context && lastData.context.scan_id;
      if (id) QLLabUI.setStatus(status, true, "scan_id=" + id + " (abrir Guided Lab / Scanner)");
    });

    QLLabUI.bindRun(root, "#mc-run", "#mc-status", "#mc-out", function () {
      const n = parseInt(root.querySelector("#mc-n").value, 10) || 5;
      const bars = parseInt(root.querySelector("#mc-bars").value, 10) || 16;
      const noise = parseFloat(root.querySelector("#mc-noise").value);
      const seed = parseInt(root.querySelector("#mc-seed").value, 10);
      const scan = (root.querySelector("#mc-scan").value || "").trim();
      const bt = (root.querySelector("#mc-bt").value || "").trim();
      const storePaths = root.querySelector("#mc-paths").checked;
      return QLApi.labMonteCarlo({
        n_scenarios: n,
        n_bars: bars,
        noise_bps: isFinite(noise) ? noise : 10,
        seed: isFinite(seed) ? seed : 42,
        scan_id: scan || null,
        backtest_id: bt || null,
        store_paths: storePaths,
      }).then(function (data) {
        renderResult(data);
        refresh().catch(function () {});
        return data;
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonteCarloPane = createMonteCarloPane;
})(window);
