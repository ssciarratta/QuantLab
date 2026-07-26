/** Shell del escritorio QuantLab Workbench. */
(function () {
  "use strict";

  const workspace = document.getElementById("workspace");
  const taskbarWindows = document.getElementById("taskbar-windows");
  const bannerMode = document.getElementById("banner-mode");
  const bannerLive = document.getElementById("banner-live");
  const bannerSession = document.getElementById("banner-session");
  const clockEl = document.getElementById("taskbar-clock");
  const startBtn = document.getElementById("btn-start");
  const startMenu = document.getElementById("start-menu");

  let sessionMode = "tester";
  let savedGeom = {};

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
    wm.open("optimize", "Optimizer", pane, mergeOpts("optimize", { x: 140, y: 70, w: 460, h: 380 }));
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
    wm.open("features", "Features", pane, mergeOpts("features", { x: 180, y: 110, w: 460, h: 380 }));
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

  const openers = {
    health: openHealth,
    market: openMarket,
    blotter: openBlotter,
    journal: openJournal,
    paper_session: openPaperSession,
    positions: openPositions,
    risk: openRisk,
    chat: openChat,
    backtest: openBacktest,
    scanner: openScanner,
    metrics: openMetrics,
    experiments: openExperiments,
    optimize: openOptimize,
    montecarlo: openMonteCarlo,
    features: openFeatures,
    export_hb: openExportHb,
    validation: openValidation,
  };

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
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("es-AR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
  tickClock();
  setInterval(tickClock, 1000);

  // Boot: banner + layout restore + ventanas default
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
  ]).then(function (results) {
    const sessionData = results[0];
    const layoutData = results[1];
    if (sessionData) {
      const sid =
        (sessionData.session && sessionData.session.session_id) ||
        sessionData.session_id ||
        "?";
      if (bannerSession) bannerSession.textContent = "session " + sid;
    } else if (bannerSession) {
      bannerSession.textContent = "session ?";
    }
    if (layoutData && layoutData.layout && layoutData.layout.windows) {
      savedGeom = layoutData.layout.windows;
    }
    openHealth();
    openMarket();
    openBlotter();
  });
})();
