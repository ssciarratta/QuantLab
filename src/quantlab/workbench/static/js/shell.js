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
  const sbHeartbeat = document.getElementById("sb-heartbeat");
  const sbVersion = document.getElementById("sb-version");

  let sessionMode = "tester";
  let savedGeom = {};
  let cachedSessionId = "—";
  let cachedVersion = null;
  let clockTimezone = "UTC"; /* F74: settings.timezone UTC|local */
  let heartbeatPollSeconds = 5; /* F75: N seconds · GET /api/broker/heartbeat */
  let heartbeatTimer = null;

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
      minimized: !!g.minimized,
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

  function openBacktest() {
    const pane = QLPanes.createBacktestPane();
    wm.open("backtest", tr("pane.backtest", "Backtest"), pane, mergeOpts("backtest", { x: 48, y: 48, w: 480, h: 420 }));
  }

  function openScanner() {
    const pane = QLPanes.createScannerPane();
    wm.open("scanner", tr("pane.scanner", "Alpha Scanner"), pane, mergeOpts("scanner", { x: 80, y: 60, w: 460, h: 400 }));
  }

  function openMetrics() {
    const pane = QLPanes.createMetricsPane();
    wm.open("metrics", tr("pane.metrics", "Metrics / Último"), pane, mergeOpts("metrics", { x: 100, y: 80, w: 480, h: 400 }));
    pane.refresh().catch(function () {});
  }

  function openReports() {
    const pane = QLPanes.createReportsPane();
    wm.open("reports", tr("pane.reports", "Reports"), pane, mergeOpts("reports", { x: 110, y: 70, w: 560, h: 460 }));
    pane.refresh().catch(function () {});
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
    wm.open("optimize", tr("pane.optimize", "Optimizer"), pane, mergeOpts("optimize", { x: 140, y: 70, w: 560, h: 520 }));
  }

  function openMonteCarlo() {
    const pane = QLPanes.createMonteCarloPane();
    wm.open(
      "montecarlo",
      tr("pane.montecarlo", "Monte Carlo"),
      pane,
      mergeOpts("montecarlo", { x: 160, y: 100, w: 460, h: 380 })
    );
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
      if (typeof refreshPresetsMenu === "function") {
        refreshPresetsMenu();
      }
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

  startMenu.querySelectorAll("[data-wm-action]").forEach(function (btn) {
    btn.addEventListener("click", function () {
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
      }
      startMenu.setAttribute("hidden", "");
      startMenu.classList.add("hidden");
      startBtn.classList.remove("active");
    });
  });

  if (sbVersion) {
    sbVersion.addEventListener("click", function (ev) {
      ev.stopPropagation();
      openAbout();
    });
  }

  function closeStartMenu() {
    startMenu.setAttribute("hidden", "");
    startMenu.classList.add("hidden");
    startBtn.classList.remove("active");
  }

  function applyWorkspacePreset(name) {
    if (!QLApi || !QLApi.applyPreset || !name) return;
    QLApi.applyPreset(name)
      .then(function (payload) {
        if (!payload || !payload.ok || !payload.layout) return;
        const windows = payload.layout.windows || {};
        savedGeom = windows;
        if (wm.closeAll) {
          wm.closeAll({ silent: true });
        }
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
      btn.title = p.description || p.name;
      btn.textContent = p.label || p.name;
      const del = document.createElement("button");
      del.type = "button";
      del.className = "preset-delete";
      del.setAttribute("data-preset-delete", p.name);
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
    btn.addEventListener("click", function () {
      const name = btn.getAttribute("data-preset");
      closeStartMenu();
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
        ev.stopPropagation();
        const delName = delBtn.getAttribute("data-preset-delete");
        closeStartMenu();
        deleteCustomPreset(delName);
        return;
      }
      const btn = ev.target && ev.target.closest
        ? ev.target.closest("[data-preset]")
        : null;
      if (!btn || !customPresetsHost.contains(btn)) return;
      const name = btn.getAttribute("data-preset");
      closeStartMenu();
      applyWorkspacePreset(name);
    });
  }

  if (btnPresetSave) {
    btnPresetSave.addEventListener("click", function (ev) {
      ev.stopPropagation();
      closeStartMenu();
      saveCurrentAsPreset();
    });
  }

  refreshPresetsMenu();

  document.addEventListener("click", function () {
    closeStartMenu();
  });

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
