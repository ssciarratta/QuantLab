/** Shell del escritorio QuantLab Workbench. */
(function () {
  "use strict";

  const workspace = document.getElementById("workspace");
  const taskbarWindows = document.getElementById("taskbar-windows");
  const bannerMode = document.getElementById("banner-mode");
  const bannerLive = document.getElementById("banner-live");
  const bannerSession = document.getElementById("banner-session");
  const bannerVersion = document.getElementById("banner-version");
  const bannerUpdated = document.getElementById("banner-updated");
  const bannerUpdateBtn = document.getElementById("banner-update-btn");
  const clockEl = document.getElementById("sb-clock");
  const startBtn = document.getElementById("btn-start");
  const startMenu = document.getElementById("start-menu");
  const sbMode = document.getElementById("sb-mode");
  const sbLive = document.getElementById("sb-live");
  const sbSession = document.getElementById("sb-session");
  const sbVenue = document.getElementById("sb-venue");
  const sbMd = document.getElementById("sb-md");
  const sbHeartbeat = document.getElementById("sb-heartbeat");
  const sbVersion = document.getElementById("sb-version");

  let sessionMode = "tester";
  let savedGeom = {};
  let cachedSessionId = "—";
  let cachedVersion = null;
  let clockTimezone = "UTC"; /* F74: settings.timezone UTC|local */
  let heartbeatPollSeconds = 5; /* F75: N seconds · GET /api/broker/heartbeat */
  let heartbeatTimer = null;
  let uiFontScale = 1.15;
  const FONT_MIN = 0.85;
  const FONT_MAX = 1.6;
  const FONT_STEP = 0.1;

  const wm = new QLWindowManager(workspace, taskbarWindows);

  wm.setLayoutChangeHandler(function (layout) {
    if (!QLApi || !QLApi.putLayout) return;
    QLApi.putLayout(layout).catch(function () {});
  });

  function mergeOpts(id, defaults) {
    const g = savedGeom[id];
    if (!g) return defaults;
    const out = {
      x: g.x != null ? g.x : defaults.x,
      y: g.y != null ? g.y : defaults.y,
      w: g.w != null ? g.w : defaults.w,
      h: g.h != null ? g.h : defaults.h,
      // Nunca reabrir minimizado desde el menú (parecía que «se cerraba»).
      minimized: false,
      maximized: !!g.maximized,
    };
    if (g.z != null) out.z = g.z;
    return out;
  }

  function applyTheme(theme) {
    /* F48: data-theme on documentElement (+ body) from settings load / PUT */
    const t = theme === "high-contrast" ? "high-contrast" : "slate";
    document.documentElement.setAttribute("data-theme", t);
    if (document.body) document.body.setAttribute("data-theme", t);
  }

  function applyFontScale(scale, persist) {
    let s = Number(scale);
    if (!isFinite(s)) s = 1.15;
    if (s < FONT_MIN) s = FONT_MIN;
    if (s > FONT_MAX) s = FONT_MAX;
    s = Math.round(s * 100) / 100;
    uiFontScale = s;
    document.documentElement.style.setProperty("--ql-font-scale", String(s));
    const label = document.getElementById("sb-font-value");
    if (label) label.textContent = Math.round(s * 100) + "%";
    try {
      localStorage.setItem("ql_ui_font_scale", String(s));
    } catch (e) {}
    if (persist && QLApi && QLApi.putSettings) {
      QLApi.putSettings({ ui_font_scale: s }).catch(function () {});
    }
  }

  function bumpFont(delta) {
    applyFontScale(uiFontScale + delta, true);
  }

  function tr(key, fallback) {
    if (window.QLi18n && typeof QLi18n.t === "function") {
      return QLi18n.t(key, fallback);
    }
    return fallback != null ? fallback : key;
  }

  function applyLocale(locale) {
    /* F60: settings.locale → QLi18n + DOM chrome (menú / aria / botones) */
    if (!window.QLi18n) return;
    const loc = QLi18n.setLocale(locale || QLi18n.DEFAULT_LOCALE || "es");
    QLi18n.applyDom(document);
    return loc;
  }

  function updateStatusBar(payload) {
    if (!payload) return;
    if (payload.mode) {
      sessionMode = payload.mode;
      const label =
        sessionMode === "paper" ? "PAPER (REAL)" : String(sessionMode).toUpperCase();
      if (sbMode) sbMode.textContent = label;
    }
    const blocked = payload.live_blocked !== false;
    if (sbLive) {
      sbLive.textContent = blocked ? "LIVE_BLOCKED" : "LIVE_UNLOCKED";
      sbLive.classList.toggle("unlocked", !blocked);
    }
    if (payload.session_id) {
      cachedSessionId = payload.session_id;
      if (sbSession) sbSession.textContent = cachedSessionId;
    } else if (sbSession && cachedSessionId) {
      sbSession.textContent = cachedSessionId;
    }
    if (sbVenue) {
      sbVenue.textContent =
        payload.venue ||
        (payload.settings && payload.settings.default_venue) ||
        "—";
    }
    if (sbMd) {
      sbMd.textContent = payload.md_provider || "—";
    }
    if (payload.version && sbVersion) {
      cachedVersion = payload.version;
      sbVersion.textContent = "v" + cachedVersion;
    }
  }

  function refreshVersionBadge() {
    if (!QLApi || !QLApi.about) return;
    QLApi.about()
      .then(function (data) {
        if (!data) return;
        if (sbVersion && data.version) {
          cachedVersion = data.version;
          sbVersion.textContent = "v" + data.version;
        }
        updateStatusBar({
          live_blocked: data.live_blocked !== false,
          version: data.version,
        });
      })
      .catch(function () {});
    refreshUpdateBanner();
  }

  function refreshUpdateBanner() {
    if (!QLApi || !QLApi.updateStatus) return;
    QLApi.updateStatus()
      .then(function (data) {
        if (!data) return;
        const localV = data.local_version || data.package_version || "—";
        const ghV = data.github_version;
        let label = "v" + localV;
        if (ghV) {
          if (ghV === localV && !data.update_available) {
            label = "v" + localV + " · GH ok";
          } else {
            label = "v" + localV + " · GH " + ghV;
          }
        }
        if (bannerVersion) bannerVersion.textContent = label;
        if (sbVersion && localV && localV !== "—") {
          cachedVersion = localV;
          sbVersion.textContent = "v" + localV;
        }
        if (bannerUpdated) {
          bannerUpdated.textContent =
            "mod " + (data.last_modified_display || "—");
          if (data.last_modified_at) {
            var src = data.last_modified_source
              ? " [" + data.last_modified_source + "]"
              : "";
            bannerUpdated.title =
              "Última modificación: " +
              data.last_modified_at +
              src +
              " (archivos locales / git)";
          }
        }
        document.title = "QuantLab Workbench v" + localV;
        if (bannerUpdateBtn) {
          bannerUpdateBtn.hidden = false;
          bannerUpdateBtn.disabled = false;
          bannerUpdateBtn.textContent = data.update_available
            ? "Actualizar"
            : "Sincronizar";
          bannerUpdateBtn.title = data.update_available
            ? "Hay versión nueva en GitHub — git pull + reinicio"
            : "Forzar sync con GitHub (git pull) aunque ya estés al día";
        }
      })
      .catch(function () {
        if (bannerVersion && !bannerVersion.textContent.startsWith("v")) {
          bannerVersion.textContent = "v—";
        }
      });
  }

  function onBannerUpdateClick() {
    if (!QLApi || !QLApi.updateApply || !bannerUpdateBtn) return;
    if (
      !window.confirm(
        "¿Descargar la última versión desde GitHub (git pull)?\n" +
          "Después tenés que reiniciar QuantLab para aplicar el código."
      )
    ) {
      return;
    }
    bannerUpdateBtn.disabled = true;
    bannerUpdateBtn.textContent = "…";
    QLApi.updateApply()
      .then(function (data) {
        const msg =
          (data && data.message) ||
          "Actualizado. Reiniciá QuantLab para cargar el código.";
        if (window.QLToasts && QLToasts.show) {
          QLToasts.show("ok", msg);
        } else {
          window.alert(msg);
        }
        refreshUpdateBanner();
      })
      .catch(function (err) {
        const msg =
          (err && err.message) ||
          "No se pudo actualizar (¿cambios locales sin commit?).";
        if (window.QLToasts && QLToasts.show) {
          QLToasts.show("error", msg);
        } else {
          window.alert(msg);
        }
        if (bannerUpdateBtn) {
          bannerUpdateBtn.disabled = false;
          bannerUpdateBtn.textContent = "Actualizar";
        }
      });
  }

  if (bannerUpdateBtn) {
    bannerUpdateBtn.addEventListener("click", onBannerUpdateClick);
  }

  function updateBanner(modePayload) {
    if (!modePayload) return;
    sessionMode = modePayload.mode || sessionMode;
    const label =
      sessionMode === "paper" ? "PAPER (REAL)" : String(sessionMode).toUpperCase();
    bannerMode.textContent = "modo " + label;
    const blocked = modePayload.live_blocked !== false;
    bannerLive.textContent = blocked ? "LIVE_BLOCKED" : "LIVE_UNLOCKED";
    bannerLive.style.borderColor = blocked ? "" : "#d4544a";
    bannerLive.style.color = blocked ? "" : "#d4544a";
    updateStatusBar({
      mode: sessionMode,
      live_blocked: blocked,
      session_id: cachedSessionId !== "—" ? cachedSessionId : undefined,
    });
  }

  function openHealth() {
    const pane = QLPanes.createHealthPane(updateBanner);
    wm.open("health", tr("pane.health", "Salud / Modo"), pane, mergeOpts("health", { x: 24, y: 20, w: 440, h: 360 }));
    pane.refresh().catch(function () {});
  }

  function openMarket() {
    const pane = QLPanes.createMarketPane(function () {
      return sessionMode;
    });
    wm.open("market", tr("pane.market", "Market Data"), pane, mergeOpts("market", { x: 360, y: 40, w: 460, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openUniverse() {
    const pane = QLPanes.createUniversePane();
    wm.open("universe", tr("pane.universe", "Universe"), pane, mergeOpts("universe", { x: 40, y: 60, w: 480, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openCatalog() {
    const pane = QLPanes.createCatalogPane();
    wm.open("catalog", tr("pane.catalog", "Data Catalog"), pane, mergeOpts("catalog", { x: 80, y: 80, w: 560, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openBlotter() {
    const pane = QLPanes.createBlotterPane();
    wm.open("blotter", tr("pane.blotter", "Paper Blotter"), pane, mergeOpts("blotter", { x: 120, y: 120, w: 520, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openJournal() {
    const pane = QLPanes.createJournalPane();
    wm.open("journal", tr("pane.journal", "Journal"), pane, mergeOpts("journal", { x: 180, y: 100, w: 560, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openPaperSession() {
    const pane = QLPanes.createPaperSessionPane();
    wm.open(
      "paper_session",
      tr("pane.paper_session", "Sesión Paper"),
      pane,
      mergeOpts("paper_session", { x: 160, y: 90, w: 520, h: 440 })
    );
    pane.refresh().catch(function () {});
  }

  function openPositions() {
    const pane = QLPanes.createPositionsPane();
    wm.open("positions", tr("pane.positions", "Posiciones"), pane, mergeOpts("positions", { x: 200, y: 80, w: 480, h: 360 }));
    pane.refresh().catch(function () {});
  }

  function openRisk() {
    const pane = QLPanes.createRiskPane();
    wm.open("risk", tr("pane.risk", "Riesgo"), pane, mergeOpts("risk", { x: 240, y: 60, w: 460, h: 380 }));
    pane.refresh().catch(function () {});
  }

  function openReconciliation() {
    const pane = QLPanes.createReconciliationPane();
    wm.open(
      "reconciliation",
      tr("pane.reconciliation", "Reconciliación"),
      pane,
      mergeOpts("reconciliation", { x: 260, y: 70, w: 500, h: 440 })
    );
    pane.refresh();
  }

  function openVenues() {
    const pane = QLPanes.createVenuesPane();
    wm.open(
      "venues",
      tr("pane.venues", "Venues"),
      pane,
      mergeOpts("venues", { x: 280, y: 90, w: 480, h: 420 })
    );
    pane.refresh();
  }

  function openApiExplorer() {
    const pane = QLPanes.createApiExplorerPane();
    wm.open(
      "api_explorer",
      tr("pane.api_explorer", "API Explorer"),
      pane,
      mergeOpts("api_explorer", { x: 300, y: 100, w: 560, h: 460 })
    );
    pane.refresh();
  }

  function openGuidedLab(opts) {
    opts = opts || {};
    if ((opts.focusId || opts.prefill) && window.QLNav) {
      window.QLNav.setFocus("guided_lab", {
        focusId: opts.focusId || null,
        prefill: opts.prefill || null,
        message: opts.message || null,
      });
    }
    if (wm.windows.has("guided_lab")) {
      wm.focus("guided_lab");
      const root = wm.windows.get("guided_lab").body.firstElementChild;
      if (root && typeof root.applyNavFocus === "function") root.applyNavFocus();
      return;
    }
    const pane = QLPanes.createGuidedLabPane();
    wm.open(
      "guided_lab",
      tr("pane.guided_lab", "Guided Lab"),
      pane,
      mergeOpts("guided_lab", { x: 160, y: 40, w: 680, h: 640 })
    );
    if (pane.refresh) pane.refresh();
    if (typeof pane.applyNavFocus === "function") pane.applyNavFocus();
  }

  function openSimulator(opts) {
    opts = opts || {};
    if (opts.prefill && window.QLNav) {
      window.QLNav.setFocus("simulator", { prefill: opts.prefill });
    }
    if (wm.windows.has("simulator")) {
      wm.focus("simulator");
      const root = wm.windows.get("simulator").body.firstElementChild;
      if (root && typeof root.applyPrefill === "function" && opts.prefill) {
        root.applyPrefill(opts.prefill);
      } else if (root && root.refresh) {
        root.refresh();
      }
      return;
    }
    const pane = QLPanes.createSimulatorPane();
    wm.open(
      "simulator",
      tr("pane.simulator", "Simulador"),
      pane,
      mergeOpts("simulator", { x: 40, y: 20, w: 980, h: 720 })
    );
    if (pane.refresh) pane.refresh();
    if (opts.prefill && typeof pane.applyPrefill === "function") {
      pane.applyPrefill(opts.prefill);
    }
  }

  function openDiagnostics() {
    const pane = QLPanes.createDiagnosticsPane();
    wm.open(
      "diagnostics",
      tr("pane.diagnostics", "Diagnostics"),
      pane,
      mergeOpts("diagnostics", { x: 320, y: 110, w: 520, h: 480 })
    );
    pane.refresh();
  }

  function openBacktest(opts) {
    opts = opts || {};
    if (wm.windows.has("backtest")) {
      wm.focus("backtest");
      const root = wm.windows.get("backtest").body.firstElementChild;
      if (root && typeof root.applyNavFocus === "function") root.applyNavFocus();
      return;
    }
    const pane = QLPanes.createBacktestPane();
    wm.open("backtest", tr("pane.backtest", "Backtest"), pane, mergeOpts("backtest", { x: 48, y: 48, w: 560, h: 480 }));
    if (typeof pane.applyNavFocus === "function") pane.applyNavFocus();
  }

  function openScanner(opts) {
    opts = opts || {};
    if (wm.windows.has("scanner")) {
      wm.focus("scanner");
      return;
    }
    const pane = QLPanes.createScannerPane();
    wm.open("scanner", tr("pane.scanner", "Alpha Scanner"), pane, mergeOpts("scanner", { x: 80, y: 40, w: 720, h: 640 }));
  }

  function openStrategies(opts) {
    opts = opts || {};
    if (wm.windows.has("strategies")) {
      wm.focus("strategies");
      const root = wm.windows.get("strategies").body.firstElementChild;
      if (root && opts.focusId && typeof root.focusStrategy === "function") {
        root.focusStrategy(opts.focusId);
      } else if (root && root.refresh) {
        root.refresh();
      }
      return;
    }
    const pane = QLPanes.createStrategiesPane({ focusId: opts.focusId });
    wm.open(
      "strategies",
      tr("pane.strategies", "Estrategias"),
      pane,
      mergeOpts("strategies", { x: 60, y: 30, w: 640, h: 700 })
    );
  }

  function openSimRegistry() {
    if (!window.QLSimRegistry || typeof QLSimRegistry.openWindow !== "function") {
      return;
    }
    QLSimRegistry.openWindow(
      mergeOpts("sim_registry", { x: 12, y: 12, w: 360, h: 440 })
    );
  }

  function openMetrics() {
    const pane = QLPanes.createMetricsPane();
    wm.open("metrics", tr("pane.metrics", "Metrics / Último"), pane, mergeOpts("metrics", { x: 100, y: 80, w: 480, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openReports(opts) {
    opts = opts || {};
    if (opts.focusId && window.QLNav) {
      window.QLNav.setFocus("reports", { focusId: opts.focusId, message: opts.message });
    }
    if (wm.windows.has("reports")) {
      wm.focus("reports");
      const root = wm.windows.get("reports").body.firstElementChild;
      if (root && typeof root.applyNavFocus === "function") {
        root.applyNavFocus();
      } else if (root && typeof root.refresh === "function") {
        root.refresh().catch(function () {});
      }
      return;
    }
    const pane = QLPanes.createReportsPane();
    wm.open("reports", tr("pane.reports", "Reports"), pane, mergeOpts("reports", { x: 110, y: 70, w: 620, h: 520 }));
    pane.refresh()
      .then(function () {
        if (typeof pane.applyNavFocus === "function") pane.applyNavFocus();
      })
      .catch(function () {});
  }

  function openExperiments() {
    const pane = QLPanes.createExperimentsPane();
    wm.open(
      "experiments",
      tr("pane.experiments", "Experiments"),
      pane,
      mergeOpts("experiments", { x: 120, y: 90, w: 480, h: 380 })
    );
    pane.refresh().catch(function () {});
  }

  function openOptimize() {
    const pane = QLPanes.createOptimizePane();
    wm.open("optimize", tr("pane.optimize", "Optimizer"), pane, mergeOpts("optimize", { x: 140, y: 70, w: 620, h: 560 }));
  }

  function openMonteCarlo(opts) {
    opts = opts || {};
    if ((opts.prefill || opts.focusId) && window.QLNav) {
      window.QLNav.setFocus("montecarlo", {
        focusId: opts.focusId || null,
        prefill: opts.prefill || null,
        message: (opts.prefill && opts.prefill.message) || opts.message || null,
      });
    }
    if (wm.windows.has("montecarlo")) {
      wm.focus("montecarlo");
      const root = wm.windows.get("montecarlo").body.firstElementChild;
      if (root && typeof root.applyPrefill === "function" && opts.prefill) {
        root.applyPrefill(opts.prefill);
      } else if (root && typeof root.applyNavFocus === "function") {
        root.applyNavFocus();
      }
      return;
    }
    const pane = QLPanes.createMonteCarloPane();
    wm.open(
      "montecarlo",
      tr("pane.montecarlo", "Monte Carlo"),
      pane,
      mergeOpts("montecarlo", { x: 140, y: 60, w: 800, h: 640 })
    );
    if (opts.prefill && typeof pane.applyPrefill === "function") {
      pane.applyPrefill(opts.prefill);
    } else if (typeof pane.applyNavFocus === "function") {
      pane.applyNavFocus();
    }
  }

  function openFeatures() {
    const pane = QLPanes.createFeaturesPane();
    wm.open("features", tr("pane.features", "Features"), pane, mergeOpts("features", { x: 180, y: 110, w: 520, h: 460 }));
  }

  function openExportHb() {
    const pane = QLPanes.createExportHbPane();
    wm.open(
      "export_hb",
      tr("pane.export_hb", "Hummingbot Export"),
      pane,
      mergeOpts("export_hb", { x: 200, y: 90, w: 460, h: 360 })
    );
  }

  function openValidation() {
    const pane = QLPanes.createValidationPane();
    wm.open(
      "validation",
      tr("pane.validation", "Validation Splits"),
      pane,
      mergeOpts("validation", { x: 220, y: 80, w: 480, h: 400 })
    );
    pane.refresh().catch(function () {});
  }

  function openChat() {
    const pane = QLPanes.createChatPane();
    wm.open("chat", tr("pane.chat", "Chat IA"), pane, mergeOpts("chat", { x: 260, y: 40, w: 440, h: 460 }));
    pane.refresh().catch(function () {});
  }

  function openSettings() {
    const pane = QLPanes.createSettingsPane(function (data) {
      updateStatusBar(data);
      if (data && data.settings) {
        applyTheme(data.settings.theme);
        applyLocale(data.settings.locale);
        if (window.QLToasts && QLToasts.setDesktopNotifications) {
          QLToasts.setDesktopNotifications(
            data.settings.desktop_notifications === true
          );
        }
        if (window.QLToasts && QLToasts.setSoundAlerts) {
          QLToasts.setSoundAlerts(data.settings.sound_alerts === true);
        }
        setClockTimezone(data.settings.timezone);
      }
      if (data && data.settings && data.settings.ui_font_scale != null) {
        applyFontScale(data.settings.ui_font_scale, false);
      }
    });
    wm.open("settings", tr("pane.settings", "Settings"), pane, mergeOpts("settings", { x: 280, y: 60, w: 440, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openDocs() {
    const pane = QLPanes.createDocsPane();
    wm.open("docs", tr("pane.docs", "Help / Docs"), pane, mergeOpts("docs", { x: 200, y: 50, w: 560, h: 480 }));
    pane.refresh().catch(function () {});
  }

  function openAbout() {
    if (window.QLAbout && QLAbout.open) {
      QLAbout.open();
    }
  }

  function onSessionSwitched(data) {
    const sid =
      (data && data.session_id) ||
      (data && data.session && data.session.session_id) ||
      "—";
    if (bannerSession) bannerSession.textContent = "session " + sid;
    if (sbSession) sbSession.textContent = sid;
    cachedSessionId = sid;
    QLApi.getMode()
      .then(updateBanner)
      .catch(function () {});
  }

  function openSessions() {
    const pane = QLPanes.createSessionsPane(onSessionSwitched);
    wm.open("sessions", tr("pane.sessions", "Sessions"), pane, mergeOpts("sessions", { x: 200, y: 60, w: 480, h: 440 }));
    pane.refresh().catch(function () {});
  }

  function openActivity() {
    const pane = QLPanes.createActivityPane();
    wm.open("activity", tr("pane.activity", "Activity"), pane, mergeOpts("activity", { x: 220, y: 70, w: 520, h: 440 }));
    pane.refresh().catch(function () {});
  }

  function openAccessLog() {
    const pane = QLPanes.createAccessLogPane();
    wm.open(
      "access_log",
      tr("pane.access_log", "Access Log"),
      pane,
      mergeOpts("access_log", { x: 230, y: 75, w: 560, h: 460 })
    );
    pane.refresh().catch(function () {});
  }

  function openBackups() {
    const pane = QLPanes.createBackupsPane();
    wm.open(
      "backups",
      tr("pane.backups", "Backups"),
      pane,
      mergeOpts("backups", { x: 240, y: 80, w: 560, h: 460 })
    );
    pane.refresh().catch(function () {});
  }

  function openOpsMetrics() {
    const pane = QLPanes.createOpsMetricsPane();
    wm.open(
      "ops_metrics",
      tr("pane.ops_metrics", "Ops Metrics"),
      pane,
      mergeOpts("ops_metrics", { x: 240, y: 80, w: 480, h: 420 })
    );
    pane.refresh().catch(function () {});
  }

  const openers = {
    health: openHealth,
    market: openMarket,
    universe: openUniverse,
    catalog: openCatalog,
    blotter: openBlotter,
    journal: openJournal,
    paper_session: openPaperSession,
    positions: openPositions,
    risk: openRisk,
    reconciliation: openReconciliation,
    venues: openVenues,
    api_explorer: openApiExplorer,
    diagnostics: openDiagnostics,
    guided_lab: openGuidedLab,
    simulator: openSimulator,
    strategies: openStrategies,
    sim_registry: openSimRegistry,
    chat: openChat,
    settings: openSettings,
    docs: openDocs,
    about: openAbout,
    sessions: openSessions,
    activity: openActivity,
    access_log: openAccessLog,
    backups: openBackups,
    ops_metrics: openOpsMetrics,
    backtest: openBacktest,
    scanner: openScanner,
    metrics: openMetrics,
    reports: openReports,
    experiments: openExperiments,
    optimize: openOptimize,
    montecarlo: openMonteCarlo,
    features: openFeatures,
    export_hb: openExportHb,
    validation: openValidation,
  };

  window.QLShell = {
    open: function (paneId, opts) {
      const fn = openers[paneId];
      if (typeof fn === "function") {
        fn(opts || {});
        return true;
      }
      return false;
    },
    openers: openers,
    wm: wm,
    /** Snapshot moneda/estrategia/params del Simulador abierto (si existe). */
    getSimHandoff: function () {
      if (!wm.windows.has("simulator")) return null;
      try {
        const root = wm.windows.get("simulator").body.firstElementChild;
        if (root && typeof root.getSimHandoff === "function") {
          return root.getSimHandoff();
        }
      } catch (e) {}
      return null;
    },
    setFontScale: function (s, persist) {
      applyFontScale(s, persist !== false);
    },
    getFontScale: function () {
      return uiFontScale;
    },
  };

  const fontDown = document.getElementById("sb-font-down");
  const fontUp = document.getElementById("sb-font-up");
  if (fontDown) {
    fontDown.addEventListener("click", function () {
      bumpFont(-FONT_STEP);
    });
  }
  if (fontUp) {
    fontUp.addEventListener("click", function () {
      bumpFont(FONT_STEP);
    });
  }
  try {
    const stored = localStorage.getItem("ql_ui_font_scale");
    if (stored) applyFontScale(stored, false);
    else applyFontScale(uiFontScale, false);
  } catch (e) {
    applyFontScale(uiFontScale, false);
  }

  const palette = new QLCommandPalette({
    openers: openers,
    wm: wm,
    onHealthRefresh: function () {
      QLApi.getMode()
        .then(updateBanner)
        .catch(function () {});
      QLApi.health().catch(function () {});
    },
  });
  palette.load();

  const PANE_SHORTCUT_ORDER = [
    "health",
    "market",
    "universe",
    "catalog",
    "blotter",
    "journal",
    "paper_session",
    "positions",
    "risk",
  ];

  function isTypingTarget(el) {
    if (!el) return false;
    const tag = (el.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return true;
    if (el.isContentEditable) return true;
    return false;
  }

  document.addEventListener("keydown", function (ev) {
    const key = ev.key;
    const ctrl = ev.ctrlKey || ev.metaKey;

    if (key === "Escape") {
      if (palette.isOpen()) {
        ev.preventDefault();
        palette.hide();
        return;
      }
      if (window.QLAbout && QLAbout.isOpen && QLAbout.isOpen()) {
        ev.preventDefault();
        QLAbout.close();
        return;
      }
      if (startMenu && !startMenu.hasAttribute("hidden")) {
        ev.preventDefault();
        closeStartMenu();
        return;
      }
    }

    if (ctrl && (key === "k" || key === "K")) {
      ev.preventDefault();
      palette.toggle();
      return;
    }
    if (ctrl && ev.shiftKey && (key === "p" || key === "P")) {
      ev.preventDefault();
      palette.toggle();
      return;
    }

    if (palette.isOpen()) return;

    // Ctrl+W ya no cierra paneles (solo el botón ×). Evita cierres accidentales.

    if (ctrl && !ev.altKey && !ev.shiftKey && key >= "1" && key <= "9") {
      if (isTypingTarget(ev.target) && !ev.target.closest(".command-palette")) return;
      const idx = parseInt(key, 10) - 1;
      const paneId = PANE_SHORTCUT_ORDER[idx];
      if (paneId && openers[paneId]) {
        ev.preventDefault();
        openers[paneId]();
      }
    }
  });

  startBtn.addEventListener("click", function (ev) {
    ev.preventDefault();
    ev.stopPropagation();
    toggleStartMenu();
  });

  function isStartMenuOpen() {
    return !!(
      startMenu &&
      !startMenu.hasAttribute("hidden") &&
      !startMenu.classList.contains("hidden")
    );
  }

  function openStartMenu() {
    if (!startMenu || !startBtn) return;
    startMenu.removeAttribute("hidden");
    startMenu.classList.remove("hidden");
    startBtn.classList.add("active");
    startBtn.setAttribute("aria-expanded", "true");
    try {
      if (typeof refreshPresetsMenu === "function") refreshPresetsMenu();
    } catch (e) {}
    try {
      if (typeof renderFavoritesMenu === "function") renderFavoritesMenu();
    } catch (e) {}
  }

  function closeStartMenu() {
    if (!startMenu || !startBtn) return;
    startMenu.setAttribute("hidden", "");
    startMenu.classList.add("hidden");
    startBtn.classList.remove("active");
    startBtn.setAttribute("aria-expanded", "false");
  }

  function toggleStartMenu() {
    if (isStartMenuOpen()) closeStartMenu();
    else openStartMenu();
  }

  if (window.QLShell) {
    window.QLShell.toggleStartMenu = toggleStartMenu;
    window.QLShell.openStartMenu = openStartMenu;
    window.QLShell.closeStartMenu = closeStartMenu;
  }

  /* QUANTLAB (banner) abre el mismo menú que el botón QL. */
  var brandEl = document.querySelector(".top-banner .brand");
  if (brandEl && !brandEl._qlStartBound) {
    brandEl._qlStartBound = true;
    brandEl.classList.add("brand-menu-trigger");
    brandEl.setAttribute("role", "button");
    brandEl.setAttribute("tabindex", "0");
    brandEl.setAttribute(
      "title",
      "Abrir menú QL (igual que el botón QL abajo a la izquierda)"
    );
    brandEl.setAttribute("aria-label", "Abrir menú QuantLab");
    brandEl.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      toggleStartMenu();
    });
    brandEl.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        ev.stopPropagation();
        toggleStartMenu();
      }
    });
  }

  // —— Favoritos del menú QL (orden custom, persistido) ——
  var FAV_STORAGE_KEY = "ql_menu_favorites_v2";
  var FAV_DEFAULT = ["chat", "scanner", "simulator", "strategies"];
  var FAV_META = {
    chat: { label: "Chat IA", tip: "Asistente research." },
    scanner: {
      label: "Alpha Scanner",
      tip: "Ranking MD real multi-mercado.",
    },
    simulator: {
      label: "Simulador",
      tip: "Comparar mercados × monedas × leverage.",
    },
    strategies: {
      label: "Estrategias",
      tip: "Guías del catálogo (antes en el Simulador).",
    },
    guided_lab: { label: "Guided Lab", tip: "Wizard paper/demo." },
    montecarlo: { label: "Monte Carlo", tip: "Estrés estadístico." },
    backtest: { label: "Backtest", tip: "Velas sintéticas." },
  };

  function loadFavorites() {
    try {
      var raw = localStorage.getItem(FAV_STORAGE_KEY);
      if (!raw) {
        /* migrar v1 si existía, anteponiendo Chat IA */
        var legacy = localStorage.getItem("ql_menu_favorites");
        if (legacy) {
          var old = JSON.parse(legacy);
          if (Array.isArray(old) && old.length) {
            var merged = old.filter(function (id) {
              return !!openers[id];
            });
            if (merged.indexOf("chat") < 0 && openers.chat) {
              merged.unshift("chat");
            }
            if (merged.length) {
              saveFavorites(merged);
              return merged;
            }
          }
        }
      } else {
        var arr = JSON.parse(raw);
        if (Array.isArray(arr) && arr.length) {
          return arr.filter(function (id) {
            return !!openers[id];
          });
        }
      }
    } catch (e) {}
    return FAV_DEFAULT.slice();
  }

  function saveFavorites(ids) {
    try {
      localStorage.setItem(FAV_STORAGE_KEY, JSON.stringify(ids));
    } catch (e) {}
  }

  function renderFavoritesMenu() {
    var box = document.getElementById("ql-fav-list");
    if (!box) return;
    var ids = loadFavorites();
    box.innerHTML = ids
      .map(function (id, idx) {
        var meta = FAV_META[id] || { label: id, tip: id };
        return (
          '<div class="ql-fav-row" data-fav="' +
          id +
          '">' +
          '<button type="button" class="ql-fav-open" data-open="' +
          id +
          '" data-tip="' +
          meta.tip +
          '">' +
          meta.label +
          "</button>" +
          '<span class="ql-fav-moves">' +
          '<button type="button" class="ql-fav-up" data-i="' +
          idx +
          '" title="Subir"' +
          (idx === 0 ? " disabled" : "") +
          ">↑</button>" +
          '<button type="button" class="ql-fav-down" data-i="' +
          idx +
          '" title="Bajar"' +
          (idx === ids.length - 1 ? " disabled" : "") +
          ">↓</button>" +
          "</span></div>"
        );
      })
      .join("");
    box.querySelectorAll(".ql-fav-open").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var key = btn.getAttribute("data-open");
        if (openers[key]) openers[key]();
      });
    });
    box.querySelectorAll(".ql-fav-up").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var i = Number(btn.getAttribute("data-i"));
        if (i <= 0) return;
        var cur = loadFavorites();
        var t = cur[i - 1];
        cur[i - 1] = cur[i];
        cur[i] = t;
        saveFavorites(cur);
        renderFavoritesMenu();
      });
    });
    box.querySelectorAll(".ql-fav-down").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var i = Number(btn.getAttribute("data-i"));
        var cur = loadFavorites();
        if (i >= cur.length - 1) return;
        var t = cur[i + 1];
        cur[i + 1] = cur[i];
        cur[i] = t;
        saveFavorites(cur);
        renderFavoritesMenu();
      });
    });
  }

  var favReset = document.getElementById("ql-fav-reset");
  if (favReset) {
    favReset.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      saveFavorites(FAV_DEFAULT.slice());
      renderFavoritesMenu();
    });
  }
  renderFavoritesMenu();

  // Clicks dentro del menú no deben cerrarlo (seguir abriendo paneles).
  startMenu.addEventListener("click", function (ev) {
    ev.stopPropagation();
  });

  startMenu.querySelectorAll("[data-open]").forEach(function (btn) {
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      const key = btn.getAttribute("data-open");
      if (key === "about") {
        openAbout();
        return;
      }
      if (openers[key]) openers[key]();
      // Menú QL permanece abierto para seguir navegando.
    });
  });

  startMenu.querySelectorAll("[data-wm-action]").forEach(function (btn) {
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      const action = btn.getAttribute("data-wm-action");
      if (action === "minimize_all" && wm.minimizeAll) {
        wm.minimizeAll();
      } else if (action === "restore_all" && wm.restoreAll) {
        wm.restoreAll();
      } else if (action === "cascade_windows" && wm.cascadeWindows) {
        wm.cascadeWindows();
      } else if (action === "tile_windows" && wm.tileWindows) {
        wm.tileWindows();
      } else if (action === "bring_to_front" && wm.bringToFront) {
        wm.bringToFront();
      } else if (action === "send_to_back" && wm.sendToBack) {
        wm.sendToBack();
      } else if (action === "maximize_window" && wm.maximize) {
        wm.maximize();
      } else if (action === "restore_from_maximize" && wm.restoreFromMaximize) {
        wm.restoreFromMaximize();
      }
      // Acciones de ventanas: menú sigue abierto.
    });
  });

  if (sbVersion) {
    sbVersion.addEventListener("click", function (ev) {
      ev.stopPropagation();
      openAbout();
    });
  }

  function applyWorkspacePreset(name) {
    if (!QLApi || !QLApi.applyPreset || !name) return;
    QLApi.applyPreset(name)
      .then(function (payload) {
        if (!payload || !payload.ok || !payload.layout) return;
        const windows = payload.layout.windows || {};
        // Merge geom del preset sin borrar ventanas ya abiertas.
        Object.keys(windows).forEach(function (id) {
          savedGeom[id] = windows[id];
        });
        const ids =
          (payload.preset && payload.preset.window_ids) || Object.keys(windows);
        ids.forEach(function (id) {
          if (openers[id]) openers[id]();
        });
      })
      .catch(function () {});
  }

  const customPresetsHost = document.getElementById("custom-presets");
  const btnPresetSave = document.getElementById("btn-preset-save");

  function renderCustomPresets(presets) {
    if (!customPresetsHost) return;
    customPresetsHost.innerHTML = "";
    const customs = (presets || []).filter(function (p) {
      return p && p.custom === true;
    });
    if (!customs.length) return;
    const group = document.createElement("div");
    group.className = "start-group";
    group.setAttribute("data-i18n", "preset.custom_group");
    group.textContent =
      (window.QLi18n && QLi18n.t && QLi18n.t("preset.custom_group")) || "Custom";
    customPresetsHost.appendChild(group);
    customs.forEach(function (p) {
      const row = document.createElement("div");
      row.className = "custom-preset-row";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("data-preset", p.name);
      btn.setAttribute("data-custom-preset", "1");
      btn.setAttribute(
        "data-tip",
        (p.description || p.name) +
          "\nPreset personalizado — abrí este layout guardado."
      );
      btn.textContent = p.label || p.name;
      const del = document.createElement("button");
      del.type = "button";
      del.className = "preset-delete";
      del.setAttribute("data-preset-delete", p.name);
      del.setAttribute(
        "data-tip",
        "Eliminar este preset personalizado.\nNo borra ventanas abiertas ahora."
      );
      del.setAttribute(
        "aria-label",
        ((window.QLi18n && QLi18n.t && QLi18n.t("preset.delete")) || "Delete") +
          " " +
          (p.label || p.name)
      );
      del.title =
        (window.QLi18n && QLi18n.t && QLi18n.t("preset.delete_title")) ||
        "Delete custom preset";
      del.textContent = "×";
      row.appendChild(btn);
      row.appendChild(del);
      customPresetsHost.appendChild(row);
    });
  }

  function refreshPresetsMenu() {
    if (!QLApi || !QLApi.getPresets) return;
    QLApi.getPresets()
      .then(function (payload) {
        if (!payload || !payload.ok) return;
        renderCustomPresets(payload.presets || []);
      })
      .catch(function () {});
  }

  function saveCurrentAsPreset() {
    if (!QLApi || !QLApi.savePreset) return;
    const promptMsg =
      (window.QLi18n && QLi18n.t && QLi18n.t("preset.save_prompt")) ||
      "Custom preset name:";
    const raw = window.prompt(promptMsg, "");
    if (raw === null) return;
    const name = String(raw || "").trim();
    if (!name) return;
    QLApi.savePreset(name)
      .then(function (payload) {
        if (!payload || !payload.ok) return;
        refreshPresetsMenu();
      })
      .catch(function () {});
  }

  function deleteCustomPreset(name) {
    if (!QLApi || !QLApi.deletePreset || !name) return;
    const confirmMsg =
      (window.QLi18n && QLi18n.t && QLi18n.t("preset.delete_confirm")) ||
      "Delete custom preset?";
    if (!window.confirm(confirmMsg + "\n" + name)) return;
    QLApi.deletePreset(name)
      .then(function (payload) {
        if (!payload || !payload.ok) return;
        refreshPresetsMenu();
      })
      .catch(function () {});
  }

  startMenu.querySelectorAll("[data-preset]").forEach(function (btn) {
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      const name = btn.getAttribute("data-preset");
      // No cerrar menú: el preset ahora suma ventanas, no reemplaza.
      applyWorkspacePreset(name);
    });
  });

  if (customPresetsHost) {
    customPresetsHost.addEventListener("click", function (ev) {
      const delBtn =
        ev.target && ev.target.closest
          ? ev.target.closest("[data-preset-delete]")
          : null;
      if (delBtn && customPresetsHost.contains(delBtn)) {
        ev.preventDefault();
        ev.stopPropagation();
        const delName = delBtn.getAttribute("data-preset-delete");
        deleteCustomPreset(delName);
        return;
      }
      const btn = ev.target && ev.target.closest
        ? ev.target.closest("[data-preset]")
        : null;
      if (!btn || !customPresetsHost.contains(btn)) return;
      ev.preventDefault();
      ev.stopPropagation();
      const name = btn.getAttribute("data-preset");
      applyWorkspacePreset(name);
    });
  }

  if (btnPresetSave) {
    btnPresetSave.addEventListener("click", function (ev) {
      ev.stopPropagation();
      saveCurrentAsPreset();
    });
  }

  document.addEventListener("click", function (ev) {
    if (!isStartMenuOpen()) return;
    var t = ev.target;
    if (startMenu && startMenu.contains(t)) return;
    if (startBtn && (t === startBtn || startBtn.contains(t))) return;
    if (brandEl && (t === brandEl || brandEl.contains(t))) return;
    closeStartMenu();
  });

  refreshPresetsMenu();

  function setClockTimezone(tz) {
    /* F74: status bar clock · UTC (default) | local */
    clockTimezone = tz === "local" ? "local" : "UTC";
    tickClock();
  }

  function updateHeartbeatStatus(payload) {
    if (!sbHeartbeat) return;
    let label = "—";
    let cls = "mono sb-heartbeat";
    if (payload) {
      const st = payload.status || payload.heartbeat;
      if (st === "ok") {
        label = "ok";
        cls += " ok";
      } else if (st === "disconnected") {
        label = "disconnected";
        cls += " fail";
      } else {
        label = "fail";
        cls += " fail";
      }
      if (
        typeof payload.poll_seconds === "number" &&
        payload.poll_seconds > 0 &&
        payload.poll_seconds !== heartbeatPollSeconds
      ) {
        heartbeatPollSeconds = payload.poll_seconds;
        restartHeartbeatPoll();
      }
    }
    sbHeartbeat.textContent = label;
    sbHeartbeat.className = cls;
  }

  function pollBrokerHeartbeat() {
    if (!QLApi || !QLApi.brokerHeartbeat) return;
    QLApi.brokerHeartbeat()
      .then(updateHeartbeatStatus)
      .catch(function () {
        updateHeartbeatStatus({ status: "fail", heartbeat: "fail" });
      });
  }

  function restartHeartbeatPoll() {
    if (heartbeatTimer != null) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
    const ms = Math.max(1, Number(heartbeatPollSeconds) || 5) * 1000;
    heartbeatTimer = setInterval(pollBrokerHeartbeat, ms);
  }

  function tickClock() {
    if (!clockEl) return;
    const now = new Date();
    const loc =
      window.QLi18n && QLi18n.getLocale && QLi18n.getLocale() === "en"
        ? "en-US"
        : "es-AR";
    const opts = {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    };
    if (clockTimezone === "UTC") {
      opts.timeZone = "UTC";
      clockEl.textContent = now.toLocaleTimeString(loc, opts) + " UTC";
    } else {
      clockEl.textContent = now.toLocaleTimeString(loc, opts);
    }
  }
  tickClock();
  setInterval(tickClock, 1000);

  /* F75: broker heartbeat poll every N seconds */
  pollBrokerHeartbeat();
  restartHeartbeatPoll();

  // F60: aplicar i18n default es antes del boot async
  applyLocale("es");

  // Boot: banner + layout + settings + ventanas default
  QLApi.getMode()
    .then(updateBanner)
    .catch(function () {
      bannerMode.textContent = "modo ?";
    });

  refreshVersionBadge();

  Promise.all([
    QLApi.session().catch(function () {
      return null;
    }),
    QLApi.getLayout().catch(function () {
      return null;
    }),
    QLApi.getSettings().catch(function () {
      return null;
    }),
    QLApi.getOnboarding
      ? QLApi.getOnboarding().catch(function () {
          return null;
        })
      : Promise.resolve(null),
  ]).then(function (results) {
    const sessionData = results[0];
    const layoutData = results[1];
    const settingsData = results[2];
    const onboardingData = results[3];
    if (sessionData) {
      const sid =
        (sessionData.session && sessionData.session.session_id) ||
        sessionData.session_id ||
        "?";
      cachedSessionId = sid;
      if (bannerSession) bannerSession.textContent = "session " + sid;
      updateStatusBar({
        mode: sessionData.mode || sessionMode,
        live_blocked: sessionData.live_blocked !== false,
        session_id: sid,
        venue: sessionData.connected_venue || sessionData.venue,
        md_provider: sessionData.md_provider,
      });
    } else if (bannerSession) {
      bannerSession.textContent = "session ?";
    }
    if (layoutData && layoutData.layout && layoutData.layout.windows) {
      savedGeom = layoutData.layout.windows;
    }
    if (settingsData && settingsData.settings) {
      applyTheme(settingsData.settings.theme);
      applyLocale(settingsData.settings.locale || "es");
      if (window.QLToasts && QLToasts.setDesktopNotifications) {
        QLToasts.setDesktopNotifications(
          settingsData.settings.desktop_notifications === true
        );
      }
      if (window.QLToasts && QLToasts.setSoundAlerts) {
        QLToasts.setSoundAlerts(settingsData.settings.sound_alerts === true);
      }
      setClockTimezone(settingsData.settings.timezone);
      if (settingsData.settings.ui_font_scale != null) {
        applyFontScale(settingsData.settings.ui_font_scale, false);
      }
      updateStatusBar(settingsData);
      // Opcional: hidratar mensajes desde API (parity static JSON)
      if (QLApi.getI18n) {
        QLApi.getI18n(settingsData.settings.locale || "es")
          .then(function (payload) {
            if (payload && payload.messages && window.QLi18n) {
              QLi18n.mergeMessages(payload.locale || "es", payload.messages);
              QLi18n.applyDom(document);
            }
          })
          .catch(function () {});
      }
    }
    openHealth();
    openMarket();
    openBlotter();
    openSimRegistry();

    // F37: first-run wizard si meta.onboarding_done ausente
    if (
      onboardingData &&
      onboardingData.show_wizard &&
      !onboardingData.onboarding_done &&
      window.QLOnboarding
    ) {
      const wizard = window.QLOnboarding.create({
        "open-market": openMarket,
        "open-paper": openPaperSession,
        "open-backtest": openBacktest,
        "open-chat": openChat,
      });
      wizard.show();
    }
  });
})();
