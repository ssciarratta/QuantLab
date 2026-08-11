/** Panel Market Data. */
(function (global) {
  "use strict";

  function createMarketPane(getSessionMode) {
    const root = document.createElement("div");
    root.className = "pane-market";

    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Market Data</h3>' +
      '<p class="muted pane-sub">Conexión · instrumentos · snapshot</p></div>' +
      '<div class="pane-toolbar">' +
      '<label class="field">Mercado<select id="md-venue"></select></label>' +
      '<label class="field">MD source<select id="md-source">' +
      '<option value="fake">fake</option>' +
      '<option value="env">env</option>' +
      "</select></label>" +
      "</div>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn" id="md-connect">Conectar</button>' +
      '<button type="button" class="btn secondary" id="md-reconnect">Reconectar</button>' +
      '<button type="button" class="btn secondary" id="md-disconnect">Desconectar</button>' +
      "</div>" +
      '<p class="muted mono" id="md-conn">sin conectar</p>' +
      '<p class="muted mono" id="md-provider">provider: —</p>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Instrumentos</h3>" +
      '<div class="pane-actions">' +
      '<button type="button" class="btn secondary" id="md-instruments">Listar</button>' +
      "</div>" +
      '<div id="md-inst-list" class="mono muted">—</div>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Snapshot</h3>" +
      '<div class="pane-actions">' +
      '<label class="field">Símbolo<input id="md-symbol" type="text" placeholder="ej. GGAL" /></label>' +
      '<button type="button" class="btn" id="md-snap">Consultar</button>' +
      "</div>" +
      '<dl class="kv" id="md-snap-out"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Cuenta</h3>" +
      '<button type="button" class="btn secondary" id="md-account">Ver cuenta</button>' +
      '<dl class="kv" id="md-acct-out" style="margin-top:0.35rem"></dl>' +
      "</div>";

    const venueSel = root.querySelector("#md-venue");
    const sourceSel = root.querySelector("#md-source");
    const connEl = root.querySelector("#md-conn");
    const providerEl = root.querySelector("#md-provider");
    const instList = root.querySelector("#md-inst-list");
    const snapOut = root.querySelector("#md-snap-out");
    const acctOut = root.querySelector("#md-acct-out");

    async function loadVenues() {
      const data = await QLApi.venues();
      venueSel.innerHTML = "";
      (data.venues || []).forEach(function (v) {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        venueSel.appendChild(opt);
      });
      if ((data.venues || []).indexOf("a3") >= 0) {
        venueSel.value = "a3";
      }
    }

    function applyConnectResult(res, prefix) {
      connEl.textContent =
        (prefix || "conectado") +
        " · venue=" +
        res.venue +
        " · mode=" +
        res.mode +
        " · paper=" +
        String(res.paper_broker) +
        " · md_source=" +
        (res.md_source || sourceSel.value);
      providerEl.textContent = "provider: " + (res.md_provider || "—");
      connEl.classList.remove("status-bad");
    }

    root.querySelector("#md-connect").addEventListener("click", async function () {
      try {
        const mode = getSessionMode ? getSessionMode() : "tester";
        const res = await QLApi.connect(venueSel.value, mode, {
          md_source: sourceSel.value,
        });
        applyConnectResult(res, "conectado");
      } catch (err) {
        connEl.textContent = "Error: " + err.message;
        providerEl.textContent = "provider: —";
        connEl.classList.add("status-bad");
      }
    });

    root.querySelector("#md-reconnect").addEventListener("click", async function () {
      try {
        const res = await QLApi.reconnect();
        applyConnectResult(res, "reconectado");
        if (res.md_source && sourceSel) {
          sourceSel.value = res.md_source;
        }
        if (res.venue && venueSel) {
          venueSel.value = res.venue;
        }
      } catch (err) {
        connEl.textContent = "Error reconnect: " + err.message;
        connEl.classList.add("status-bad");
      }
    });

    root.querySelector("#md-disconnect").addEventListener("click", async function () {
      try {
        const res = await QLApi.disconnect();
        connEl.textContent =
          "desconectado" +
          (res.previous_venue ? " · was=" + res.previous_venue : "") +
          (res.has_last_connect ? " · last_connect=ok" : " · last_connect=none");
        providerEl.textContent = "provider: —";
        connEl.classList.remove("status-bad");
      } catch (err) {
        connEl.textContent = "Error disconnect: " + err.message;
        connEl.classList.add("status-bad");
      }
    });

    root.querySelector("#md-instruments").addEventListener("click", async function () {
      try {
        const data = await QLApi.instruments();
        const items = data.instruments || [];
        if (!items.length) {
          instList.textContent = "(vacío)";
          return;
        }
        instList.innerHTML = items
          .map(function (i) {
            var mat = i.maturity || (i.meta && i.meta.maturity) || "";
            var tag = mat ? " · vence " + mat : "";
            var varn =
              (venueSel.value || "") === "a3"
                ? " · [margen + dif. diarias]"
                : "";
            return (
              (i.symbol || "") +
              " · " +
              (i.description || "") +
              tag +
              varn +
              " [" +
              (i.currency || "") +
              "]"
            );
          })
          .join("<br>");
        if ((venueSel.value || "") === "a3" && items.length) {
          window.alert(
            "A3/Matba: para operar estos futuros el margen lo fija la cámara y " +
              "el contrato está sujeto a diferencias diarias hasta el vencimiento. " +
              "No son perpetuos crypto."
          );
        }
        if (items[0] && !root.querySelector("#md-symbol").value) {
          root.querySelector("#md-symbol").value = items[0].symbol;
        }
      } catch (err) {
        instList.textContent = "Error: " + err.message;
      }
    });

    root.querySelector("#md-snap").addEventListener("click", async function () {
      const sym = root.querySelector("#md-symbol").value.trim();
      if (!sym) return;
      try {
        const data = await QLApi.snapshot(sym);
        const s = data.snapshot || {};
        snapOut.innerHTML =
          "<dt>symbol</dt><dd>" +
          (s.symbol || "") +
          "</dd>" +
          "<dt>bid</dt><dd class=\"num\">" +
          (s.bid || "") +
          "</dd>" +
          "<dt>ask</dt><dd class=\"num\">" +
          (s.ask || "") +
          "</dd>" +
          "<dt>last</dt><dd class=\"num\">" +
          (s.last || "") +
          "</dd>" +
          "<dt>ts</dt><dd>" +
          (window.QLFmt && window.QLFmt.fmtDateTime
            ? window.QLFmt.fmtDateTime(s.ts)
            : s.ts || "") +
          "</dd>";
      } catch (err) {
        snapOut.innerHTML = "<dt>error</dt><dd class=\"status-bad\">" + err.message + "</dd>";
      }
    });

    root.querySelector("#md-account").addEventListener("click", async function () {
      try {
        const data = await QLApi.account();
        const a = data.account || {};
        acctOut.innerHTML =
          "<dt>cash</dt><dd>" +
          (a.cash || "") +
          " " +
          (a.currency || "") +
          "</dd>" +
          "<dt>equity</dt><dd>" +
          (a.equity != null ? a.equity : "—") +
          "</dd>";
      } catch (err) {
        acctOut.innerHTML = "<dt>error</dt><dd class=\"status-bad\">" + err.message + "</dd>";
      }
    });

    root.refresh = async function () {
      await loadVenues();
      try {
        const saved = sessionStorage.getItem("ql_active_symbol");
        const input = root.querySelector("#md-symbol");
        if (saved && input && !input.value) input.value = saved;
      } catch (err) {
        /* ignore */
      }
    };

    document.addEventListener("ql:set-symbol", function (ev) {
      const sym = ev.detail && ev.detail.symbol;
      if (!sym) return;
      const input = root.querySelector("#md-symbol");
      if (input) input.value = sym;
    });

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createMarketPane = createMarketPane;
})(window);
