/** Panel Posiciones paper (book + MTM) + equity curve (F66). */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sparklineSvg(points) {
    if (!points || points.length < 2) {
      return '<p class="muted mono">sparkline: insuficientes puntos</p>';
    }
    const vals = points.map(function (p) {
      const n = Number(p.equity);
      return Number.isFinite(n) ? n : 0;
    });
    let min = vals[0];
    let max = vals[0];
    for (let i = 1; i < vals.length; i++) {
      if (vals[i] < min) min = vals[i];
      if (vals[i] > max) max = vals[i];
    }
    const pad = 4;
    const w = 280;
    const h = 56;
    const span = max - min || 1;
    const coords = vals.map(function (v, i) {
      const x = pad + (i / (vals.length - 1)) * (w - pad * 2);
      const y = pad + (1 - (v - min) / span) * (h - pad * 2);
      return x.toFixed(1) + "," + y.toFixed(1);
    });
    const poly = coords.join(" ");
    return (
      '<svg class="equity-spark" viewBox="0 0 ' +
      w +
      " " +
      h +
      '" width="100%" height="' +
      h +
      '" role="img" aria-label="Equity sparkline">' +
      '<polyline fill="none" stroke="currentColor" stroke-width="1.5" points="' +
      poly +
      '" />' +
      "</svg>"
    );
  }

  function createPositionsPane() {
    const root = document.createElement("div");
    root.className = "pane-positions";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Cuenta paper</h3>" +
      '<p class="muted" style="margin-top:0">Cash + equity MTM desde PaperBook (sesión durable).</p>' +
      '<dl class="kv" id="pos-acct"></dl>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="pos-refresh">Actualizar</button>' +
      '<span class="mono muted" id="pos-session">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Posiciones</h3>" +
      '<div id="pos-table"></div>' +
      "</div>" +
      '<div class="pane-section" id="pos-equity-section">' +
      "<h3>Equity curve</h3>" +
      '<p class="muted" style="margin-top:0">Snapshots de sesión · GET /api/paper/equity</p>' +
      '<div id="pos-equity-spark" class="equity-spark-wrap"></div>' +
      '<p class="mono muted" id="pos-equity-count">0 puntos</p>' +
      '<div id="pos-equity-list"></div>' +
      "</div>";

    const acctEl = root.querySelector("#pos-acct");
    const tableEl = root.querySelector("#pos-table");
    const sessionEl = root.querySelector("#pos-session");
    const sparkEl = root.querySelector("#pos-equity-spark");
    const countEl = root.querySelector("#pos-equity-count");
    const listEl = root.querySelector("#pos-equity-list");

    function renderAcct(account) {
      if (!account) {
        acctEl.innerHTML = '<dt>estado</dt><dd class="muted">sin datos</dd>';
        return;
      }
      acctEl.innerHTML =
        "<dt>cash</dt><dd class=\"mono num\">" +
        (account.cash || "—") +
        "</dd>" +
        "<dt>equity</dt><dd class=\"mono num\">" +
        (account.equity != null ? account.equity : "—") +
        "</dd>" +
        "<dt>currency</dt><dd class=\"mono\">" +
        (account.currency || "—") +
        "</dd>";
    }

    function renderPositions(positions) {
      if (!positions || !positions.length) {
        tableEl.innerHTML = '<p class="muted mono">sin posiciones</p>';
        return;
      }
      const rows = positions
        .map(function (p) {
          return (
            "<tr>" +
            "<td>" +
            escapeHtml(p.symbol || "") +
            "</td>" +
            '<td class="num">' +
            escapeHtml(p.quantity || "") +
            "</td>" +
            '<td class="num">' +
            escapeHtml(p.avg_price != null ? p.avg_price : "—") +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      tableEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>Symbol</th><th>Qty</th><th>Avg</th>" +
        "</tr></thead><tbody>" +
        rows +
        "</tbody></table>";
    }

    function renderEquity(data) {
      const points = (data && data.points) || [];
      countEl.textContent = points.length + " puntos";
      sparkEl.innerHTML = sparklineSvg(points);
      if (!points.length) {
        listEl.innerHTML = '<p class="muted mono">sin puntos equity</p>';
        return;
      }
      const recent = points.slice(-20).reverse();
      const rows = recent
        .map(function (p) {
          return (
            "<tr>" +
            '<td class="mono">' +
            escapeHtml(p.ts || "") +
            "</td>" +
            '<td class="num mono">' +
            escapeHtml(p.equity) +
            "</td>" +
            '<td class="num mono">' +
            escapeHtml(p.cash) +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      listEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>ts</th><th>equity</th><th>cash</th>" +
        "</tr></thead><tbody>" +
        rows +
        "</tbody></table>";
    }

    async function refresh() {
      const bookData = await QLApi.paperBook();
      sessionEl.textContent = "session " + (bookData.session_id || "?");
      renderAcct(bookData.account);
      let positions = [];
      try {
        const posData = await QLApi.positions();
        positions = posData.positions || [];
      } catch (err) {
        const book = bookData.book || {};
        const raw = book.positions || {};
        positions = Object.keys(raw).map(function (sym) {
          return {
            symbol: sym,
            quantity: raw[sym].quantity,
            avg_price: raw[sym].avg_price,
          };
        });
      }
      renderPositions(positions);
      try {
        const eq = await QLApi.paperEquity(200);
        renderEquity(eq);
      } catch (err) {
        sparkEl.innerHTML = "";
        countEl.textContent = "equity —";
        listEl.innerHTML =
          '<p class="status-bad mono">' + escapeHtml(err.message || err) + "</p>";
      }
    }

    root.querySelector("#pos-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        tableEl.innerHTML = '<p class="status-bad mono">' + escapeHtml(err.message) + "</p>";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createPositionsPane = createPositionsPane;
})(window);
