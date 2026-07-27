/** Guided Lab — wizard venue→scan→estrategia→simular + LIVE unlock (F99/F100/F109). */
(function (global) {
  "use strict";

  function t(key, fallback) {
    if (global.QLi18n && typeof global.QLi18n.t === "function") {
      return global.QLi18n.t(key, fallback);
    }
    return fallback != null ? fallback : key;
  }

  function createGuidedLabPane() {
    const root = document.createElement("div");
    root.className = "pane-guided-lab";

    root.innerHTML =
      '<div class="pane-section">' +
      '<h3 data-i18n="pane.guided_lab">Guided Lab</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.intro">' +
      "Flujo: venue → scan → estrategia → simular. " +
      "LIVE solo tras usuario/contraseña (corte humano). Sin unlock = bloqueado.</p>" +
      '<div class="data-legend" role="note">' +
      '<div class="data-legend-row">' +
      '<span class="data-badge data-badge-real">HISTÓRICO Binance</span>' +
      "<span>Klines / ticks públicos reales del mercado. " +
      "Ranking y <em>Backtest top 5</em> miran las últimas N velas hasta ahora " +
      "(ej. de las 14:00 a las 15:01 según tamaño de vela).</span>" +
      "</div>" +
      '<div class="data-legend-row">' +
      '<span class="data-badge data-badge-synth">SINTÉTICO lab</span>' +
      "<span>Barras inventadas del laboratorio. " +
      "<em>Scan lab</em> y <em>Simular backtest</em> — no son precios de Binance.</span>" +
      "</div>" +
      "</div>" +
      '<div class="mono" id="gl-live">LIVE_BLOCKED = True</div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.unlock.title">0. Unlock LIVE (opcional)</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.unlock.hint">' +
      "Definí QUANTLAB_LIVE_USER / QUANTLAB_LIVE_PASSWORD en tu PC. " +
      "Nunca se guardan en git ni en disco de sesión.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-user" placeholder="usuario" autocomplete="username">' +
      '<input type="password" id="gl-pass" placeholder="contraseña" autocomplete="current-password">' +
      '<button type="button" class="btn secondary" id="gl-unlock" data-i18n="guided_lab.unlock.btn" data-tip="Valida usuario/contraseña LIVE locales.\nSin unlock el demo sigue bloqueado." data-i18n-tip="tip.gl.unlock">Unlock</button>' +
      '<button type="button" class="btn secondary" id="gl-lock" data-i18n="guided_lab.lock.btn" data-tip="Vuelve a LIVE_BLOCKED.\nCorta el camino demo hasta nuevo unlock." data-i18n-tip="tip.gl.lock">Lock</button>' +
      "</div>" +
      '<span class="mono muted" id="gl-unlock-status">—</span>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.venue">1. Venue</h3>' +
      '<select id="gl-venue">' +
      '<option value="binance" data-i18n="guided_lab.venue.binance">binance (MD público / demo)</option>' +
      '<option value="paper" data-i18n="guided_lab.venue.paper">paper (simulado)</option>' +
      '<option value="a3" data-i18n="guided_lab.venue.a3">a3 (MD fake|env / paper)</option>' +
      "</select>" +
      '<div id="gl-section-a3" style="display:none">' +
      '<div class="pane-row" style="margin-top:0.5em">' +
      '<label class="muted"><span data-i18n="guided_lab.a3.md_source">A3 md_source</span> ' +
      '<select id="gl-a3-md">' +
      '<option value="fake" data-i18n="guided_lab.a3.md_fake">fake (CI)</option>' +
      '<option value="env" data-i18n="guided_lab.a3.md_env">env (read-only)</option>' +
      "</select></label>" +
      '<button type="button" class="btn secondary" id="gl-a3-status-btn" data-i18n="guided_lab.a3.status_btn" data-tip="Consulta estado del MD A3 (fake/env).\nRead-only; no envía órdenes." data-i18n-tip="tip.gl.a3_status">Estado MD A3</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-connect" data-i18n="guided_lab.a3.connect" data-tip="Conecta PaperBroker A3 en esta sesión.\nSin routing a venue real." data-i18n-tip="tip.gl.a3_connect">Conectar paper A3</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-instr" data-i18n="guided_lab.a3.instruments" data-tip="Lista instrumentos disponibles en A3.\nÚtil antes del snapshot." data-i18n-tip="tip.gl.a3_instr">Listar instrumentos</button>' +
      '<button type="button" class="btn secondary" id="gl-a3-snap" data-i18n="guided_lab.a3.snapshot" data-tip="Toma un snapshot MD del símbolo elegido.\nSolo lectura." data-i18n-tip="tip.gl.a3_snap">Snapshot</button>' +
      '<input type="text" id="gl-a3-sym" placeholder="símbolo" style="width:7em">' +
      '<span class="mono muted" id="gl-a3-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-a3-out">—</div>' +
      '<div class="pane-row" style="margin-top:0.5em">' +
      '<select id="gl-a3-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="gl-a3-qty" value="1" style="width:5em" placeholder="qty">' +
      '<button type="button" class="btn" id="gl-a3-paper" data-i18n="guided_lab.a3.paper_submit" data-tip="Envía una orden paper vía A3.\nNo hay routing a exchange real." data-i18n-tip="tip.gl.a3_paper">Enviar paper (A3)</button>' +
      '<span class="mono muted" id="gl-a3-paper-status">—</span>' +
      "</div>" +
      '<p class="muted" data-i18n="guided_lab.a3.footer">A3 = PaperBroker (sin routing venue). MD env: QUANTLAB_A3_MD_READONLY=1 + creds.</p>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.scan">2. Escanear</h3>' +
      '<p class="muted" style="margin:0 0 0.4rem;font-size:0.85em">' +
      '<span class="data-badge data-badge-synth">SINTÉTICO</span> Scan lab · ' +
      '<span class="data-badge data-badge-real">HISTÓRICO</span> Scan Binance / Ranking / Backtest top 5' +
      "</p>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="gl-scan" data-i18n="guided_lab.scan.lab" data-tip="Escanea el lab SINTÉTICO local.\nNo son datos de Binance." data-i18n-tip="tip.gl.scan_lab">Scan lab (sintético)</button>' +
      '<button type="button" class="btn secondary" id="gl-scan-bn" data-i18n="guided_lab.scan.binance" style="display:none" data-tip="Lista pares USDT — MD HISTÓRICO/público Binance.\nSolo lectura." data-i18n-tip="tip.gl.scan_bn">Scan Binance (histórico)</button>' +
      '<button type="button" class="btn secondary" id="gl-scan-bn-alpha" data-i18n="guided_lab.scan.binance_alpha" style="display:none" data-tip="Ranking alpha sobre klines HISTÓRICAS Binance.\nÚltimas N velas hasta ahora." data-i18n-tip="tip.gl.scan_alpha">Ranking alpha (histórico)</button>' +
      '<button type="button" class="btn" id="gl-pipeline-bn" data-i18n="guided_lab.pipeline.binance" style="display:none" data-tip="Backtest top 5 sobre klines HISTÓRICAS Binance.\nPaper + fees; sin órdenes live." data-i18n-tip="tip.gl.pipeline">Backtest top 5 (histórico)</button>' +
      '<span class="mono muted" id="gl-scan-status">—</span>' +
      "</div>" +
      '<div class="mono" id="gl-scan-out">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.strategy">3. Estrategia</h3>' +
      '<select id="gl-strategy"></select>' +
      '<p class="muted mono" id="gl-strategy-hint" style="margin:0.25rem 0 0">cargando catálogo…</p>' +
      '<div class="pane-row" style="margin-top:0.5rem;flex-wrap:wrap;gap:0.5rem;align-items:center">' +
      '<span class="data-badge data-badge-real">HISTÓRICO Binance</span>' +
      '<label class="muted" title="Intervalo de klines Binance (MD público). 1m = más fino disponible sin L2/ticks.">' +
      "velas " +
      '<select id="gl-interval">' +
      '<option value="1m">1m (más fino)</option>' +
      '<option value="3m">3m</option>' +
      '<option value="5m" selected>5m</option>' +
      '<option value="15m">15m</option>' +
      '<option value="30m">30m</option>' +
      '<option value="1h">1h</option>' +
      '<option value="4h">4h</option>' +
      '<option value="1d">1d</option>' +
      "</select></label>" +
      '<label class="muted" title="Cantidad de velas Binance (8–3000). Pagina API de a 1000. Default 1200 ≈ 20× el histórico de 60.">' +
      "n_bars/klines " +
      '<input type="number" id="gl-bars" value="1200" min="8" max="3000" style="width:4.5em">' +
      "</label>" +
      "</div>" +
      '<p class="muted" id="gl-bars-hint" style="margin:0.35rem 0 0;font-size:0.85em">' +
      "Ranking / Backtest top 5: mira el mercado REAL de Binance y toma las últimas N velas hasta ahora " +
      "(ej. 5m×1200 ≈ desde hace ~4 días hasta este momento). Detalle fills abajo + panel Reports." +
      "</p>" +
      "</div>" +
      '<div class="pane-section">' +
      '<h3 data-i18n="guided_lab.section.simulate">4. Simular (paper)</h3>' +
      '<p class="data-badge data-badge-synth" style="display:inline-block;margin:0 0 0.4rem">DATOS SINTÉTICOS (lab)</p>' +
      '<p class="muted" style="margin:0 0 0.45rem;font-size:0.85em">' +
      "No usa Binance. Genera barras inventadas del lab. " +
      "Elegí <strong>días</strong> (o velas). Los <strong>trades no se fijan</strong>: los decide la estrategia." +
      "</p>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.5rem;align-items:center">' +
      '<label class="muted" title="Días de recorrido sintético. Se convierten a velas según el intervalo de arriba.">' +
      "días sim " +
      '<input type="number" id="gl-sim-days" value="7" min="1" max="90" style="width:3.5em">' +
      "</label>" +
      '<label class="muted" title="Velas sintéticas (4–2000). Si tocás días, se recalcula solo.">' +
      "velas sim " +
      '<input type="number" id="gl-sim-bars" value="2000" min="4" max="2000" style="width:4.5em">' +
      "</label>" +
      '<span class="mono muted" id="gl-sim-hint" style="font-size:0.8em">—</span>' +
      "</div>" +
      '<div class="pane-row" style="margin-top:0.4rem">' +
      '<button type="button" class="btn" id="gl-run" data-i18n="guided_lab.simulate.run" data-tip="Backtest paper con barras SINTÉTICAS del lab.\nNo son klines de Binance; no envía órdenes." data-i18n-tip="tip.gl.run">Simular backtest (sintético)</button>' +
      '<span class="mono muted" id="gl-run-status">—</span>' +
      "</div>" +
      '<dl class="kv" id="gl-result"></dl>' +
      "</div>" +
      '<div class="pane-section" id="gl-section-demo" style="display:none">' +
      '<h3 data-i18n="guided_lab.section.demo">5. Demo order (post-unlock)</h3>' +
      '<p class="muted" style="margin-top:0" data-i18n="guided_lab.demo.hint">' +
      "Fill demo Binance. Requiere unlock. " +
      "Default: sim local. Testnet remoto solo con QUANTLAB_DEMO_USE_TESTNET=1 + keys.</p>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-demo-sym" value="BTCUSDT" style="width:7em">' +
      '<select id="gl-demo-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
      '<input type="text" id="gl-demo-qty" value="0.001" style="width:5em">' +
      '<input type="text" id="gl-demo-price" placeholder="price (LIMIT)" style="width:7em">' +
      '<label class="muted" style="display:flex;align-items:center;gap:0.35rem">' +
      '<input type="checkbox" id="gl-demo-mirror">' +
      '<span data-i18n="guided_lab.demo.mirror">Mirror a paper journal</span></label>' +
      '<button type="button" class="btn" id="gl-demo-submit" data-i18n="guided_lab.demo.submit" data-tip="Envía orden demo post-unlock.\nDefault: sim local; testnet solo con flag+keys." data-i18n-tip="tip.gl.demo_submit">Enviar demo</button>' +
      '<span class="mono muted" id="gl-demo-status">—</span>' +
      "</div>" +
      '<div class="pane-row">' +
      '<input type="text" id="gl-demo-cancel-id" placeholder="order_id" style="width:8em">' +
      '<button type="button" class="btn secondary" id="gl-demo-cancel" data-i18n="guided_lab.demo.cancel" data-tip="Cancela una orden demo por order_id.\nRequiere unlock activo." data-i18n-tip="tip.gl.demo_cancel">Cancelar orden</button>' +
      '<button type="button" class="btn secondary" id="gl-demo-open" data-i18n="guided_lab.demo.open_orders" data-tip="Lista órdenes demo abiertas.\nSolo tras unlock." data-i18n-tip="tip.gl.demo_open">Ver abiertas</button>' +
      "</div>" +
      '<div class="mono" id="gl-demo-out">—</div>' +
      "</div>";

    const liveEl = root.querySelector("#gl-live");
    const scanOut = root.querySelector("#gl-scan-out");
    const scanStatus = root.querySelector("#gl-scan-status");
    const runStatus = root.querySelector("#gl-run-status");
    const resultEl = root.querySelector("#gl-result");
    const unlockStatus = root.querySelector("#gl-unlock-status");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function statusErr(el, err) {
      el.textContent = t("guided_lab.status.error", "error") + ": " + err.message;
      el.className = "mono status-bad";
    }

    function formatBacktestRun(r, strategyId) {
      if (!r.ok) {
        return (
          "<div class=\"bt-run bad\"><strong>" +
          esc(r.symbol) +
          "</strong> ERROR: " +
          esc(r.error) +
          "</div>"
        );
      }
      const res = r.result || {};
      const fills = Number(res.n_fills || 0);
      const orders = Number(res.n_orders || 0);
      const eq = res.final_equity;
      const fees = res.total_fees != null ? res.total_fees : "—";
      const feeSched = res.fee_schedule || {};
      const takerBps = feeSched.taker_bps != null ? feeSched.taker_bps : "10";
      const verdict = res.verdict_es || "";
      const br = res.bar_range || {};
      const cls = fills > 0 ? "ok" : "warn";
      let meaning = "";
      if (fills > 0) {
        meaning =
          "Hubo trades simulados. Fees Binance Spot VIP0 (~" +
          takerBps +
          " bps/lado) ya descontados del cash.";
      } else if (orders > 0) {
        meaning =
          "Puso órdenes LIMIT pero el precio de la vela no las tocó → 0 fills. Capital intacto.";
      } else {
        meaning =
          "No generó órdenes. Con MM en alts baratas era común; ya hay fix de spread. Probá de nuevo o usá momentum.";
      }
      const fillRows = Array.isArray(res.fills) ? res.fills : [];
      let fillsHtml = "";
      if (fillRows.length) {
        fillsHtml =
          "<details class=\"bt-fills\" open>" +
          "<summary>Detalle fills (" +
          fillRows.length +
          (res.fills_truncated ? "+" : "") +
          ")</summary>" +
          '<table class="data-table"><thead><tr>' +
          "<th>ts</th><th>side</th><th>px</th><th>qty</th><th>fee</th>" +
          "</tr></thead><tbody>" +
          fillRows
            .map(function (f) {
              return (
                "<tr><td class=\"mono\">" +
                esc((f.timestamp || "").slice(0, 19)) +
                "</td><td>" +
                esc(f.side || "—") +
                "</td><td class=\"mono num\">" +
                esc(f.price) +
                "</td><td class=\"mono num\">" +
                esc(f.quantity) +
                "</td><td class=\"mono num\">" +
                esc(f.fee) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table></details>";
      }
      const rangeLine =
        br.start && br.end
          ? "<br><span class=\"muted\">rango " +
            esc(formatRangeHuman(br.start, br.end)) +
            " (" +
            esc(br.start) +
            " → " +
            esc(br.end) +
            ")</span>"
          : "";
      const src = String(res.data_source || "");
      const isHist = src.indexOf("binance") >= 0;
      const badge = isHist
        ? '<span class="data-badge data-badge-real">HISTÓRICO Binance</span> '
        : src === "synthetic" || r.symbol === "SYN"
          ? '<span class="data-badge data-badge-synth">SINTÉTICO lab</span> '
          : "";
      return (
        "<div class=\"bt-run " +
        cls +
        "\">" +
        badge +
        "<strong>" +
        esc(r.symbol) +
        "</strong> · estrategia <span class=\"mono\">" +
        esc(strategyId || res.strategy_id || "—") +
        "</span><br>" +
        "capital final <span class=\"mono\">" +
        esc(eq) +
        "</span> · fees <span class=\"mono\">" +
        esc(fees) +
        "</span> · órdenes=" +
        esc(orders) +
        " · fills=" +
        esc(fills) +
        " · barras=" +
        esc(res.n_bars) +
        rangeLine +
        "<br><span class=\"muted\">" +
        esc(verdict || meaning) +
        "</span>" +
        fillsHtml +
        "</div>"
      );
    }

    function intervalMinutes(iv) {
      const map = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
      };
      return map[iv] || 5;
    }

    function daysToSimBars(days, iv) {
      const mins = intervalMinutes(iv);
      let n = Math.round((Number(days) * 24 * 60) / mins);
      if (n < 4) n = 4;
      if (n > 2000) n = 2000;
      return n;
    }

    function approxDaysFromBars(nBars, iv) {
      const mins = intervalMinutes(iv);
      return ((Number(nBars) * mins) / (24 * 60)).toFixed(2);
    }

    function formatRangeHuman(startIso, endIso) {
      if (!startIso || !endIso) return "";
      function short(iso) {
        try {
          const d = new Date(iso);
          if (isNaN(d.getTime())) return String(iso).slice(0, 16);
          return d.toLocaleString("es-AR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          });
        } catch (e) {
          return String(iso).slice(0, 16);
        }
      }
      return short(startIso) + " → " + short(endIso);
    }

    function binanceBarOpts() {
      const intervalEl = root.querySelector("#gl-interval");
      const barsEl = root.querySelector("#gl-bars");
      let interval = (intervalEl && intervalEl.value) || "5m";
      let klineLimit = Number(barsEl && barsEl.value) || 1200;
      if (klineLimit < 8) klineLimit = 8;
      if (klineLimit > 3000) klineLimit = 3000;
      return { interval: interval, kline_limit: klineLimit };
    }

    function syncSimFromDays() {
      const daysEl = root.querySelector("#gl-sim-days");
      const simBarsEl = root.querySelector("#gl-sim-bars");
      const hint = root.querySelector("#gl-sim-hint");
      const iv = (root.querySelector("#gl-interval") || {}).value || "5m";
      const days = Number(daysEl && daysEl.value) || 7;
      const n = daysToSimBars(days, iv);
      if (simBarsEl) simBarsEl.value = String(n);
      if (hint) {
        hint.textContent =
          "≈ " +
          n +
          " velas sintéticas × " +
          iv +
          " (~" +
          approxDaysFromBars(n, iv) +
          " días lab). Trades = resultado de la estrategia, no un número fijo.";
      }
    }

    function syncBarsHint() {
      const hint = root.querySelector("#gl-bars-hint");
      const opts = binanceBarOpts();
      if (!hint) return;
      const n = opts.kline_limit;
      const iv = opts.interval;
      const daysApprox = approxDaysFromBars(n, iv);
      hint.textContent =
        "HISTÓRICO Binance: mira el mercado USDT real y toma las últimas " +
        n +
        " velas × " +
        iv +
        " (~" +
        daysApprox +
        " días hacia atrás hasta AHORA). Ej.: si son las 15:01 y pedís 12×1h, cubre ~03:01→15:01. " +
        "Ranking y Backtest top 5 usan ESTO. Simular (abajo) es otra cosa: sintético.";
      syncSimFromDays();
    }

    const glInterval = root.querySelector("#gl-interval");
    const glBars = root.querySelector("#gl-bars");
    const glSimDays = root.querySelector("#gl-sim-days");
    const glSimBars = root.querySelector("#gl-sim-bars");
    if (glInterval) glInterval.addEventListener("change", syncBarsHint);
    if (glBars) glBars.addEventListener("input", syncBarsHint);
    if (glSimDays) {
      glSimDays.addEventListener("input", syncSimFromDays);
      glSimDays.addEventListener("change", syncSimFromDays);
    }
    if (glSimBars) {
      glSimBars.addEventListener("input", function () {
        const hint = root.querySelector("#gl-sim-hint");
        const iv = (root.querySelector("#gl-interval") || {}).value || "5m";
        let n = Number(glSimBars.value) || 24;
        if (n < 4) n = 4;
        if (n > 2000) n = 2000;
        if (hint) {
          hint.textContent =
            n +
            " velas sintéticas × " +
            iv +
            " (~" +
            approxDaysFromBars(n, iv) +
            " días). Trades = resultado de la estrategia.";
        }
      });
    }
    syncBarsHint();

    let lastBinanceSymbols = [];

    function applyVenueUi() {
      const venue = root.querySelector("#gl-venue").value;
      const a3Section = root.querySelector("#gl-section-a3");
      const demoSection = root.querySelector("#gl-section-demo");
      const scanBn = root.querySelector("#gl-scan-bn");
      const scanBnAlpha = root.querySelector("#gl-scan-bn-alpha");
      const pipelineBn = root.querySelector("#gl-pipeline-bn");
      if (a3Section) {
        a3Section.style.display = venue === "a3" ? "" : "none";
      }
      if (demoSection) {
        demoSection.style.display = venue === "binance" ? "" : "none";
      }
      const showBn = venue === "binance";
      if (scanBn) {
        scanBn.style.display = showBn ? "" : "none";
      }
      if (scanBnAlpha) {
        scanBnAlpha.style.display = showBn ? "" : "none";
      }
      if (pipelineBn) {
        pipelineBn.style.display = showBn ? "" : "none";
      }
    }

    function refreshLive() {
      return QLApi.liveStatus()
        .then(function (data) {
          const unlocked = data.unlocked === true;
          const demo = data.demo || {};
          const transport = demo.transport || (unlocked ? "—" : "blocked");
          liveEl.textContent =
            "LIVE_BLOCKED=" +
            data.live_blocked +
            " · unlocked=" +
            unlocked +
            " · configured=" +
            data.credentials_configured +
            " · transport=" +
            transport +
            (demo.n_fills != null ? " · fills=" + demo.n_fills : "");
          liveEl.className = unlocked ? "mono status-ok" : "mono status-bad";
          unlockStatus.textContent = unlocked
            ? t("guided_lab.status.unlock_active", "unlock activo") +
                " (" +
                esc(data.venue_scope) +
                ")"
            : data.credentials_configured
              ? t("guided_lab.status.blocked_creds", "bloqueado — ingresá user/pass")
              : t(
                  "guided_lab.status.blocked_env",
                  "bloqueado — configurá env QUANTLAB_LIVE_USER/PASSWORD"
                );
        })
        .catch(function (err) {
          liveEl.textContent =
            t("guided_lab.status.error", "error") + ": " + err.message;
        });
    }

    root.querySelector("#gl-unlock").addEventListener("click", function () {
      const user = root.querySelector("#gl-user").value;
      const pass = root.querySelector("#gl-pass").value;
      unlockStatus.textContent = t("guided_lab.status.validating", "validando…");
      QLApi.liveUnlock(user, pass, "binance_demo")
        .then(function () {
          root.querySelector("#gl-pass").value = "";
          return refreshLive();
        })
        .catch(function (err) {
          statusErr(unlockStatus, err);
        });
    });

    root.querySelector("#gl-lock").addEventListener("click", function () {
      QLApi.liveLock()
        .then(function () {
          return refreshLive();
        })
        .catch(function (err) {
          statusErr(unlockStatus, err);
        });
    });

    root.querySelector("#gl-venue").addEventListener("change", applyVenueUi);

    const a3Status = root.querySelector("#gl-a3-status");
    const a3Out = root.querySelector("#gl-a3-out");
    function a3MdSource() {
      return root.querySelector("#gl-a3-md").value || "fake";
    }
    root.querySelector("#gl-a3-status-btn").addEventListener("click", function () {
      a3Status.textContent = t("guided_lab.status.querying", "consultando…");
      QLApi.a3MdStatus()
        .then(function (data) {
          a3Status.textContent = data.env_ready
            ? t("guided_lab.status.env_ready", "env listo")
            : t("guided_lab.status.env_not_ready", "env no listo") +
                " (" +
                esc(data.reason) +
                ")";
          a3Status.className = data.env_ready ? "mono status-ok" : "mono muted";
          a3Out.textContent =
            "flag=" +
            data.md_readonly_flag +
            " creds=" +
            data.credentials_configured +
            " env=" +
            esc(data.environment) +
            " · " +
            esc(data.note);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-connect").addEventListener("click", function () {
      const md = a3MdSource();
      a3Status.textContent =
        t("guided_lab.status.a3_connecting", "conectando A3 paper…") + " md=" + md;
      root.querySelector("#gl-venue").value = "a3";
      applyVenueUi();
      QLApi.connect("a3", "paper", { md_source: md })
        .then(function (data) {
          a3Status.textContent = data.ok
            ? t("guided_lab.status.a3_connected", "A3 paper conectado") + " (" + md + ")"
            : t("guided_lab.status.failed", "falló");
          a3Status.className = data.ok ? "mono status-ok" : "mono status-bad";
          a3Out.textContent = esc(JSON.stringify(data.health || data, null, 0)).slice(0, 280);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-instr").addEventListener("click", function () {
      a3Status.textContent = t("guided_lab.status.listing", "listando…");
      QLApi.instruments()
        .then(function (data) {
          const items = data.instruments || data.items || [];
          a3Status.textContent = "ok (" + items.length + ")";
          a3Status.className = "mono status-ok";
          if (items.length && !root.querySelector("#gl-a3-sym").value) {
            root.querySelector("#gl-a3-sym").value = items[0].symbol || "";
          }
          a3Out.innerHTML = items
            .slice(0, 12)
            .map(function (it) {
              return esc(it.symbol || it.instrument_id || JSON.stringify(it));
            })
            .join("<br>") || "—";
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-snap").addEventListener("click", function () {
      const sym = root.querySelector("#gl-a3-sym").value.trim();
      if (!sym) {
        a3Status.textContent = t(
          "guided_lab.status.symbol_required",
          "ingresá símbolo o listá instrumentos"
        );
        a3Status.className = "mono status-bad";
        return;
      }
      a3Status.textContent = t("guided_lab.status.snapshot", "snapshot…");
      QLApi.snapshot(sym)
        .then(function (data) {
          a3Status.textContent = t("guided_lab.status.snapshot_ok", "snapshot ok");
          a3Status.className = "mono status-ok";
          const s = data.snapshot || data;
          a3Out.textContent =
            esc(s.symbol || sym) +
            " bid=" +
            esc(s.bid) +
            " ask=" +
            esc(s.ask) +
            " last=" +
            esc(s.last);
        })
        .catch(function (err) {
          statusErr(a3Status, err);
        });
    });
    root.querySelector("#gl-a3-paper").addEventListener("click", function () {
      const sym = root.querySelector("#gl-a3-sym").value.trim();
      const side = root.querySelector("#gl-a3-side").value;
      const qty = root.querySelector("#gl-a3-qty").value.trim();
      const paperStatus = root.querySelector("#gl-a3-paper-status");
      if (!sym || !qty) {
        paperStatus.textContent = t(
          "guided_lab.status.symbol_qty_required",
          "símbolo y qty requeridos"
        );
        paperStatus.className = "mono status-bad";
        return;
      }
      paperStatus.textContent = t("guided_lab.status.sending_paper", "enviando paper…");
      QLApi.paperSubmit({
        intent_type: "place_order",
        instrument_id: sym,
        side: side,
        quantity: qty,
        order_type: "market",
      })
        .then(function (res) {
          const ack = res.ack || {};
          paperStatus.textContent =
            (ack.status || "?") + " · " + (ack.order_id || "") + " · " + (ack.message || "");
          paperStatus.className = "mono status-ok";
          const acct = res.account || {};
          a3Out.textContent =
            t("guided_lab.status.paper_ok", "paper ok") +
            " · cash=" +
            esc(acct.cash) +
            " · equity=" +
            esc(acct.equity);
        })
        .catch(function (err) {
          statusErr(paperStatus, err);
        });
    });

    root.querySelector("#gl-scan").addEventListener("click", function () {
      scanStatus.textContent = t("guided_lab.status.scanning_lab", "escaneando lab…");
      QLApi.labScanner({ top_n: 3 })
        .then(function (data) {
          scanStatus.textContent = t("guided_lab.status.scan_lab_ok", "ok (lab)");
          scanStatus.className = "mono status-ok";
          const selected = data.selected || [];
          const scores = data.scores || [];
          scanOut.innerHTML =
            '<div class="bt-summary"><span class="data-badge data-badge-synth">SINTÉTICO lab</span> ' +
            "Ranking sobre barras inventadas del lab (no es Binance).</div>" +
            selected
              .map(function (id, i) {
                const sc = scores[i] || {};
                return esc(id) + ' <span class="muted">composite=' + esc(sc.composite) + "</span>";
              })
              .join("<br>");
        })
        .catch(function (err) {
          statusErr(scanStatus, err);
        });
    });

    root.querySelector("#gl-scan-bn").addEventListener("click", function () {
      scanStatus.textContent = t("guided_lab.status.scanning_binance", "escaneando Binance…");
      QLApi.binanceScan(20)
        .then(function (data) {
          scanStatus.textContent = t("guided_lab.status.scan_binance_ok", "ok (binance MD)");
          scanStatus.className = "mono status-ok";
          const symbols = data.symbols || [];
          lastBinanceSymbols = symbols.slice(0, 5);
          const tickers = data.tickers || [];
          scanOut.innerHTML =
            '<div class="bt-summary"><span class="data-badge data-badge-real">HISTÓRICO Binance</span> ' +
            "MD público en vivo / book (solo lectura).</div>" +
            "símbolos=" +
            esc(data.n_symbols) +
            "<br>" +
            tickers
              .map(function (tk) {
                return esc(tk.symbol) + " bid=" + esc(tk.bid) + " ask=" + esc(tk.ask);
              })
              .join("<br>") +
            (symbols.length
              ? "<br><span class=\"muted\">…" + esc(symbols.slice(0, 5).join(", ")) + "</span>"
              : "");
        })
        .catch(function (err) {
          statusErr(scanStatus, err);
        });
    });

    root.querySelector("#gl-scan-bn-alpha").addEventListener("click", function () {
      scanStatus.textContent = t(
        "guided_lab.status.scanning_binance_alpha",
        "ranking alpha Binance…"
      );
      QLApi.binanceScanner(
        Object.assign({ top_n: 5, symbol_limit: 15 }, binanceBarOpts())
      )
        .then(function (data) {
          scanStatus.textContent = t(
            "guided_lab.status.scan_binance_alpha_ok",
            "ok (alpha Binance)"
          );
          scanStatus.className = "mono status-ok";
          const selected = data.selected_symbols || [];
          lastBinanceSymbols = selected.slice();
          const scores = data.scores || [];
          scanOut.innerHTML =
            '<div class="bt-summary"><span class="data-badge data-badge-real">HISTÓRICO Binance</span> ' +
            "Ranking alpha sobre klines reales (últimas N velas hasta ahora).</div>" +
            "interval=" +
            esc(data.interval) +
            " · klines=" +
            esc(data.kline_limit) +
            " · fetched=" +
            esc(data.fetched != null ? data.fetched : data.n_symbols_fetched) +
            " · eligible=" +
            esc(data.eligible != null ? data.eligible : "—") +
            " · excluded=" +
            esc(data.excluded != null ? data.excluded : 0) +
            " · top=" +
            esc(data.top_n) +
            (data.note
              ? '<div class="muted" style="margin-top:4px">' + esc(data.note) + "</div>"
              : "") +
            (data.exclusion_counts
              ? '<div class="muted">exclusiones: ' +
                esc(JSON.stringify(data.exclusion_counts)) +
                "</div>"
              : "") +
            "<br>" +
            selected
              .map(function (sym, i) {
                const sc = scores[i] || {};
                return (
                  esc(sym) +
                  ' <span class="muted">composite=' +
                  esc(sc.composite) +
                  "</span>"
                );
              })
              .join("<br>");
        })
        .catch(function (err) {
          statusErr(scanStatus, err);
        });
    });

    root.querySelector("#gl-pipeline-bn").addEventListener("click", function () {
      const strategy = root.querySelector("#gl-strategy").value;
      const barOpts = binanceBarOpts();
      runStatus.textContent = t("guided_lab.status.pipeline_binance", "pipeline Binance…");
      resultEl.innerHTML = "";
      QLApi.binancePipeline(
        Object.assign(
          {
            strategy_id: strategy,
            top_n: 5,
            symbol_limit: 15,
            experiment_id: "wb-bn-pipe",
          },
          barOpts
        )
      )
        .then(function (data) {
          runStatus.textContent = data.ok
            ? t("guided_lab.status.pipeline_ok", "pipeline ok")
            : t("guided_lab.status.failed", "falló");
          runStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          const scanner = data.scanner || {};
          const batch = data.backtests || {};
          const runs = batch.runs || [];
          lastBinanceSymbols = (scanner.selected_symbols || []).slice();
          const zeroFills = runs.every(function (r) {
            return r.ok && Number((r.result || {}).n_fills || 0) === 0;
          });
          const firstRange =
            runs.find(function (r) {
              return r.ok && r.result && r.result.bar_range;
            }) || null;
          const br0 =
            firstRange && firstRange.result ? firstRange.result.bar_range : null;
          const rangeTxt = br0
            ? formatRangeHuman(br0.start, br0.end)
            : "últimas " +
              (scanner.kline_limit || barOpts.kline_limit) +
              " velas hasta ahora";
          scanOut.innerHTML =
            "<div class=\"bt-summary\">" +
            '<span class="data-badge data-badge-real">HISTÓRICO Binance</span> ' +
            "<strong>Qué se hizo</strong><br>" +
            "1) Miró el mercado real Binance USDT y tomó klines " +
            esc(scanner.interval || barOpts.interval) +
            " × " +
            esc(scanner.kline_limit || barOpts.kline_limit) +
            ".<br>" +
            "2) Ventana temporal: <span class=\"mono\">" +
            esc(rangeTxt) +
            "</span> (hacia atrás desde el momento de la consulta).<br>" +
            "3) Ranking eligió pares; backtest corrió <span class=\"mono\">" +
            esc(data.strategy_id) +
            "</span> (paper + fees; sin órdenes live).<br>" +
            "4) fills = trades de la estrategia en ese histórico. Detalle abajo + panel Reports." +
            (zeroFills
              ? "<br><strong>Si ves 0 fills:</strong> la señal no cruzó el OHLC. Probá momentum o más klines."
              : "") +
            "</div>" +
            "<div class=\"bt-list\">" +
            runs.map(function (r) {
              return formatBacktestRun(r, data.strategy_id);
            }).join("") +
            "</div>";
          resultEl.innerHTML =
            "<dt>tipo de datos</dt><dd><span class=\"data-badge data-badge-real\">HISTÓRICO Binance</span></dd>" +
            "<dt>ventana</dt><dd class=\"mono\">" +
            esc(rangeTxt) +
            "</dd>" +
            "<dt>strategy</dt><dd class=\"mono\">" +
            esc(data.strategy_id) +
            "</dd>" +
            "<dt>interval × klines</dt><dd class=\"mono\">" +
            esc(scanner.interval || barOpts.interval) +
            " × " +
            esc(scanner.kline_limit || barOpts.kline_limit) +
            "</dd>" +
            "<dt>n_ok</dt><dd class=\"mono num\">" +
            esc(batch.n_ok) +
            "/" +
            esc(batch.n_requested) +
            "</dd>" +
            "<dt>live</dt><dd class=\"mono\">bloqueado</dd>";
        })
        .catch(function (err) {
          statusErr(runStatus, err);
        });
    });

    root.querySelector("#gl-run").addEventListener("click", function () {
      const strategy = root.querySelector("#gl-strategy").value;
      const iv = (root.querySelector("#gl-interval") || {}).value || "5m";
      let nBars = Number(root.querySelector("#gl-sim-bars").value);
      if (!nBars || nBars < 4) {
        const days = Number(root.querySelector("#gl-sim-days").value) || 7;
        nBars = daysToSimBars(days, iv);
      }
      if (nBars < 4) nBars = 4;
      if (nBars > 2000) nBars = 2000;
      runStatus.textContent = t("guided_lab.status.simulating", "simulando…");
      resultEl.innerHTML = "";
      QLApi.labBacktest({ strategy_id: strategy, n_bars: nBars })
        .then(function (data) {
          runStatus.textContent = data.ok
            ? t("guided_lab.status.simulation_ok", "simulación ok (sintético)")
            : t("guided_lab.status.failed", "falló");
          runStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          const br = data.bar_range || {};
          const daysApprox = approxDaysFromBars(data.n_bars, iv);
          resultEl.innerHTML =
            "<dt>tipo de datos</dt><dd><span class=\"data-badge data-badge-synth\">SINTÉTICO lab</span> — no es Binance</dd>" +
            "<dt>horizonte</dt><dd class=\"mono\">" +
            esc(data.n_bars) +
            " velas (~" +
            esc(daysApprox) +
            " días a intervalo UI " +
            esc(iv) +
            ")</dd>" +
            (br.start
              ? "<dt>rango sim</dt><dd class=\"mono\">" +
                esc(formatRangeHuman(br.start, br.end)) +
                "</dd>"
              : "") +
            "<dt>strategy</dt><dd class=\"mono\">" +
            esc(data.strategy_id) +
            "</dd>" +
            "<dt>capital final</dt><dd class=\"mono num\">" +
            esc(data.final_equity) +
            "</dd>" +
            "<dt>fees</dt><dd class=\"mono num\">" +
            esc(data.total_fees) +
            "</dd>" +
            "<dt>fills (trades)</dt><dd class=\"mono num\">" +
            esc(data.n_fills) +
            " <span class=\"muted\">← los decide la estrategia, no el # de días</span></dd>" +
            "<dt>veredicto</dt><dd>" +
            esc(data.verdict_es || "—") +
            "</dd>";
          if (Array.isArray(data.fills) && data.fills.length) {
            resultEl.innerHTML +=
              "<dt>detalle</dt><dd>" +
              formatBacktestRun(
                { ok: true, symbol: "SYN", result: data },
                data.strategy_id
              ) +
              "</dd>";
          }
        })
        .catch(function (err) {
          statusErr(runStatus, err);
        });
    });

    const demoStatus = root.querySelector("#gl-demo-status");
    const demoOut = root.querySelector("#gl-demo-out");
    root.querySelector("#gl-demo-submit").addEventListener("click", function () {
      demoStatus.textContent = t("guided_lab.status.sending_demo", "enviando demo…");
      const payload = {
        symbol: root.querySelector("#gl-demo-sym").value,
        side: root.querySelector("#gl-demo-side").value,
        quantity: root.querySelector("#gl-demo-qty").value,
      };
      const priceVal = root.querySelector("#gl-demo-price").value.trim();
      if (priceVal) {
        payload.price = priceVal;
      }
      if (root.querySelector("#gl-demo-mirror").checked) {
        payload.mirror_to_paper = true;
      }
      QLApi.liveDemoSubmit(payload)
        .then(function (data) {
          demoStatus.textContent = data.ok
            ? t("guided_lab.status.demo_ok", "demo ok")
            : t("guided_lab.status.failed", "falló");
          demoStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          demoOut.textContent =
            esc(data.order_id) +
            " " +
            esc(data.status) +
            " @ " +
            esc(data.message) +
            " [" +
            esc(data.transport) +
            "]" +
            (data.mirrored_to_paper ? " · mirrored" : "");
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    root.querySelector("#gl-demo-cancel").addEventListener("click", function () {
      const orderId = root.querySelector("#gl-demo-cancel-id").value.trim();
      if (!orderId) {
        demoStatus.textContent =
          t("guided_lab.status.error", "error") + ": order_id requerido";
        demoStatus.className = "mono status-bad";
        return;
      }
      demoStatus.textContent = t("guided_lab.status.cancelling", "cancelando…");
      QLApi.liveDemoCancel(orderId)
        .then(function (data) {
          demoStatus.textContent = data.ok
            ? t("guided_lab.status.cancel_ok", "cancel ok")
            : t("guided_lab.status.failed", "falló");
          demoStatus.className = data.ok ? "mono status-ok" : "mono status-bad";
          demoOut.textContent =
            esc(data.order_id) +
            " " +
            esc(data.status) +
            " @ " +
            esc(data.message);
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    root.querySelector("#gl-demo-open").addEventListener("click", function () {
      demoStatus.textContent = t("guided_lab.status.querying", "consultando…");
      QLApi.liveDemoOpenOrders()
        .then(function (data) {
          const orders = data.orders || [];
          demoStatus.textContent = "ok (" + orders.length + ")";
          demoStatus.className = "mono status-ok";
          if (!orders.length) {
            demoOut.textContent = "—";
            return;
          }
          demoOut.innerHTML = orders
            .map(function (ord) {
              return (
                esc(ord.order_id || ord.client_order_id || "?") +
                " " +
                esc(ord.symbol || ord.instrument_id || "") +
                " " +
                esc(ord.side || "") +
                " qty=" +
                esc(ord.quantity || ord.orig_qty) +
                (ord.price != null ? " @ " + esc(ord.price) : "") +
                " [" +
                esc(ord.status || "") +
                "]"
              );
            })
            .join("<br>");
        })
        .catch(function (err) {
          statusErr(demoStatus, err);
        });
    });

    function fillStrategySelect(strategies) {
      const sel = root.querySelector("#gl-strategy");
      const hint = root.querySelector("#gl-strategy-hint");
      if (!sel) return;
      const prev = sel.value;
      sel.innerHTML = "";
      const list = (strategies || []).filter(function (s) {
        return s && s.runnable !== false;
      });
      const byFamily = {};
      list.forEach(function (s) {
        const fam = s.family || "other";
        if (!byFamily[fam]) byFamily[fam] = [];
        byFamily[fam].push(s);
      });
      Object.keys(byFamily)
        .sort()
        .forEach(function (fam) {
          const group = document.createElement("optgroup");
          group.label = fam;
          byFamily[fam].forEach(function (s) {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = (s.name || s.id) + " · binance-ready";
            if (s.description) opt.title = s.description;
            group.appendChild(opt);
          });
          sel.appendChild(group);
        });
      if (prev) {
        sel.value = prev;
      }
      if (!sel.value && list.length) {
        sel.value = list[0].id;
      }
      if (hint) {
        hint.textContent =
          list.length +
          " runnable (backtest/paper/Binance demo). Stubs ocultos aquí.";
      }
    }

    root.refresh = function () {
      return QLApi.labStrategies()
        .then(function (res) {
          fillStrategySelect(res.strategies || []);
          return refreshLive();
        })
        .catch(function () {
          fillStrategySelect([
            { id: "momentum", name: "momentum", family: "momentum", runnable: true },
            {
              id: "inventory_mm",
              name: "inventory_mm",
              family: "market_making",
              runnable: true,
            },
          ]);
          return refreshLive();
        });
    };

    applyVenueUi();
    root.refresh();
    QLi18n.applyDom(root);
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createGuidedLabPane = createGuidedLabPane;
})(window);
