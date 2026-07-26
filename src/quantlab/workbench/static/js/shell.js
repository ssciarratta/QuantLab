/** Shell del escritorio QuantLab Workbench. */
(function () {
  "use strict";

  const workspace = document.getElementById("workspace");
  const taskbarWindows = document.getElementById("taskbar-windows");
  const bannerMode = document.getElementById("banner-mode");
  const bannerLive = document.getElementById("banner-live");
  const bannerSession = document.getElementById("banner-session");
  const clockEl = document.getElementById("sb-clock");
  const startBtn = document.getElementById("btn-start");
  const startMenu = document.getElementById("start-menu");
  const sbMode = document.getElementById("sb-mode");
  const sbLive = document.getElementById("sb-live");
  const sbSession = document.getElementById("sb-session");
  const sbVenue = document.getElementById("sb-venue");
  const sbMd = document.getElementById("sb-md");

  let sessionMode = "tester";
  let savedGeom = {};
  let cachedSessionId = "—";

  const wm = new QLWindowManager(workspace, taskbarWindows);

  wm.setLayoutChangeHandler(function (layout) {
    if (!QLApi || !QLApi.putLayout) return;
    QLApi.putLayout(layout).catch(function () {});
  });

  function mergeOpts(id, defaults) {
    const g = savedGeom[id];
    if (!g) return defaults;
    return {
      x: g.x != null ? g.x : defaults.x,
      y: g.y != null ? g.y : defaults.y,
      w: g.w != null ? g.w : defaults.w,
      h: g.h != null ? g.h : defaults.h,
      minimized: !!g.minimized,
    };
  }

  function applyTheme(theme) {
    const t = theme === "high-contrast" ? "high-contrast" : "slate";
    document.documentElement.setAttribute("data-theme", t);
    document.body.setAttribute("data-theme", t);
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
    wm.open("health", "Salud / Modo", pane, mergeOpts("health", { x: 24, y: 20, w: 440, h: 360 }));
    pane.refresh().catch(function () {});
  }

  function openMarket() {
    const pane = QLPanes.createMarketPane(function () {
      return sessionMode;
    });
    wm.open("market", "Market Data", pane, mergeOpts("market", { x: 360, y: 40, w: 460, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openUniverse() {
    const pane = QLPanes.createUniversePane();
    wm.open("universe", "Universe", pane, mergeOpts("universe", { x: 40, y: 60, w: 480, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openCatalog() {
    const pane = QLPanes.createCatalogPane();
    wm.open("catalog", "Data Catalog", pane, mergeOpts("catalog", { x: 80, y: 80, w: 560, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openBlotter() {
    const pane = QLPanes.createBlotterPane();
    wm.open("blotter", "Paper Blotter", pane, mergeOpts("blotter", { x: 120, y: 120, w: 520, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openJournal() {
    const pane = QLPanes.createJournalPane();
    wm.open("journal", "Journal", pane, mergeOpts("journal", { x: 180, y: 100, w: 560, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openPaperSession() {
    const pane = QLPanes.createPaperSessionPane();
    wm.open(
      "paper_session",
      "Sesión Paper",
      pane,
      mergeOpts("paper_session", { x: 160, y: 90, w: 520, h: 440 })
    );
    pane.refresh().catch(function () {});
  }

  function openPositions() {
    const pane = QLPanes.createPositionsPane();
    wm.open("positions", "Posiciones", pane, mergeOpts("positions", { x: 200, y: 80, w: 480, h: 360 }));
    pane.refresh().catch(function () {});
  }

  function openRisk() {
    const pane = QLPanes.createRiskPane();
    wm.open("risk", "Riesgo", pane, mergeOpts("risk", { x: 240, y: 60, w: 460, h: 380 }));
    pane.refresh().catch(function () {});
  }

  function openBacktest() {
    const pane = QLPanes.createBacktestPane();
    wm.open("backtest", "Backtest", pane, mergeOpts("backtest", { x: 48, y: 48, w: 480, h: 420 }));
  }

  function openScanner() {
    const pane = QLPanes.createScannerPane();
    wm.open("scanner", "Alpha Scanner", pane, mergeOpts("scanner", { x: 80, y: 60, w: 460, h: 400 }));
  }

  function openMetrics() {
    const pane = QLPanes.createMetricsPane();
    wm.open("metrics", "Metrics / Último", pane, mergeOpts("metrics", { x: 100, y: 80, w: 480, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openReports() {
    const pane = QLPanes.createReportsPane();
    wm.open("reports", "Reports", pane, mergeOpts("reports", { x: 110, y: 70, w: 560, h: 460 }));
    pane.refresh().catch(function () {});
  }

  function openExperiments() {
    const pane = QLPanes.createExperimentsPane();
    wm.open(
      "experiments",
      "Experiments",
      pane,
      mergeOpts("experiments", { x: 120, y: 90, w: 480, h: 380 })
    );
    pane.refresh().catch(function () {});
  }

  function openOptimize() {
    const pane = QLPanes.createOptimizePane();
    wm.open("optimize", "Optimizer", pane, mergeOpts("optimize", { x: 140, y: 70, w: 560, h: 520 }));
  }

  function openMonteCarlo() {
    const pane = QLPanes.createMonteCarloPane();
    wm.open(
      "montecarlo",
      "Monte Carlo",
      pane,
      mergeOpts("montecarlo", { x: 160, y: 100, w: 460, h: 380 })
    );
  }

  function openFeatures() {
    const pane = QLPanes.createFeaturesPane();
    wm.open("features", "Features", pane, mergeOpts("features", { x: 180, y: 110, w: 520, h: 460 }));
  }

  function openExportHb() {
    const pane = QLPanes.createExportHbPane();
    wm.open(
      "export_hb",
      "Hummingbot Export",
      pane,
      mergeOpts("export_hb", { x: 200, y: 90, w: 460, h: 360 })
    );
  }

  function openValidation() {
    const pane = QLPanes.createValidationPane();
    wm.open(
      "validation",
      "Validation Splits",
      pane,
      mergeOpts("validation", { x: 220, y: 80, w: 480, h: 400 })
    );
    pane.refresh().catch(function () {});
  }

  function openChat() {
    const pane = QLPanes.createChatPane();
    wm.open("chat", "Chat IA", pane, mergeOpts("chat", { x: 260, y: 40, w: 440, h: 460 }));
    pane.refresh().catch(function () {});
  }

  function openSettings() {
    const pane = QLPanes.createSettingsPane(function (data) {
      updateStatusBar(data);
      if (data && data.settings) applyTheme(data.settings.theme);
    });
    wm.open("settings", "Settings", pane, mergeOpts("settings", { x: 280, y: 60, w: 440, h: 420 }));
    pane.refresh().catch(function () {});
  }

  function openDocs() {
    const pane = QLPanes.createDocsPane();
    wm.open("docs", "Help / Docs", pane, mergeOpts("docs", { x: 200, y: 50, w: 560, h: 480 }));
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
    chat: openChat,
    settings: openSettings,
    docs: openDocs,
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

    if (ctrl && (key === "w" || key === "W")) {
      if (isTypingTarget(ev.target) && !ev.target.closest(".win")) return;
      ev.preventDefault();
      wm.closeFocused();
      return;
    }

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
    ev.stopPropagation();
    const open = startMenu.hasAttribute("hidden");
    if (open) {
      startMenu.removeAttribute("hidden");
      startMenu.classList.remove("hidden");
      startBtn.classList.add("active");
    } else {
      startMenu.setAttribute("hidden", "");
      startMenu.classList.add("hidden");
      startBtn.classList.remove("active");
    }
  });

  startMenu.querySelectorAll("[data-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const key = btn.getAttribute("data-open");
      if (openers[key]) openers[key]();
      startMenu.setAttribute("hidden", "");
      startMenu.classList.add("hidden");
      startBtn.classList.remove("active");
    });
  });

  document.addEventListener("click", function () {
    startMenu.setAttribute("hidden", "");
    startMenu.classList.add("hidden");
    startBtn.classList.remove("active");
  });

  function tickClock() {
    if (!clockEl) return;
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("es-AR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
  tickClock();
  setInterval(tickClock, 1000);

  // Boot: banner + layout + settings + ventanas default
  QLApi.getMode()
    .then(updateBanner)
    .catch(function () {
      bannerMode.textContent = "modo ?";
    });

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
      updateStatusBar(settingsData);
    }
    openHealth();
    openMarket();
    openBlotter();

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
