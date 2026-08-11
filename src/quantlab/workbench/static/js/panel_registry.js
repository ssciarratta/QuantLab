/** Fuente única de paneles — navegación por tarea (7 grupos). Sin backend. */
(function (global) {
  "use strict";

  /** @typedef {{ id: string, label: string, subtitle?: string, tip: string, primary?: boolean, advanced?: boolean }} PanelDef */

  /** @type {Record<string, PanelDef>} */
  var PANELS = {
    home: {
      id: "home",
      label: "Inicio",
      subtitle: "Orientación y accesos rápidos",
      tip: "Estado del sistema y flujo principal del laboratorio.",
      primary: true,
    },
    chat: {
      id: "chat",
      label: "Asistente",
      subtitle: "Chat IA",
      tip: "Asistente research — no envía órdenes.",
    },
    scanner: {
      id: "scanner",
      label: "Buscar oportunidades",
      subtitle: "Alpha Scanner",
      tip: "Ranking MD real multi-mercado.",
      primary: true,
    },
    universe: {
      id: "universe",
      label: "Lista de seguimiento",
      subtitle: "Universe",
      tip: "Watchlist y universo de símbolos.",
    },
    market: {
      id: "market",
      label: "Cotizaciones en vivo",
      subtitle: "Market Data",
      tip: "Snapshots read-only de mercado.",
    },
    catalog: {
      id: "catalog",
      label: "Datos disponibles",
      subtitle: "Data Catalog",
      tip: "Artefactos del laboratorio.",
    },
    features: {
      id: "features",
      label: "Variables calculadas",
      subtitle: "Features",
      tip: "Ingeniería de features.",
      advanced: true,
    },
    simulator: {
      id: "simulator",
      label: "Comparar mercados",
      subtitle: "Simulador multi-venue",
      tip: "Comparar mercados × monedas × leverage.",
      primary: true,
    },
    backtest: {
      id: "backtest",
      label: "Probar en histórico",
      subtitle: "Backtest",
      tip: "Debug sintético / histórico.",
      primary: true,
    },
    montecarlo: {
      id: "montecarlo",
      label: "Simular escenarios",
      subtitle: "Monte Carlo",
      tip: "Estrés estadístico y volatilidad.",
      primary: true,
    },
    optimize: {
      id: "optimize",
      label: "Optimizar parámetros",
      subtitle: "Optimizer",
      tip: "Grid de parámetros.",
      advanced: true,
    },
    validation: {
      id: "validation",
      label: "Validación train/test",
      subtitle: "Validation Splits",
      tip: "Splits train/test.",
      advanced: true,
    },
    strategy_live_test: {
      id: "strategy_live_test",
      label: "Ejecutar en prueba",
      subtitle: "Corrida en vivo · paper / testnet",
      tip: "Paper / testnet con MD real.",
      primary: true,
    },
    paper_session: {
      id: "paper_session",
      label: "Motor paper (avanzado)",
      subtitle: "Sesión paper · step manual",
      tip: "Capital y PnL · step manual.",
      advanced: true,
    },
    binance_spot: {
      id: "binance_spot",
      label: "Prueba Spot Testnet",
      subtitle: "Binance Spot Testnet",
      tip: "Conexión Spot Testnet.",
      advanced: true,
    },
    binance_futures: {
      id: "binance_futures",
      label: "Prueba Futures Testnet",
      subtitle: "Binance Futures Testnet",
      tip: "Conexión Futures Testnet.",
      advanced: true,
    },
    monitor: {
      id: "monitor",
      label: "Operación activa",
      subtitle: "Monitoreo unificado",
      tip: "Estado de corrida, órdenes, posiciones y riesgo en una vista.",
      primary: true,
    },
    blotter: {
      id: "blotter",
      label: "Órdenes simuladas",
      subtitle: "Paper Blotter",
      tip: "Órdenes paper en curso.",
    },
    journal: {
      id: "journal",
      label: "Registro de fills",
      subtitle: "Journal",
      tip: "Fills autoritativos.",
    },
    positions: {
      id: "positions",
      label: "Posiciones y PnL",
      subtitle: "Posiciones",
      tip: "Posiciones abiertas.",
    },
    risk: {
      id: "risk",
      label: "Límites y kill switch",
      subtitle: "Riesgo",
      tip: "Límites paper.",
    },
    reconciliation: {
      id: "reconciliation",
      label: "Verificar consistencia",
      subtitle: "Reconciliación",
      tip: "Book vs journal.",
      advanced: true,
    },
    sim_registry: {
      id: "sim_registry",
      label: "Mis simulaciones",
      subtitle: "Historial Comparar / MC",
      tip: "Historial local Comparar / Ranking / MC.",
      primary: true,
    },
    metrics: {
      id: "metrics",
      label: "Última corrida",
      subtitle: "Metrics",
      tip: "Métricas del último run.",
    },
    reports: {
      id: "reports",
      label: "Informes",
      subtitle: "Reports",
      tip: "Informes y resúmenes.",
    },
    experiments: {
      id: "experiments",
      label: "Experimentos guardados",
      subtitle: "Experiments",
      tip: "Registro de experimentos.",
    },
    export_hb: {
      id: "export_hb",
      label: "Exportar a Hummingbot",
      subtitle: "Hummingbot Export",
      tip: "Export para Hummingbot.",
    },
    strategies: {
      id: "strategies",
      label: "Catálogo de estrategias",
      subtitle: "IDs y guías",
      tip: "Catálogo y guías.",
    },
    guided_lab: {
      id: "guided_lab",
      label: "Asistente paso a paso",
      subtitle: "Guided Lab",
      tip: "Wizard paso a paso (legacy).",
      advanced: true,
    },
    health: {
      id: "health",
      label: "Estado del sistema",
      subtitle: "Salud / modo",
      tip: "Estado PAPER y LIVE_BLOCKED.",
    },
    settings: {
      id: "settings",
      label: "Ajustes",
      subtitle: "Settings",
      tip: "Preferencias UI y sesión.",
    },
    sessions: {
      id: "sessions",
      label: "Sesiones locales",
      subtitle: "Sessions",
      tip: "Gestión de sesiones locales.",
    },
    backups: {
      id: "backups",
      label: "Copias de seguridad",
      subtitle: "Backups",
      tip: "Backup / restore.",
    },
    diagnostics: {
      id: "diagnostics",
      label: "Diagnóstico completo",
      subtitle: "Diagnostics",
      tip: "Bundle de diagnóstico.",
    },
    api_explorer: {
      id: "api_explorer",
      label: "Explorar API",
      subtitle: "API Explorer",
      tip: "Endpoints del workbench.",
      advanced: true,
    },
    activity: {
      id: "activity",
      label: "Actividad reciente",
      subtitle: "Activity log",
      tip: "Log de actividad de sesión.",
    },
    access_log: {
      id: "access_log",
      label: "Registro HTTP",
      subtitle: "Access Log",
      tip: "Access log de la API.",
      advanced: true,
    },
    ops_metrics: {
      id: "ops_metrics",
      label: "Métricas del servidor",
      subtitle: "Ops Metrics",
      tip: "Métricas operativas del servidor.",
      advanced: true,
    },
    venues: {
      id: "venues",
      label: "Mercados conectados",
      subtitle: "Venues",
      tip: "Brokers registrados.",
      advanced: true,
    },
    docs: {
      id: "docs",
      label: "Ayuda",
      subtitle: "Help / Docs",
      tip: "Documentación embebida.",
    },
    about: {
      id: "about",
      label: "Acerca de QuantLab",
      subtitle: "Versión y fases",
      tip: "Versión y fases del build.",
    },
  };

  var GROUPS = [
    {
      id: "inicio",
      label: "Inicio",
      defaultOpen: true,
      paneIds: ["home", "chat", "health"],
    },
    {
      id: "investigar",
      label: "Investigar",
      defaultOpen: true,
      paneIds: ["scanner", "universe", "market", "catalog", "features", "strategies"],
    },
    {
      id: "probar",
      label: "Probar",
      defaultOpen: true,
      paneIds: [
        "simulator",
        "backtest",
        "montecarlo",
        "optimize",
        "validation",
        "guided_lab",
      ],
    },
    {
      id: "ejecutar",
      label: "Ejecutar en prueba",
      defaultOpen: true,
      paneIds: [
        "strategy_live_test",
        "paper_session",
        "binance_spot",
        "binance_futures",
      ],
    },
    {
      id: "monitorear",
      label: "Monitorear",
      defaultOpen: false,
      paneIds: ["monitor", "blotter", "journal", "positions", "risk", "reconciliation"],
    },
    {
      id: "resultados",
      label: "Resultados",
      defaultOpen: false,
      paneIds: ["sim_registry", "metrics", "reports", "experiments", "export_hb"],
    },
    {
      id: "sistema",
      label: "Sistema",
      defaultOpen: false,
      paneIds: [
        "settings",
        "sessions",
        "backups",
        "diagnostics",
        "api_explorer",
        "activity",
        "access_log",
        "ops_metrics",
        "venues",
        "docs",
        "about",
      ],
    },
  ];

  var TASKBAR_DEFAULT = [
    "home",
    "scanner",
    "simulator",
    "strategy_live_test",
    "sim_registry",
    "chat",
  ];

  var NEXT_FLOW = {
    scanner: { paneId: "simulator", label: "Comparar mercados" },
    simulator: { paneId: "strategy_live_test", label: "Ejecutar en prueba" },
    backtest: { paneId: "montecarlo", label: "Simular escenarios" },
    montecarlo: { paneId: "strategy_live_test", label: "Ejecutar en prueba" },
    strategy_live_test: { paneId: "monitor", label: "Monitorear operación" },
    monitor: { paneId: "sim_registry", label: "Ver resultados" },
  };

  var FLOW_STEPS = [
    { paneId: "scanner", label: "Buscar" },
    { paneId: "simulator", label: "Comparar" },
    { paneId: "backtest", label: "Histórico" },
    { paneId: "montecarlo", label: "Escenarios" },
    { paneId: "strategy_live_test", label: "Ejecutar" },
    { paneId: "sim_registry", label: "Resultados" },
  ];

  var LAYOUT_PRESETS = {
    investigar: {
      label: "Investigar",
      tip: "Scanner, universo y cotizaciones.",
      paneIds: ["scanner", "universe", "market"],
    },
    probar: {
      label: "Probar estrategia",
      tip: "Simulador, backtest y Monte Carlo.",
      paneIds: ["simulator", "backtest", "montecarlo"],
    },
    ejecutar: {
      label: "Ejecutar en prueba",
      tip: "Corrida en vivo paper/testnet.",
      paneIds: ["strategy_live_test"],
    },
    monitorear: {
      label: "Monitorear operación",
      tip: "Blotter, journal, posiciones y riesgo.",
      paneIds: ["strategy_live_test", "monitor", "blotter", "journal", "positions", "risk"],
    },
    resultados: {
      label: "Revisar resultados",
      tip: "Mis simulaciones e informes.",
      paneIds: ["sim_registry", "reports", "metrics"],
    },
  };

  function getPanel(id) {
    return PANELS[id] || { id: id, label: id, tip: id };
  }

  function getMenuSections() {
    return GROUPS.map(function (g) {
      return {
        id: g.id,
        label: g.label,
        defaultOpen: g.defaultOpen !== false,
        items: g.paneIds.map(function (pid) {
          var p = getPanel(pid);
          return { id: p.id, label: p.label, tip: p.tip, subtitle: p.subtitle };
        }),
      };
    });
  }

  function getNextStep(paneId) {
    return NEXT_FLOW[paneId] || null;
  }

  function getPrimaryHomeActions() {
    return [
      "scanner",
      "simulator",
      "strategy_live_test",
      "monitor",
      "sim_registry",
      "chat",
    ].map(function (id) {
      return getPanel(id);
    });
  }

  function listAllPaneIds() {
    return Object.keys(PANELS);
  }

  function listAdvancedPaneIds() {
    return listAllPaneIds().filter(function (id) {
      return PANELS[id] && PANELS[id].advanced;
    });
  }

  global.QLPanelRegistry = {
    version: 1,
    groups: GROUPS,
    panels: PANELS,
    taskbarDefault: TASKBAR_DEFAULT,
    flowSteps: FLOW_STEPS,
    layoutPresets: LAYOUT_PRESETS,
    getPanel: getPanel,
    getMenuSections: getMenuSections,
    getPrimaryHomeActions: getPrimaryHomeActions,
    getNextStep: getNextStep,
    nextFlow: NEXT_FLOW,
    listAllPaneIds: listAllPaneIds,
    listAdvancedPaneIds: listAdvancedPaneIds,
  };
})(typeof window !== "undefined" ? window : globalThis);
