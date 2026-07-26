/** Shell del escritorio QuantLab Workbench. */
(function () {
  "use strict";

  const workspace = document.getElementById("workspace");
  const taskbarWindows = document.getElementById("taskbar-windows");
  const bannerMode = document.getElementById("banner-mode");
  const bannerLive = document.getElementById("banner-live");
  const clockEl = document.getElementById("taskbar-clock");
  const startBtn = document.getElementById("btn-start");
  const startMenu = document.getElementById("start-menu");

  let sessionMode = "tester";

  const wm = new QLWindowManager(workspace, taskbarWindows);

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
    wm.open("health", "Salud / Modo", pane, { x: 24, y: 20, w: 440, h: 360 });
    pane.refresh().catch(function () {});
  }

  function openMarket() {
    const pane = QLPanes.createMarketPane(function () {
      return sessionMode;
    });
    wm.open("market", "Market Data", pane, { x: 360, y: 40, w: 460, h: 400 });
    pane.refresh().catch(function () {});
  }

  function openBlotter() {
    const pane = QLPanes.createBlotterPane();
    wm.open("blotter", "Paper Blotter", pane, { x: 120, y: 120, w: 520, h: 360 });
    pane.refresh().catch(function () {});
  }

  const openers = {
    health: openHealth,
    market: openMarket,
    blotter: openBlotter,
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

  // Boot: banner + 3 ventanas
  QLApi.getMode()
    .then(updateBanner)
    .catch(function () {
      bannerMode.textContent = "modo ?";
    })
    .finally(function () {
      openHealth();
      openMarket();
      openBlotter();
    });
})();
