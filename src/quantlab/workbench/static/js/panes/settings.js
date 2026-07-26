/** Panel Settings — preferencias de sesión (F36). */
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
      "</div>";

    const themeEl = root.querySelector("#set-theme");
    const venueEl = root.querySelector("#set-venue");
    const strategyEl = root.querySelector("#set-strategy");
    const slipEl = root.querySelector("#set-slip");
    const localeEl = root.querySelector("#set-locale");
    const statusEl = root.querySelector("#set-status");
    const metaEl = root.querySelector("#set-meta");

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
      const t = theme === "high-contrast" ? "high-contrast" : "slate";
      document.documentElement.setAttribute("data-theme", t);
      document.body.setAttribute("data-theme", t);
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

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createSettingsPane = createSettingsPane;
})(window);
