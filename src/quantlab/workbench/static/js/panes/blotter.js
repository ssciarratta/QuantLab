/** Panel Paper Blotter. */
(function (global) {
  "use strict";

  function createBlotterPane() {
    const root = document.createElement("div");
    root.className = "pane-blotter";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Enviar orden paper</h3>" +
      '<p class="muted" style="margin-top:0">Solo paths TESTER/PAPER vía PaperBroker — nunca place_order live.</p>' +
      '<div class="pane-row">' +
      '<label class="field">Símbolo<input id="bl-symbol" type="text" /></label>' +
      '<label class="field">Lado<select id="bl-side">' +
      '<option value="buy">BUY</option>' +
      '<option value="sell">SELL</option>' +
      "</select></label>" +
      '<label class="field">Qty<input id="bl-qty" type="text" value="1" /></label>' +
      "</div>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="bl-submit">Submit paper</button>' +
      '<span class="mono" id="bl-ack">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Fills</h3>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="bl-refresh">Actualizar fills</button>' +
      "</div>" +
      '<div id="bl-fills"></div>' +
      "</div>";

    const ackEl = root.querySelector("#bl-ack");
    const fillsEl = root.querySelector("#bl-fills");

    async function refreshFills() {
      const data = await QLApi.paperFills();
      const fills = data.fills || [];
      if (!fills.length) {
        fillsEl.innerHTML = '<p class="muted mono">sin fills</p>';
        return;
      }
      const rows = fills
        .map(function (f) {
          return (
            "<tr>" +
            "<td>" +
            (f.ts || "").slice(11, 19) +
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
            "<td class=\"muted\">" +
            (f.fill_id || "") +
            "</td>" +
            "</tr>"
          );
        })
        .join("");
      fillsEl.innerHTML =
        '<table class="data-table"><thead><tr>' +
        "<th>Hora</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Px</th><th>Fill</th>" +
        "</tr></thead><tbody>" +
        rows +
        "</tbody></table>";
    }

    root.querySelector("#bl-submit").addEventListener("click", async function () {
      const symbol = root.querySelector("#bl-symbol").value.trim();
      const side = root.querySelector("#bl-side").value;
      const qty = root.querySelector("#bl-qty").value.trim();
      if (!symbol || !qty) {
        ackEl.textContent = "símbolo y qty requeridos";
        ackEl.className = "mono status-bad";
        return;
      }
      try {
        const res = await QLApi.paperSubmit({
          intent_type: "place_order",
          instrument_id: symbol,
          side: side,
          quantity: qty,
          order_type: "market",
        });
        const ack = res.ack || {};
        ackEl.textContent =
          (ack.status || "?") + " · " + (ack.order_id || "") + " · " + (ack.message || "");
        ackEl.className = "mono status-ok";
        await refreshFills();
      } catch (err) {
        ackEl.textContent = "Error: " + err.message;
        ackEl.className = "mono status-bad";
      }
    });

    root.querySelector("#bl-refresh").addEventListener("click", function () {
      refreshFills().catch(function (err) {
        fillsEl.innerHTML = '<p class="status-bad mono">' + err.message + "</p>";
      });
    });

    root.refresh = async function () {
      await refreshFills();
    };

    root.setDefaultSymbol = function (sym) {
      const input = root.querySelector("#bl-symbol");
      if (input && !input.value) input.value = sym;
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createBlotterPane = createBlotterPane;
})(window);
