/** Toast notifications — success / error (F41) + desktop Notification (F72) + WebAudio beep (F73). */
(function (global) {
  "use strict";

  const MAX_VISIBLE = 4;
  const DEFAULT_MS = 4200;
  let desktopEnabled = false;
  let soundEnabled = false;
  let audioCtx = null;

  function ensureHost() {
    let host = document.getElementById("ql-toast-host");
    if (host) return host;
    host = document.createElement("div");
    host.id = "ql-toast-host";
    host.className = "ql-toast-host";
    host.setAttribute("aria-live", "polite");
    host.setAttribute("aria-relevant", "additions");
    document.body.appendChild(host);
    return host;
  }

  function desktopNotify(title, body) {
    if (!desktopEnabled) return;
    if (typeof Notification === "undefined") return;
    if (Notification.permission !== "granted") return;
    try {
      new Notification(String(title || "QuantLab"), {
        body: String(body || ""),
        tag: "quantlab-workbench",
      });
    } catch (err) {
      /* graceful: Notification denied / insecure context / unsupported */
    }
  }

  function requestPermissionIfNeeded() {
    if (!desktopEnabled) return;
    if (typeof Notification === "undefined") return;
    if (Notification.permission !== "default") return;
    try {
      var maybe = Notification.requestPermission();
      if (maybe && typeof maybe.then === "function") {
        maybe.catch(function () {});
      }
    } catch (err) {
      /* graceful */
    }
  }

  function setDesktopNotifications(enabled) {
    desktopEnabled = !!enabled;
    if (desktopEnabled) requestPermissionIfNeeded();
  }

  function ensureAudioCtx() {
    if (audioCtx) return audioCtx;
    var AC = global.AudioContext || global.webkitAudioContext;
    if (typeof AC !== "function") return null;
    try {
      audioCtx = new AC();
    } catch (err) {
      return null;
    }
    return audioCtx;
  }

  /** Short WebAudio beep — no external assets (F73). */
  function playBeep() {
    if (!soundEnabled) return;
    var ctx = ensureAudioCtx();
    if (!ctx) return;
    try {
      if (ctx.state === "suspended" && typeof ctx.resume === "function") {
        ctx.resume().catch(function () {});
      }
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 880;
      gain.gain.value = 0.0001;
      osc.connect(gain);
      gain.connect(ctx.destination);
      var t0 = ctx.currentTime;
      gain.gain.setValueAtTime(0.0001, t0);
      gain.gain.exponentialRampToValueAtTime(0.12, t0 + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.12);
      osc.start(t0);
      osc.stop(t0 + 0.14);
      osc.onended = function () {
        try {
          osc.disconnect();
          gain.disconnect();
        } catch (err2) {
          /* ignore */
        }
      };
    } catch (err) {
      /* graceful: AutoplayPolicy / unsupported */
    }
  }

  function setSoundAlerts(enabled) {
    soundEnabled = !!enabled;
  }

  function show(kind, message, opts) {
    const host = ensureHost();
    const ms = (opts && opts.ms) || DEFAULT_MS;
    const el = document.createElement("div");
    el.className = "ql-toast ql-toast--" + (kind === "error" ? "error" : "ok");
    el.setAttribute("role", "status");
    const label = kind === "error" ? "Error" : "OK";
    el.innerHTML =
      '<span class="ql-toast-kind">' +
      label +
      "</span>" +
      '<span class="ql-toast-msg"></span>';
    el.querySelector(".ql-toast-msg").textContent = String(message || "");
    host.appendChild(el);
    while (host.children.length > MAX_VISIBLE) {
      host.removeChild(host.firstChild);
    }
    requestAnimationFrame(function () {
      el.classList.add("ql-toast--in");
    });
    const timer = setTimeout(function () {
      el.classList.remove("ql-toast--in");
      el.classList.add("ql-toast--out");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 280);
    }, ms);
    el.addEventListener("click", function () {
      clearTimeout(timer);
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    if (kind === "error") {
      desktopNotify("QuantLab · Error", message);
      playBeep();
    }
    return el;
  }

  global.QLToasts = {
    success: function (message, opts) {
      return show("ok", message, opts);
    },
    error: function (message, opts) {
      return show("error", message, opts);
    },
    show: show,
    setDesktopNotifications: setDesktopNotifications,
    setSoundAlerts: setSoundAlerts,
    desktopEnabled: function () {
      return desktopEnabled;
    },
    soundEnabled: function () {
      return soundEnabled;
    },
    notifyKillEngage: function (detail) {
      desktopNotify(
        "QuantLab · Kill Switch",
        detail || "Paper kill ENGAGED"
      );
      playBeep();
    },
    desktopNotify: desktopNotify,
    playBeep: playBeep,
  };
})(window);
