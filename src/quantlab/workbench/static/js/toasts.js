/** Toast notifications — success / error (F41) + desktop Notification hook (F72). */
(function (global) {
  "use strict";

  const MAX_VISIBLE = 4;
  const DEFAULT_MS = 4200;
  let desktopEnabled = false;

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
    desktopEnabled: function () {
      return desktopEnabled;
    },
    notifyKillEngage: function (detail) {
      desktopNotify(
        "QuantLab · Kill Switch",
        detail || "Paper kill ENGAGED"
      );
    },
    desktopNotify: desktopNotify,
  };
})(window);
