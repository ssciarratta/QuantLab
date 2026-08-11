/** Operación activa — monitoreo unificado (blotter + posiciones + estado corrida). */
(function (global) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fmtNum(v) {
    if (v == null || v === "") return "—";
    var n = Number(v);
    return isFinite(n) ? n.toLocaleString("es-AR", { maximumFractionDigits: 6 }) : String(v);
  }

  function fmtDt(iso) {
    if (global.QLFmt && global.QLFmt.fmtDateTime) return global.QLFmt.fmtDateTime(iso);
    return iso == null || iso === "" ? "—" : String(iso);
  }

  function createMonitorPane(opts) {
    opts = opts || {};
    var onOpen = typeof opts.onOpen === "function" ? opts.onOpen : function () {};

    var root = document.createElement("div");
    root.className = "pane-monitor";
    root.innerHTML =
      '<div class="mon-status" id="mon-status">' +
      '<span class="ql-status-chip" id="mon-phase">Sin corrida activa</span>' +
      '<span class="mono muted" id="mon-steps">—</span>' +
      "</div>" +
      '<div class="mon-grid">' +
      '<section class="mon-section"><h4>Órdenes recientes</h4><div id="mon-orders" class="mono">—</div></section>' +
      '<section class="mon-section"><h4>Posiciones</h4><div id="mon-pos" class="mono">—</div></section>' +
      '<section class="mon-section"><h4>Resultado paper</h4><div id="mon-pnl" class="mono">—</div></section>' +
      "</div>" +
      '<div class="mon-actions">' +
      '<button type="button" class="btn secondary" data-open="strategy_live_test">Corrida en vivo</button>' +
      '<button type="button" class="btn secondary" data-open="blotter">Blotter completo</button>' +
      '<button type="button" class="btn secondary" data-open="journal">Journal</button>' +
      '<button type="button" class="btn secondary" data-open="positions">Posiciones</button>' +
      '<button type="button" class="btn secondary" data-open="risk">Riesgo</button>' +
      "</div>";

    root.querySelectorAll("[data-open]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        onOpen(btn.getAttribute("data-open"));
      });
    });

    async function refresh() {
      var phaseEl = root.querySelector("#mon-phase");
      var stepsEl = root.querySelector("#mon-steps");
      var ordersEl = root.querySelector("#mon-orders");
      var posEl = root.querySelector("#mon-pos");
      var pnlEl = root.querySelector("#mon-pnl");

      try {
        if (QLApi.executionLive) {
          var live = await QLApi.executionLive();
          var data = live && live.live ? live.live : live;
          if (data && data.live_summary) {
            var s = data.live_summary;
            var running = !!s.paper_running;
            if (phaseEl) {
              phaseEl.textContent = running
                ? "● Ejecutando — " + (s.strategy_name || s.strategy_id || "")
                : s.phase === "RUNNING"
                  ? "● Registrada"
                  : "● " + (s.phase || "Idle");
              phaseEl.className =
                "ql-status-chip ql-status-chip--" + (running ? "ok" : "idle");
            }
            if (stepsEl) {
              stepsEl.textContent =
                (s.symbol_resolved || s.symbol || "—") +
                " · paso " +
                (s.steps || 0) +
                "/" +
                (s.max_steps || "?");
            }
          }
          if (data && data.fills && ordersEl) {
            var fills = data.fills.slice().reverse().slice(0, 8);
            if (!fills.length) {
              ordersEl.innerHTML = '<span class="muted">Sin operaciones aún</span>';
            } else {
              ordersEl.innerHTML = fills
                .map(function (f) {
                  var buy = String(f.side || "").toUpperCase() === "BUY";
                  return (
                    '<div class="' +
                    (buy ? "slt-order-buy" : "slt-order-sell") +
                    '">' +
                    (buy ? "Compra" : "Venta") +
                    " " +
                    fmtNum(f.quantity || f.qty) +
                    " @ " +
                    fmtNum(f.price) +
                    " · " +
                    esc(fmtDt(f.ts || f.timestamp)) +
                    "</div>"
                  );
                })
                .join("");
            }
          }
          if (data && data.positions && posEl) {
            var pos = data.positions || [];
            posEl.innerHTML = pos.length
              ? pos
                  .map(function (p) {
                    return (
                      esc(p.symbol || p.instrument_id) +
                      ": " +
                      fmtNum(p.quantity || p.qty) +
                      " · uPnL " +
                      fmtNum(p.unrealized_pnl)
                    );
                  })
                  .join("<br>")
              : '<span class="muted">Sin posiciones abiertas</span>';
          }
          if (data && data.pnl && pnlEl) {
            var p = data.pnl;
            pnlEl.innerHTML =
              "Equity " +
              fmtNum(p.equity) +
              " · Cash " +
              fmtNum(p.cash) +
              " · PnL " +
              fmtNum(p.total_pnl != null ? p.total_pnl : p.unrealized);
          }
          return;
        }
      } catch (e) {}

      try {
        var paper = await QLApi.paperSessionStatus();
        if (phaseEl) {
          phaseEl.textContent = paper.running ? "● Paper activo" : "● Sin motor paper";
        }
        if (stepsEl && paper.steps != null) {
          stepsEl.textContent = "steps " + paper.steps + "/" + (paper.max_steps || "?");
        }
        var fillsData = await QLApi.paperFills();
        if (ordersEl && fillsData && fillsData.fills) {
          var fl = (fillsData.fills || []).slice(-8).reverse();
          ordersEl.innerHTML = fl.length
            ? fl
                .map(function (f) {
                  return (
                    esc(f.side) +
                    " " +
                    fmtNum(f.quantity) +
                    " @ " +
                    fmtNum(f.price)
                  );
                })
                .join("<br>")
            : '<span class="muted">Sin fills</span>';
        }
      } catch (e2) {
        if (ordersEl) ordersEl.textContent = "Error al cargar: " + (e2.message || e2);
      }
    }

    root.refresh = refresh;
    refresh().catch(function () {});
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMonitorPane = createMonitorPane;
})(typeof window !== "undefined" ? window : globalThis);
