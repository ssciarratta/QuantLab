/** i18n scaffold (F60) — default es · stub en · t() + applyDom. */
(function (global) {
  "use strict";

  const DEFAULT_LOCALE = "es";
  const SUPPORTED = { es: true, en: true };

  const MESSAGES = {
    es: {
      "app.name": "QuantLab",
      "skip_to_content": "Ir al contenido",
      "menu.start": "Menú inicio",
      "menu.workspaces": "Espacios de trabajo",
      "menu.session": "Sesión",
      "menu.lab": "Laboratorio",
      "menu.windows": "Ventanas",
      "menu.system": "Sistema",
      "action.minimize_all": "Minimize all",
      "action.restore_all": "Restore all windows",
      "action.cascade_windows": "Cascade windows",
      "action.tile_windows": "Tile windows",
      "action.bring_to_front": "Bring to Front",
      "action.send_to_back": "Send to Back",
      "action.maximize_window": "Maximize window",
      "action.restore_from_maximize": "Restore from Maximize",
      "preset.research": "Research",
      "preset.trading_paper": "Trading Paper",
      "preset.ops": "Ops",
      "preset.save": "Guardar espacio actual…",
      "preset.custom_group": "Custom",
      "preset.save_prompt": "Nombre del preset custom:",
      "preset.delete": "Eliminar",
      "preset.delete_title": "Eliminar preset custom",
      "preset.delete_confirm": "¿Eliminar preset custom?",
      "pane.health": "Salud / Modo",
      "pane.market": "Market Data",
      "pane.universe": "Universe",
      "pane.catalog": "Data Catalog",
      "pane.blotter": "Paper Blotter",
      "pane.journal": "Journal",
      "pane.paper_session": "Sesión Paper",
      "pane.positions": "Posiciones",
      "pane.risk": "Riesgo",
      "pane.chat": "Chat IA",
      "pane.backtest": "Backtest",
      "pane.scanner": "Alpha Scanner",
      "pane.metrics": "Metrics / Último",
      "pane.reports": "Reports",
      "pane.experiments": "Experiments",
      "pane.optimize": "Optimizer",
      "pane.montecarlo": "Monte Carlo",
      "pane.features": "Features",
      "pane.export_hb": "Hummingbot Export",
      "pane.validation": "Validation Splits",
      "pane.sessions": "Sessions",
      "pane.activity": "Activity",
      "pane.access_log": "Access Log",
      "pane.backups": "Backups",
      "pane.ops_metrics": "Ops Metrics",
      "pane.reconciliation": "Reconciliación",
      "pane.venues": "Venues",
      "pane.api_explorer": "API Explorer",
      "pane.settings": "Settings",
      "pane.docs": "Help / Docs",
      "pane.about": "Acerca de",
      "btn.save": "Guardar",
      "btn.refresh": "Recargar",
      "btn.close": "Cerrar",
      "btn.cancel": "Cancelar",
      "btn.export": "Exportar sesión",
      "btn.import": "Importar",
      "btn.download": "Descargar ZIP",
      "aria.taskbar": "Barra de tareas",
      "aria.windows": "Ventanas abiertas",
      "aria.version": "Versión QuantLab",
      "aria.workspace": "Escritorio",
      "aria.palette": "Command Palette",
      "aria.about": "Acerca de QuantLab",
      "aria.onboarding": "Onboarding QuantLab",
      "aria.status": "Status bar",
      "chat.banner": "Asistente research — no envía órdenes",
      "status.mode": "mode",
      "status.live": "live",
      "status.session": "session",
      "status.venue": "venue",
      "status.md": "md",
      "status.heartbeat": "hb",
    },
    en: {
      "app.name": "QuantLab",
      "skip_to_content": "Skip to content",
      "menu.start": "Start menu",
      "menu.workspaces": "Workspaces",
      "menu.session": "Session",
      "menu.lab": "Lab",
      "menu.windows": "Windows",
      "menu.system": "System",
      "action.minimize_all": "Minimize all",
      "action.restore_all": "Restore all windows",
      "action.cascade_windows": "Cascade windows",
      "action.tile_windows": "Tile windows",
      "action.bring_to_front": "Bring to Front",
      "action.send_to_back": "Send to Back",
      "action.maximize_window": "Maximize window",
      "action.restore_from_maximize": "Restore from Maximize",
      "preset.research": "Research",
      "preset.trading_paper": "Trading Paper",
      "preset.ops": "Ops",
      "preset.save": "Save current workspace…",
      "preset.custom_group": "Custom",
      "preset.save_prompt": "Custom preset name:",
      "preset.delete": "Delete",
      "preset.delete_title": "Delete custom preset",
      "preset.delete_confirm": "Delete custom preset?",
      "pane.health": "Health / Mode",
      "pane.market": "Market Data",
      "pane.universe": "Universe",
      "pane.catalog": "Data Catalog",
      "pane.blotter": "Paper Blotter",
      "pane.journal": "Journal",
      "pane.paper_session": "Paper Session",
      "pane.positions": "Positions",
      "pane.risk": "Risk",
      "pane.chat": "AI Chat",
      "pane.backtest": "Backtest",
      "pane.scanner": "Alpha Scanner",
      "pane.metrics": "Metrics / Last",
      "pane.reports": "Reports",
      "pane.experiments": "Experiments",
      "pane.optimize": "Optimizer",
      "pane.montecarlo": "Monte Carlo",
      "pane.features": "Features",
      "pane.export_hb": "Hummingbot Export",
      "pane.validation": "Validation Splits",
      "pane.sessions": "Sessions",
      "pane.activity": "Activity",
      "pane.access_log": "Access Log",
      "pane.backups": "Backups",
      "pane.ops_metrics": "Ops Metrics",
      "pane.reconciliation": "Reconciliation",
      "pane.venues": "Venues",
      "pane.api_explorer": "API Explorer",
      "pane.settings": "Settings",
      "pane.docs": "Help / Docs",
      "pane.about": "About",
      "btn.save": "Save",
      "btn.refresh": "Reload",
      "btn.close": "Close",
      "btn.cancel": "Cancel",
      "btn.export": "Export session",
      "btn.import": "Import",
      "btn.download": "Download ZIP",
      "aria.taskbar": "Taskbar",
      "aria.windows": "Open windows",
      "aria.version": "QuantLab version",
      "aria.workspace": "Desktop",
      "aria.palette": "Command Palette",
      "aria.about": "About QuantLab",
      "aria.onboarding": "QuantLab Onboarding",
      "aria.status": "Status bar",
      "chat.banner": "Research assistant — does not send orders",
      "status.mode": "mode",
      "status.live": "live",
      "status.session": "session",
      "status.venue": "venue",
      "status.md": "md",
      "status.heartbeat": "hb",
    },
  };

  let current = DEFAULT_LOCALE;

  function normalize(locale) {
    if (!locale) return DEFAULT_LOCALE;
    const base = String(locale).trim().toLowerCase().split("-")[0];
    return SUPPORTED[base] ? base : DEFAULT_LOCALE;
  }

  function t(key, fallback) {
    const dict = MESSAGES[current] || MESSAGES[DEFAULT_LOCALE];
    if (dict && Object.prototype.hasOwnProperty.call(dict, key)) {
      return dict[key];
    }
    const es = MESSAGES[DEFAULT_LOCALE];
    if (es && Object.prototype.hasOwnProperty.call(es, key)) {
      return es[key];
    }
    return fallback != null ? fallback : key;
  }

  function setLocale(locale) {
    current = normalize(locale);
    if (document.documentElement) {
      document.documentElement.lang = current;
    }
    return current;
  }

  function getLocale() {
    return current;
  }

  function applyAttr(el, attr, key) {
    if (!el || !key) return;
    const val = t(key);
    if (attr === "text") {
      el.textContent = val;
    } else if (attr === "title") {
      el.setAttribute("title", val);
    } else if (attr === "aria-label") {
      el.setAttribute("aria-label", val);
    } else if (attr === "placeholder") {
      el.setAttribute("placeholder", val);
    }
  }

  function applyDom(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach(function (el) {
      applyAttr(el, "text", el.getAttribute("data-i18n"));
    });
    scope.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      applyAttr(el, "aria-label", el.getAttribute("data-i18n-aria"));
    });
    scope.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      applyAttr(el, "title", el.getAttribute("data-i18n-title"));
    });
  }

  function mergeMessages(locale, messages) {
    const loc = normalize(locale);
    if (!messages || typeof messages !== "object") return;
    MESSAGES[loc] = Object.assign({}, MESSAGES[loc] || {}, messages);
  }

  global.QLi18n = {
    DEFAULT_LOCALE: DEFAULT_LOCALE,
    t: t,
    setLocale: setLocale,
    getLocale: getLocale,
    applyDom: applyDom,
    mergeMessages: mergeMessages,
    supported: Object.keys(SUPPORTED),
  };
})(window);
