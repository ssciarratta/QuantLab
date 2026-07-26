/** Panel Settings — preferencias de sesión (F36) + export/import ZIP (F39). */
(function (global) {
  "use strict";

  function createSettingsPane(onSaved) {
    const root = document.createElement("div");
    root.className = "pane-settings";

    root.innerHTML =
      '<div class="pane-section">' +
      "<h3>Preferencias</h3>" +
      '<p class="muted" style="margin-top:0">Persistidas en session/settings.json · locale es · sin LIVE.</p>' +
      '<label class="field">Tema<select id="set-theme">' +
      '<option value="slate">slate</option>' +
      '<option value="high-contrast">high-contrast</option>' +
      "</select></label>" +
      '<label class="field">Venue por defecto<input id="set-venue" type="text" placeholder="paper" /></label>' +
      '<label class="field">Estrategia por defecto<select id="set-strategy"></select></label>' +
      '<label class="field">Slippage (bps)<input id="set-slip" type="text" inputmode="decimal" placeholder="0" /></label>' +
      '<label class="field">Locale<input id="set-locale" type="text" value="es" readonly /></label>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="set-save">Guardar</button>' +
      '<button type="button" class="btn secondary" id="set-refresh">Recargar</button>' +
      '<span class="mono muted" id="set-status">—</span>' +
      "</div>" +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Sesión</h3>" +
      '<dl class="kv" id="set-meta"></dl>' +
      "</div>" +
      '<div class="pane-section">' +
      "<h3>Export / Import ZIP</h3>" +
      '<p class="muted" style="margin-top:0">Research-safe · sin secretos · zip-slip fail-closed · LIVE bloqueado.</p>' +
      '<div class="pane-row">' +
      '<button type="button" class="btn" id="set-export">Exportar sesión</button>' +
      '<button type="button" class="btn secondary" id="set-export-dl">Descargar ZIP</button>' +
      "</div>" +
      '<div class="pane-row" style="margin-top:0.5rem">' +
      '<label class="field" style="flex:1">Importar ZIP' +
      '<input id="set-import-file" type="file" accept=".zip,application/zip" />' +
      "</label>" +
      "</div>" +
      '<div class="pane-row">' +
      '<label class="field">Modo<select id="set-import-mode">' +
      '<option value="new">nueva sesión</option>' +
      '<option value="merge">merge (fail-closed)</option>' +
      "</select></label>" +
      '<button type="button" class="btn" id="set-import">Importar</button>' +
      "</div>" +
      '<p class="mono muted" id="set-zip-status">—</p>' +
      "</div>";

    const themeEl = root.querySelector("#set-theme");
    const venueEl = root.querySelector("#set-venue");
    const strategyEl = root.querySelector("#set-strategy");
    const slipEl = root.querySelector("#set-slip");
    const localeEl = root.querySelector("#set-locale");
    const statusEl = root.querySelector("#set-status");
    const metaEl = root.querySelector("#set-meta");
    const zipStatusEl = root.querySelector("#set-zip-status");
    const importFileEl = root.querySelector("#set-import-file");
    const importModeEl = root.querySelector("#set-import-mode");

    function esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function fillStrategies(list, selected) {
      strategyEl.innerHTML = "";
      const ids = (list || []).map(function (s) {
        return typeof s === "string" ? s : s.id;
      });
      if (!ids.length) {
        ["dummy", "buy_once", "momentum", "inventory_mm", "avellaneda_stoikov"].forEach(
          function (id) {
            ids.push(id);
          }
        );
      }
      ids.forEach(function (id) {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = id;
        if (id === selected) opt.selected = true;
        strategyEl.appendChild(opt);
      });
    }

    function applyTheme(theme) {
      /* F48: mirror shell — documentElement + body on load/PUT */
      const t = theme === "high-contrast" ? "high-contrast" : "slate";
      document.documentElement.setAttribute("data-theme", t);
      if (document.body) document.body.setAttribute("data-theme", t);
    }

    function render(data) {
      const s = (data && data.settings) || {};
      themeEl.value = s.theme === "high-contrast" ? "high-contrast" : "slate";
      venueEl.value = s.default_venue || "paper";
      slipEl.value = s.slippage_bps != null ? String(s.slippage_bps) : "0";
      localeEl.value = s.locale || "es";
      fillStrategies(
        (data.strategy_ids || []).length
          ? data.strategy_ids
          : null,
        s.default_strategy || "momentum"
      );
      applyTheme(s.theme);
      metaEl.innerHTML =
        "<dt>session_id</dt><dd class=\"mono\">" +
        esc(data.session_id) +
        "</dd>" +
        "<dt>mode</dt><dd class=\"mono\">" +
        esc(data.mode) +
        "</dd>" +
        "<dt>venue</dt><dd class=\"mono\">" +
        esc(data.venue || "—") +
        "</dd>" +
        "<dt>md_provider</dt><dd class=\"mono\">" +
        esc(data.md_provider || "—") +
        "</dd>" +
        "<dt>LIVE_BLOCKED</dt><dd class=\"mono\">" +
        esc(String(data.live_blocked)) +
        "</dd>";
      statusEl.textContent = "ok";
      statusEl.className = "mono muted status-ok";
      if (typeof onSaved === "function") onSaved(data);
    }

    async function refresh() {
      const [settings, strategies] = await Promise.all([
        QLApi.getSettings(),
        QLApi.labStrategies().catch(function () {
          return null;
        }),
      ]);
      if (strategies && Array.isArray(strategies.strategies)) {
        settings.strategy_ids = strategies.strategies.map(function (s) {
          return s.id || s;
        });
      }
      render(settings);
    }

    async function save() {
      const body = {
        theme: themeEl.value,
        default_venue: venueEl.value.trim(),
        default_strategy: strategyEl.value,
        slippage_bps: slipEl.value.trim() || "0",
        locale: "es",
      };
      const data = await QLApi.putSettings(body);
      render(data);
      statusEl.textContent = "guardado";
    }

    function fileToBase64(file) {
      return new Promise(function (resolve, reject) {
        const reader = new FileReader();
        reader.onload = function () {
          const result = String(reader.result || "");
          const idx = result.indexOf(",");
          resolve(idx >= 0 ? result.slice(idx + 1) : result);
        };
        reader.onerror = function () {
          reject(new Error("no se pudo leer el ZIP"));
        };
        reader.readAsDataURL(file);
      });
    }

    async function doExport() {
      const data = await QLApi.sessionExport();
      zipStatusEl.textContent =
        "export ok · " +
        (data.filename || "") +
        " · " +
        (data.files_count || 0) +
        " files · " +
        (data.path || "");
      zipStatusEl.className = "mono muted status-ok";
    }

    function doDownload() {
      const a = document.createElement("a");
      a.href = QLApi.sessionExportDownloadUrl();
      a.download = "quantlab-session.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      zipStatusEl.textContent = "descarga iniciada";
      zipStatusEl.className = "mono muted status-ok";
    }

    async function doImport() {
      const file = importFileEl.files && importFileEl.files[0];
      if (!file) {
        throw new Error("seleccioná un archivo .zip");
      }
      zipStatusEl.textContent = "importando…";
      const b64 = await fileToBase64(file);
      const data = await QLApi.sessionImport({
        mode: importModeEl.value === "merge" ? "merge" : "new",
        zip_base64: b64,
      });
      zipStatusEl.textContent =
        "import " +
        data.mode +
        " ok · session_id=" +
        data.session_id +
        " · written=" +
        data.files_written;
      zipStatusEl.className = "mono muted status-ok";
      importFileEl.value = "";
    }

    root.querySelector("#set-refresh").addEventListener("click", function () {
      refresh().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });
    root.querySelector("#set-save").addEventListener("click", function () {
      save().catch(function (err) {
        statusEl.textContent = err.message;
        statusEl.className = "mono status-bad";
      });
    });
    root.querySelector("#set-export").addEventListener("click", function () {
      doExport().catch(function (err) {
        zipStatusEl.textContent = err.message;
        zipStatusEl.className = "mono status-bad";
      });
    });
    root.querySelector("#set-export-dl").addEventListener("click", function () {
      try {
        doDownload();
      } catch (err) {
        zipStatusEl.textContent = err.message || String(err);
        zipStatusEl.className = "mono status-bad";
      }
    });
    root.querySelector("#set-import").addEventListener("click", function () {
      doImport().catch(function (err) {
        zipStatusEl.textContent = err.message;
        zipStatusEl.className = "mono status-bad";
      });
    });

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSettingsPane = createSettingsPane;
})(window);
