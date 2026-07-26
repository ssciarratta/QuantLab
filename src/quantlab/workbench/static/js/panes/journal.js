/** Panel Journal — fills paper + export CSV (client-side). */
(function (global) {
  "use strict";

  const CSV_COLS = [
    "ts",
    "fill_id",
    "order_id",
    "symbol",
    "side",
    "quantity",
    "price",
    "source",
  ];

  function csvEscape(value) {
    const s = value == null ? "" : String(value);
    if (/[",\n\r]/.test(s)) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }

  function fillsToCsv(fills) {
    const lines = [CSV_COLS.join(",")];
    fills.forEach(function (f) {
      lines.push(
        CSV_COLS.map(function (k) {
          return csvEscape(f[k]);
        }).join(",")
      );
    });
    return lines.join("\n") + "\n";
  }

  function downloadCsv(filename, text) {
    const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 500);
  }

  function createJournalPane() {
    const root = document.createElement("div");
    root.className = "pane-journal";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Journal de fills</h3>" +
      '<p class="muted" style="margin-top:0">Fuente: GET /api/paper/fills (sesión durable). Export CSV local — sin servidor.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="jn-refresh">Actualizar</button>' +
      '<button type="button" class="btn" id="jn-export">Export CSV</button>' +
      '<span class="mono muted" id="jn-count">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="jn-table"></div>' +
      "</div>";

    const tableEl = root.querySelector("#jn-table");
    const countEl = root.querySelector("#jn-count");
    let lastFills = [];

    function renderFills(fills) {
      lastFills = fills || [];
      countEl.textContent = lastFills.length + " fills";
      if (!lastFills.length) {
        tableEl.innerHTML = '<p class="muted mono">sin fills</p>';
        return;
      }
      const rows = lastFills
        .map(function (f) {
          return (
            "<tr>" +
            "<td>" +
            (f.ts || "").slice(0, 19).replace("T", " ") +
            "</td>" +
            "<td>" +
            (f.symbol || "") +
            "</td>" +
            "<td>" +
            (f.side || "") +
            "</td>" +
            '<td class="num">' +
            (f.quantity || "") +
            "</td>" +
            '<td class="num">' +
            (f.price || "") +
            "</td>" +
            '<td class="muted">' +
            (f.fill_id || "") +
            "</td>" +
            '<td class="muted">' +
            (f.order_id || "") +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      tableEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>Ts</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Px</th><th>Fill</th><th>Order</th>" +
        "</tr></thead><tbody>" +
        rows +
        "</tbody></table>";
    }

    async function refresh() {
      const data = await QLApi.paperFills();
      renderFills(data.fills || []);
    }

    root.querySelector("#jn-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        tableEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
      });
    });

    root.querySelector("#jn-export").addEventListener("click", function () {
      if (!lastFills.length) {
        countEl.textContent = "0 fills · nada que exportar";
        return;
      }
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
      downloadCsv("quantlab-fills-" + stamp + ".csv", fillsToCsv(lastFills));
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createJournalPane = createJournalPane;
})(window);
