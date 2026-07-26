/** Panel Posiciones paper (book + MTM). */
(function (global) {
  "use strict";

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
      "</div>";

    const acctEl = root.querySelector("#pos-acct");
    const tableEl = root.querySelector("#pos-table");
    const sessionEl = root.querySelector("#pos-session");

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
            (p.symbol || "") +
            "</td>" +
            '<td class="num">' +
            (p.quantity || "") +
            "</td>" +
            '<td class="num">' +
            (p.avg_price != null ? p.avg_price : "—") +
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
    }

    root.querySelector("#pos-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        tableEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createPositionsPane = createPositionsPane;
})(window);
