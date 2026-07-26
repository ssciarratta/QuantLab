/** Panel Universe — broker symbols + watchlist (F30) + import/export JSON (F79). */
(function (global) {
  "use strict";

  function setActiveSymbol(symbol) {
    const sym = String(symbol || "").trim().toUpperCase();
    if (!sym) return;
    try {
      sessionStorage.setItem("ql_active_symbol", sym);
    } catch (err) {
      /* ignore */
    }
    document.dispatchEvent(
      new CustomEvent("ql:set-symbol", { detail: { symbol: sym } })
    );
    const md = document.querySelector("#md-symbol");
    if (md) md.value = sym;
    const ps = document.querySelector("#ps-symbol");
    if (ps) ps.value = sym;
  }

  function createUniversePane() {
    const root = document.createElement("div");
    root.className = "pane-universe";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Universe / Watchlist</h3>" +
      '<p class="muted" style="margin-top:0">Símbolos del broker + watchlist de sesión. Click → set symbol en Market / Sesión Paper.</p>' +
      '<div class="pane-row">' +
      '<label class="field">Añadir<input id="un-add" type="text" placeholder="ej. GGAL" /></label>' +
      '<button type="button" class="btn" id="un-add-btn">Add</button>' +
      '<button type="button" class="btn secondary" id="un-refresh">Actualizar</button>' +
      "</div>" +
      '<div class="pane-row">' +
      '<button type="button" class="btn secondary" id="un-export">Export JSON</button>' +
      '<input id="un-import-file" type="file" accept=".json,application/json" />' +
      '<label class="field">Modo<select id="un-import-mode">' +
      '<option value="merge" selected>merge</option>' +
      '<option value="replace">replace</option>' +
      "</select></label>" +
      '<button type="button" class="btn secondary" id="un-import">Import JSON</button>' +
      "</div>" +
      '<p class="muted mono" id="un-status">—</p>' +
      "</div>" +
      '<div class="pane-section">' +
      '<div id="un-list"></div>' +
      "</div>";

    const listEl = root.querySelector("#un-list");
    const statusEl = root.querySelector("#un-status");
    const addInput = root.querySelector("#un-add");
    const importFileEl = root.querySelector("#un-import-file");
    const importModeEl = root.querySelector("#un-import-mode");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function render(data) {
      const rows = data.symbols || [];
      const msg = data.broker_message || "";
      statusEl.textContent =
        rows.length +
        " símbolos · watchlist=" +
        (data.watchlist || []).length +
        (data.broker_connected ? " · broker ok" : " · " + msg);

      if (!rows.length) {
        listEl.innerHTML =
          '<p class="muted mono">sin símbolos — conectá broker o añadí a watchlist</p>';
        return;
      }

      listEl.innerHTML = rows
        .map(function (row) {
          const sym = row.symbol || "";
          const src = row.source || "";
          const wl = row.in_watchlist ? "★" : "☆";
          const desc = row.description ? " · " + row.description : "";
          return (
            '<div class="universe-row" data-symbol="' +
            esc(sym) +
            '">' +
            '<button type="button" class="btn secondary universe-sym" data-symbol="' +
            esc(sym) +
            '">' +
            esc(sym) +
            "</button>" +
            '<span class="mono muted">' +
            esc(src) +
            desc +
            "</span>" +
            '<button type="button" class="btn secondary universe-wl" data-symbol="' +
            esc(sym) +
            '" data-in="' +
            (row.in_watchlist ? "1" : "0") +
            '" title="toggle watchlist">' +
            wl +
            "</button>" +
            "</div>"
          );
        })
        .join("");

      listEl.querySelectorAll(".universe-sym").forEach(function (btn) {
        btn.addEventListener("click", function () {
          setActiveSymbol(btn.getAttribute("data-symbol"));
          statusEl.textContent = "symbol → " + btn.getAttribute("data-symbol");
        });
      });

      listEl.querySelectorAll(".universe-wl").forEach(function (btn) {
        btn.addEventListener("click", async function () {
          const sym = btn.getAttribute("data-symbol");
          const inWl = btn.getAttribute("data-in") === "1";
          try {
            if (inWl) {
              await QLApi.putWatchlist({ remove: [sym] });
            } else {
              await QLApi.putWatchlist({ add: [sym] });
            }
            await root.refresh();
          } catch (err) {
            statusEl.textContent = "Error: " + err.message;
            statusEl.classList.add("status-bad");
          }
        });
      });
    }

    root.querySelector("#un-add-btn").addEventListener("click", async function () {
      const sym = addInput.value.trim();
      if (!sym) return;
      try {
        await QLApi.putWatchlist({ add: [sym] });
        addInput.value = "";
        setActiveSymbol(sym);
        await root.refresh();
      } catch (err) {
        statusEl.textContent = "Error: " + err.message;
        statusEl.classList.add("status-bad");
      }
    });

    root.querySelector("#un-refresh").addEventListener("click", function () {
      root.refresh().catch(function () {});
    });

    root.querySelector("#un-export").addEventListener("click", function () {
      statusEl.classList.remove("status-bad");
      const a = document.createElement("a");
      a.href = QLApi.watchlistExportUrl();
      a.download = "quantlab-watchlist.json";
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      a.remove();
      statusEl.textContent = "export JSON…";
    });

    root.querySelector("#un-import").addEventListener("click", async function () {
      const file = importFileEl.files && importFileEl.files[0];
      if (!file) {
        statusEl.textContent = "seleccioná un JSON para importar";
        statusEl.classList.add("status-bad");
        return;
      }
      statusEl.classList.remove("status-bad");
      statusEl.textContent = "importando…";
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const symbols = Array.isArray(parsed)
          ? parsed
          : parsed && Array.isArray(parsed.symbols)
            ? parsed.symbols
            : null;
        if (!symbols) {
          throw new Error("JSON debe ser {symbols:[...]} o una lista");
        }
        const mode = importModeEl.value === "replace" ? "replace" : "merge";
        const out = await QLApi.importWatchlist({ symbols: symbols, mode: mode });
        importFileEl.value = "";
        statusEl.textContent =
          "import " +
          mode +
          " · " +
          (out.before_count || 0) +
          " → " +
          (out.after_count || 0) +
          " símbolos";
        await root.refresh();
      } catch (err) {
        statusEl.textContent = "Error: " + err.message;
        statusEl.classList.add("status-bad");
      }
    });

    root.refresh = async function () {
      statusEl.classList.remove("status-bad");
      try {
        const data = await QLApi.universe();
        render(data);
      } catch (err) {
        statusEl.textContent = "Error: " + err.message;
        statusEl.classList.add("status-bad");
        listEl.innerHTML = "";
      }
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createUniversePane = createUniversePane;
  global.QLPanes.setActiveSymbol = setActiveSymbol;
})(window);
