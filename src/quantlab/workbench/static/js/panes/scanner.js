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

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
      '<div class="pane-section">' +
      "<h3>Alpha Scanner</h3>" +
      '<p class="muted" style="margin-top:0">' +
      "Ranking sobre <strong>mercados reales</strong> (klines públicas hacia atrás). " +
      "Elegí <strong>período</strong> (días) o N velas + temporalidad. " +
      "Score ≠ rentabilidad garantizada." +
      "</p>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.4rem;align-items:center">' +
      '<label class="muted">Fuente <select id="sc-source">' +
      '<option value="real" selected>MD real</option>' +
      '<option value="synthetic">Demo sintético WB</option>' +
      "</select></label>" +
      '<label class="muted">Venue <select id="sc-venue">' +
      '<option value="binance" selected>Binance</option>' +
      '<option value="okx">OKX</option>' +
      '<option value="bybit">Bybit</option>' +
      '<option value="hyperliquid">Hyperliquid</option>' +
      "</select></label>" +
      '<label class="muted">Mercado <select id="sc-market">' +
      '<option value="spot" selected>Spot</option>' +
      '<option value="futures">Futuros</option>' +
      "</select></label>" +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.4rem;margin-top:0.4rem;align-items:center">' +
      '<label class="muted">Modo ventana <select id="sc-window-mode">' +
      '<option value="period" selected>Por período (días atrás)</option>' +
      '<option value="klines">Por N velas</option>' +
      "</select></label>" +
      '<label class="muted" id="sc-period-wrap">Período <select id="sc-period">' +
      optHtml(PERIODS, "30") +
      "</select></label>" +
      '<label class="muted">TF / temporalidad <select id="sc-interval">' +
      optHtml(INTERVALS, "1h") +
      "</select></label>" +
      '<label class="field" id="sc-klines-wrap" hidden>velas' +
      '<input id="sc-klines" type="number" value="720" min="10" max="525600" /></label>' +
      '<span class="mono muted" id="sc-nbars">≈ — velas</span>' +
      "</div>" +
      '<div class="pane-row" style="flex-wrap:wrap;gap:0.4rem;margin-top:0.35rem">' +
      '<label class="muted">Perfil <select id="sc-profile">' +
      '<option value="legacy_v1" selected>legacy_v1</option>' +
      '<option value="momentum">momentum</option>' +
      '<option value="mean_reversion">mean_reversion</option>' +
      '<option value="market_making">market_making</option>' +
      '<option value="balanced">balanced</option>' +
      "</select></label>" +
      '<label class="field">top_n<input id="sc-top" type="number" value="5" min="1" max="10" /></label>' +
      '<label class="field">símbolos<input id="sc-limit" type="number" value="15" min="5" max="30" /></label>' +
      '<button type="button" class="btn" id="sc-run">Escanear</button>' +
      '<span class="mono" id="sc-status">—</span>' +
      "</div>" +
      '<p class="muted" id="sc-hint" style="font-size:0.72em;margin:0.35rem 0 0">' +
      "Por período: toma las últimas N velas hasta ahora (ej. 30 días @ 1h ≈ 720). " +
      "Binance spot = top USDT; otros venues = universo curado lab." +
      "</p>" +
      '<div id="sc-out"></div>' +
      '<div id="sc-detail" class="sc-detail" style="margin-top:0.6rem"></div>' +
      "</div>";

    var lastScan = null;
    var selectedIdx = 0;

    function setStatus(ok, msg) {
      var el = root.querySelector("#sc-status");
      el.textContent = msg;
      el.className =
        "mono " + (ok ? "status-ok" : ok === false ? "status-bad" : "muted");
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

    function syncSourceUI() {
      var synth = root.querySelector("#sc-source").value === "synthetic";
      [
        "#sc-venue",
        "#sc-market",
        "#sc-interval",
        "#sc-profile",
        "#sc-limit",
        "#sc-klines",
        "#sc-period",
        "#sc-window-mode",
      ].forEach(function (sel) {
        var el = root.querySelector(sel);
        if (el) el.disabled = synth;
      });
      root.querySelector("#sc-hint").textContent = synth
        ? "Demo local WB:A/B/C (sin red). Para mercados reales elegí «MD real»."
        : "Por período: últimas N velas hasta ahora. Binance spot = top USDT; otros = curado lab.";
    }

    function refreshNBars() {
      var el = root.querySelector("#sc-nbars");
      if (windowMode() === "klines") {
        var n = parseInt(root.querySelector("#sc-klines").value, 10) || 0;
        el.textContent = "≈ " + n.toLocaleString("es-AR") + " velas";
        return;
      }
      if (!QLApi.simPeriod) {
        el.textContent = "≈ —";
        return;
      }
      var days = root.querySelector("#sc-period").value;
      var iv = root.querySelector("#sc-interval").value;
      QLApi.simPeriod(days, iv)
        .then(function (d) {
          el.textContent = d.n_bars_display || "≈ " + d.n_bars + " velas";
          el.title = d.note || "";
        })
        .catch(function () {
          el.textContent = "≈ —";
        });
    }

    function openSim(prefill) {
      if (global.QLShell && typeof QLShell.open === "function") {
        QLShell.open("simulator", { prefill: prefill || {} });
      }
    }

    function renderDetail(idx) {
      var box = root.querySelector("#sc-detail");
      if (!lastScan || !lastScan.scores || !lastScan.scores.length) {
        box.innerHTML = "";
        return;
      }
      selectedIdx = Math.max(0, Math.min(idx, lastScan.scores.length - 1));
      var row = lastScan.scores[selectedIdx];
      var rec = row.recommendation || lastScan.recommendations || {};
      var venue = lastScan.venue || "binance";
      var mt = lastScan.market_type || "spot";
      var und =
        row.underlying ||
        (lastScan.selected_underlyings || [])[selectedIdx] ||
        "";
      var iv = lastScan.interval || "1h";

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

      box.innerHTML =
        '<div class="pane-section" style="border:1px solid var(--border,#333);border-radius:8px;padding:0.55rem 0.7rem">' +
        "<h4 style=\"margin:0 0 0.35rem\">Sugerencias · " +
        esc(und || row.instrument_id) +
        " · " +
        esc(rec.family_label_es || rec.family || "—") +
        "</h4>" +
        '<p class="muted" style="margin:0 0 0.45rem;font-size:0.8em">' +
        esc(rec.text || "") +
        "</p>" +
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

    function renderScores(data) {
      var out = root.querySelector("#sc-out");
      lastScan = data;
      if (!data || !data.scores || !data.scores.length) {
        out.innerHTML = '<p class="muted">Sin scores.</p>';
        root.querySelector("#sc-detail").innerHTML = "";
        return;
      }
      var rowsHtml = data.scores
        .map(function (s, i) {
          var und = s.underlying || s.symbol || s.instrument_id;
          var comp =
            s.composite != null
              ? Number(s.composite).toFixed(3)
              : s.base_score != null
                ? Number(s.base_score).toFixed(3)
                : "—";
          var fam =
            (s.recommendation && s.recommendation.family_label_es) ||
            (s.recommendation && s.recommendation.family) ||
            "—";
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
            '<td class="mono">' +
            esc(comp) +
            "</td>" +
            "<td>" +
            esc(fam) +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      out.innerHTML =
        '<p class="muted" style="font-size:0.75em">' +
        '<span class="data-badge data-badge-real">' +
        esc((data.venue || "lab") + "/" + (data.market_type || "—")) +
        "</span> " +
        "perfil=" +
        esc(data.profile || "") +
        " · elegibles=" +
        esc(data.eligible) +
        " · TF=" +
        esc(data.interval) +
        " · velas=" +
        esc(data.kline_limit) +
        (data.period_days != null ? " · período=" + esc(data.period_days) + "d" : "") +
        "</p>" +
        '<table class="mono" style="width:100%;font-size:0.8em;border-collapse:collapse">' +
        "<thead><tr><th>#</th><th>Moneda</th><th>Score</th><th>Familia</th></tr></thead>" +
        "<tbody>" +
        rowsHtml +
        "</tbody></table>";
      out.querySelectorAll(".sc-row").forEach(function (tr) {
        tr.addEventListener("click", function () {
          out.querySelectorAll(".sc-row").forEach(function (r) {
            r.classList.remove("sc-row-sel");
          });
          tr.classList.add("sc-row-sel");
          renderDetail(parseInt(tr.getAttribute("data-idx"), 10) || 0);
        });
      });
      renderDetail(0);
    }

    root.querySelector("#sc-source").addEventListener("change", syncSourceUI);
    root.querySelector("#sc-window-mode").addEventListener("change", syncWindowModeUI);
    root.querySelector("#sc-period").addEventListener("change", refreshNBars);
    root.querySelector("#sc-interval").addEventListener("change", refreshNBars);
    root.querySelector("#sc-klines").addEventListener("input", refreshNBars);
    root.querySelector("#sc-venue").addEventListener("change", function () {
      if (root.querySelector("#sc-venue").value === "hyperliquid") {
        root.querySelector("#sc-market").value = "futures";
      }
    });
    syncSourceUI();
    syncWindowModeUI();

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
          sel.value = d.default_profile || "legacy_v1";
        })
        .catch(function () {});
    }

    root.querySelector("#sc-run").addEventListener("click", function () {
      var topN = parseInt(root.querySelector("#sc-top").value, 10) || 5;
      setStatus(null, "ejecutando…");
      root.querySelector("#sc-out").textContent = "";
      root.querySelector("#sc-detail").innerHTML = "";
      var promise;
      if (root.querySelector("#sc-source").value === "synthetic") {
        promise = QLApi.labScanner({ top_n: topN }).then(function (d) {
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
        });
      } else {
        var opts = {
          venue: root.querySelector("#sc-venue").value,
          market_type: root.querySelector("#sc-market").value,
          top_n: topN,
          symbol_limit: parseInt(root.querySelector("#sc-limit").value, 10) || 15,
          interval: root.querySelector("#sc-interval").value,
          profile: root.querySelector("#sc-profile").value,
        };
        if (windowMode() === "period") {
          opts.period_days = parseInt(root.querySelector("#sc-period").value, 10) || 30;
        } else {
          opts.kline_limit =
            parseInt(root.querySelector("#sc-klines").value, 10) || 720;
        }
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
          setStatus(false, err.message || String(err));
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
