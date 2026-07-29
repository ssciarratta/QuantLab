/** Panel Optimizer — grid + historial + Pareto (F33). */
(function (global) {
  "use strict";

  function createOptimizePane() {
    const root = document.createElement("div");
    root.className = "pane-lab pane-optimize";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head">' +
      "<h3>Optimizer</h3>" +
      '<p class="muted pane-sub">Grid + Pareto · session/optimizer</p>' +
      "</div>" +
      '<div class="pane-toolbar">' +
      '<label>lookbacks <input type="text" id="op-lb" class="mono" value="2,3"></label>' +
      '<label>qty <input type="text" id="op-qty" class="mono" value="1"></label>' +
      '<label>n_bars <input type="number" id="op-bars" class="mono" min="8" max="60" value="20"></label>' +
      "</div>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn" id="op-run">Optimizar</button>' +
      '<button type="button" class="btn secondary" id="op-refresh">Actualizar</button>' +
      '<span class="mono" id="op-status">—</span>' +
      "</div>" +
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
      "<h3>Raw</h3>" +
      '<div id="op-out"></div>' +
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

    function esc(s) {
      return QLLabUI.escapeHtml(s);
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
      meta.textContent =
        (data.method || "grid") +
        " · n_bars=" +
        (data.n_bars != null ? data.n_bars : "?") +
        (data.run_id ? " · " + data.run_id : "") +
        (data.persisted ? " · persisted" : " · preview") +
        (data.path ? " · " + data.path : "");

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
            "</tbody></table>" +
            '<pre class="mono" style="margin-top:0.5rem;white-space:pre-wrap;font-size:0.75rem">' +
            esc(JSON.stringify(pareto, null, 2)) +
            "</pre>";
        }
      }

      out.innerHTML = QLLabUI.preJson(data);
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
      renderResult(source);
      renderRuns(data);
      if (!status.textContent || status.textContent === "—") {
        QLLabUI.setStatus(status, true, "list " + (data.count || 0));
      }
    }

    root.querySelector("#op-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        QLLabUI.setStatus(status, false, err.message);
      });
    });

    QLLabUI.bindRun(root, "#op-run", "#op-status", "#op-out", function () {
      const lookbacks = parseCsvInts(root.querySelector("#op-lb").value);
      const quantities = parseCsvStrs(root.querySelector("#op-qty").value);
      const nBars = parseInt(root.querySelector("#op-bars").value, 10) || 20;
      return QLApi.labOptimize({
        lookbacks: lookbacks.length ? lookbacks : [2, 3],
        quantities: quantities.length ? quantities : ["1"],
        n_bars: nBars,
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
  global.QLPanes.createOptimizePane = createOptimizePane;
})(window);
