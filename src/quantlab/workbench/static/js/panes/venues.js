/** Panel Venues / Broker Registry — read-only (F93). */
(function (global) {
  "use strict";

  function createVenuesPane() {
    const root = document.createElement("div");
    root.className = "pane-venues";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Registro de brokers</h3>" +
      '<p class="muted" style="margin-top:0">Solo lectura. Los plugins externos operan siempre detrás de ReadOnlyBrokerPort; ejecución LIVE bloqueada.</p>' +
      '<div class="pane-row">' +
      '<span class="mono" id="venues-badge">—</span>' +
      '<button type="button" class="btn secondary" id="venues-refresh">Actualizar</button>' +
      "</div>" +
      '<dl class="kv" id="venues-conn"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Mercados</h3>" +
      '<div class="mono" id="venues-list">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Contrato de plugins v1</h3>" +
      '<dl class="kv" id="venues-contract"></dl>' +
      "</div>";

    const badgeEl = root.querySelector("#venues-badge");
    const connEl = root.querySelector("#venues-conn");
    const listEl = root.querySelector("#venues-list");
    const contractEl = root.querySelector("#venues-contract");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function render(data) {
      const venues = Array.isArray(data.venues) ? data.venues : [];
      const plugins = Array.isArray(data.plugin_venues) ? data.plugin_venues : [];
      badgeEl.textContent =
        venues.length + " mercados · " + plugins.length + " plugin(s)";
      badgeEl.className = "mono status-ok";

      connEl.innerHTML =
        "<dt>connected_venue</dt><dd class=\"mono\">" +
        esc(data.connected_venue == null ? "(desconectado)" : data.connected_venue) +
        "</dd>" +
        "<dt>md_provider</dt><dd class=\"mono\">" +
        esc(data.md_provider == null ? "(n/a)" : data.md_provider) +
        "</dd>" +
        "<dt>mode</dt><dd class=\"mono\">" +
        esc(data.mode) +
        "</dd>" +
        "<dt>live_blocked</dt><dd class=\"mono\">" +
        esc(data.live_blocked) +
        "</dd>";

      if (!venues.length) {
        listEl.textContent = "(sin mercados registrados)";
        listEl.className = "mono muted";
      } else {
        listEl.className = "mono";
        listEl.innerHTML = venues
          .map(function (v) {
            const isPlugin = plugins.indexOf(v) !== -1;
            const isConnected = data.connected_venue === v;
            let tags = isPlugin ? " [plugin · read-only]" : " [builtin]";
            if (isConnected) tags += " [conectado]";
            return esc(v) + '<span class="muted">' + esc(tags) + "</span>";
          })
          .join("<br>");
      }

      const contract = data.plugin_contract || {};
      const caps = Array.isArray(contract.allowed_capabilities)
        ? contract.allowed_capabilities.join(", ")
        : "—";
      contractEl.innerHTML =
        "<dt>api_version</dt><dd class=\"mono\">" +
        esc(contract.api_version) +
        "</dd>" +
        "<dt>capabilities</dt><dd class=\"mono\">" +
        esc(caps) +
        "</dd>" +
        "<dt>wrapper</dt><dd class=\"mono\">" +
        esc(contract.read_only_wrapper) +
        "</dd>" +
        "<dt>execution</dt><dd class=\"mono\">" +
        esc(contract.execution) +
        "</dd>";
    }

    async function refresh() {
      try {
        const data = await QLApi.venues();
        render(data);
      } catch (err) {
        badgeEl.textContent = "error: " + err.message;
        badgeEl.className = "mono status-bad";
      }
    }

    root.querySelector("#venues-refresh").addEventListener("click", function () {
      refresh();
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createVenuesPane = createVenuesPane;
})(window);
