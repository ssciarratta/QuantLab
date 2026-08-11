/** Coordinador global de corridas lab (Sim / Ranking / MC / Scanner / …). */
(function (global) {
  "use strict";

  var active = null;
  var queue = null;
  var seq = 0;
  var listeners = [];
  var elapsedTimer = null;
  var progressPct = null; // null = indeterminado

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatElapsed(ms) {
    var s = Math.max(0, Math.floor(ms / 1000));
    var m = Math.floor(s / 60);
    s = s % 60;
    return m > 0 ? m + ":" + (s < 10 ? "0" : "") + s : s + "s";
  }

  function notify() {
    listeners.forEach(function (fn) {
      try {
        fn(snapshot());
      } catch (e) {}
    });
    syncBusyChrome();
  }

  function snapshot() {
    return {
      busy: !!active,
      progress: progressPct,
      elapsed_ms: active ? Date.now() - active.startedAt : 0,
      active: active
        ? {
            id: active.id,
            kind: active.kind,
            label: active.label,
            summary: active.summary,
            startedAt: active.startedAt,
          }
        : null,
      queued: queue
        ? { kind: queue.kind, label: queue.label, summary: queue.summary }
        : null,
    };
  }

  function ensureBusyBanner() {
    var el = document.getElementById("ql-run-busy");
    if (el) return el;
    el = document.createElement("div");
    el.id = "ql-run-busy";
    el.className = "ql-run-busy";
    el.hidden = true;
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.innerHTML =
      '<div class="ql-run-busy-inner">' +
      '<span class="ql-hourglass" aria-hidden="true">⏳</span>' +
      '<div class="ql-run-busy-text">' +
      '<span class="ql-run-busy-title mono" id="ql-run-busy-title">Procesando…</span>' +
      '<span class="ql-run-busy-elapsed mono muted" id="ql-run-busy-elapsed">0s</span>' +
      "</div>" +
      '<div class="ql-run-busy-bar-wrap" title="Avance">' +
      '<div class="ql-run-busy-bar" id="ql-run-busy-bar"></div>' +
      "</div>" +
      '<span class="ql-run-busy-pct mono muted" id="ql-run-busy-pct" hidden></span>' +
      '<button type="button" class="btn secondary stop-run" id="ql-run-busy-stop">Stop</button>' +
      "</div>";
    var host =
      document.getElementById("workspace") ||
      document.getElementById("app") ||
      document.body;
    if (host.firstChild) host.insertBefore(el, host.firstChild);
    else host.appendChild(el);
    var stopBtn = el.querySelector("#ql-run-busy-stop");
    if (stopBtn) {
      stopBtn.addEventListener("click", function () {
        stop();
      });
    }
    return el;
  }

  function stopElapsedTick() {
    if (elapsedTimer) {
      clearInterval(elapsedTimer);
      elapsedTimer = null;
    }
  }

  function startElapsedTick() {
    stopElapsedTick();
    elapsedTimer = setInterval(function () {
      if (!active) {
        stopElapsedTick();
        return;
      }
      var el = document.getElementById("ql-run-busy-elapsed");
      if (el) el.textContent = formatElapsed(Date.now() - active.startedAt);
      var sbEl = document.getElementById("sb-run-gate-elapsed");
      if (sbEl) sbEl.textContent = formatElapsed(Date.now() - active.startedAt);
    }, 250);
  }

  function applyProgressToBars(pct) {
    var bar = document.getElementById("ql-run-busy-bar");
    var pctEl = document.getElementById("ql-run-busy-pct");
    var sbBar = document.getElementById("sb-run-gate-bar");
    var determinate = pct != null && isFinite(pct);
    var w = determinate ? Math.max(0, Math.min(100, Number(pct))) : null;
    if (bar) {
      bar.classList.toggle("indeterminate", !determinate);
      if (determinate) {
        bar.style.width = w + "%";
      } else {
        bar.style.width = "";
      }
    }
    if (pctEl) {
      if (determinate) {
        pctEl.hidden = false;
        pctEl.textContent = Math.round(w) + "%";
      } else {
        pctEl.hidden = true;
        pctEl.textContent = "";
      }
    }
    if (sbBar) {
      sbBar.classList.toggle("indeterminate", !determinate);
      if (determinate) sbBar.style.width = w + "%";
      else sbBar.style.width = "";
    }
  }

  function syncBusyChrome() {
    var banner = ensureBusyBanner();
    var snap = snapshot();
    try {
      document.body.classList.toggle("ql-is-busy", !!snap.busy);
    } catch (e) {}
    if (!snap.busy) {
      banner.hidden = true;
      stopElapsedTick();
      progressPct = null;
      applyProgressToBars(null);
      return;
    }
    /* Solo status bar (#sb-run-gate): el banner en workspace tapaba titlebars WM. */
    banner.hidden = true;
    var a = snap.active || {};
    var title =
      (a.label || a.kind || "Corrida") +
      (a.summary ? " · " + a.summary : "");
    var titleEl = banner.querySelector("#ql-run-busy-title");
    if (titleEl) {
      titleEl.textContent = "Procesando · " + title;
      titleEl.title = title;
    }
    var elapsedEl = banner.querySelector("#ql-run-busy-elapsed");
    if (elapsedEl) {
      elapsedEl.textContent = formatElapsed(snap.elapsed_ms || 0);
    }
    applyProgressToBars(progressPct);
    startElapsedTick();
  }

  function setProgress(pct) {
    if (pct == null || pct === "") {
      progressPct = null;
    } else {
      var n = Number(pct);
      progressPct = isFinite(n) ? Math.max(0, Math.min(100, n)) : null;
    }
    applyProgressToBars(progressPct);
    listeners.forEach(function (fn) {
      try {
        fn(snapshot());
      } catch (e) {}
    });
  }

  function ensureModal() {
    var el = document.getElementById("ql-run-gate-modal");
    if (el) return el;
    el = document.createElement("div");
    el.id = "ql-run-gate-modal";
    el.className = "ql-run-gate-modal";
    el.hidden = true;
    el.innerHTML =
      '<div class="ql-run-gate-backdrop" data-act="cancel"></div>' +
      '<div class="ql-run-gate-card" role="dialog" aria-modal="true" aria-labelledby="ql-run-gate-title">' +
      '<h3 id="ql-run-gate-title">Corrida en curso</h3>' +
      '<p class="ql-run-gate-current mono" id="ql-run-gate-current"></p>' +
      '<p class="muted" id="ql-run-gate-new-label">Nueva corrida:</p>' +
      '<p class="ql-run-gate-next mono" id="ql-run-gate-next"></p>' +
      '<p class="muted" style="font-size:1.08em">¿Qué querés hacer?</p>' +
      '<div class="ql-run-gate-actions">' +
      '<button type="button" class="btn secondary" data-act="wait">Esperar a que termine la anterior</button>' +
      '<button type="button" class="btn" data-act="cut">Cortar la anterior y correr esta</button>' +
      '<button type="button" class="btn secondary" data-act="cancel">Cancelar</button>' +
      "</div></div>";
    document.body.appendChild(el);
    return el;
  }

  function askConflict(currentSpec, nextSpec) {
    return new Promise(function (resolve) {
      var modal = ensureModal();
      var curEl = modal.querySelector("#ql-run-gate-current");
      var nextEl = modal.querySelector("#ql-run-gate-next");
      curEl.textContent =
        (currentSpec.label || currentSpec.kind || "corrida") +
        (currentSpec.summary ? " · " + currentSpec.summary : "");
      nextEl.textContent =
        (nextSpec.label || nextSpec.kind || "nueva") +
        (nextSpec.summary ? " · " + nextSpec.summary : "");
      modal.hidden = false;

      function done(act) {
        modal.hidden = true;
        modal.querySelectorAll("[data-act]").forEach(function (btn) {
          btn.onclick = null;
        });
        resolve(act);
      }

      modal.querySelectorAll("[data-act]").forEach(function (btn) {
        btn.onclick = function (ev) {
          ev.preventDefault();
          done(btn.getAttribute("data-act") || "cancel");
        };
      });
    });
  }

  function endActive(id) {
    if (!active) return;
    if (id != null && active.id !== id) return;
    if (active.busyRoot) mountLocalBusy(active.busyRoot, false);
    active = null;
    progressPct = null;
    notify();
    if (queue) {
      var q = queue;
      queue = null;
      beginInternal(q.spec).then(function (handle) {
        if (handle && typeof q.resolve === "function") q.resolve(handle);
        else if (typeof q.resolve === "function") q.resolve(null);
      });
    }
  }

  function stopActive() {
    if (!active) return false;
    var cur = active;
    try {
      if (cur.controller && typeof cur.controller.abort === "function") {
        cur.controller.abort();
      }
    } catch (e) {}
    try {
      if (typeof cur.onCancel === "function") cur.onCancel();
    } catch (e2) {}
    if (cur.busyRoot) mountLocalBusy(cur.busyRoot, false);
    active = null;
    progressPct = null;
    notify();
    return true;
  }

  function beginInternal(spec) {
    spec = spec || {};
    if (active) {
      return Promise.resolve(null);
    }
    seq += 1;
    var id = "run-" + seq;
    var controller =
      typeof AbortController !== "undefined" ? new AbortController() : null;
    progressPct = null;
    active = {
      id: id,
      kind: spec.kind || "run",
      label: spec.label || spec.kind || "Corrida",
      summary: spec.summary || "",
      controller: controller,
      onCancel: spec.onCancel || null,
      startedAt: Date.now(),
      busyRoot: spec.busyRoot || null,
    };
    notify();
    if (spec.busyRoot) mountLocalBusy(spec.busyRoot, true);
    return Promise.resolve({
      id: id,
      kind: active.kind,
      label: active.label,
      summary: active.summary,
      signal: controller ? controller.signal : null,
      setProgress: setProgress,
      end: function () {
        if (spec.busyRoot) mountLocalBusy(spec.busyRoot, false);
        endActive(id);
      },
      stop: function () {
        if (active && active.id === id) stopActive();
      },
    });
  }

  function mountLocalBusy(root, on) {
    if (!root || !root.querySelector) return;
    var strip = root.querySelector(".ql-pane-busy");
    if (on) {
      if (!strip) {
        strip = document.createElement("div");
        strip.className = "ql-pane-busy";
        strip.innerHTML =
          '<span class="ql-hourglass" aria-hidden="true">⏳</span>' +
          '<div class="ql-pane-busy-bar-wrap"><div class="ql-pane-busy-bar indeterminate"></div></div>' +
          '<span class="mono muted ql-pane-busy-label">procesando…</span>';
        if (root.firstChild) root.insertBefore(strip, root.firstChild);
        else root.appendChild(strip);
      }
      strip.hidden = false;
      root.classList.add("ql-pane-is-busy");
    } else if (strip) {
      strip.hidden = true;
      root.classList.remove("ql-pane-is-busy");
    }
  }

  function begin(spec) {
    spec = spec || {};
    if (!active) {
      return beginInternal(spec);
    }
    return askConflict(
      {
        kind: active.kind,
        label: active.label,
        summary: active.summary,
      },
      spec
    ).then(function (act) {
      if (act === "cancel" || !act) return null;
      if (act === "wait") {
        return new Promise(function (resolve) {
          queue = { spec: spec, resolve: resolve };
          notify();
        });
      }
      stopActive();
      return beginInternal(spec);
    });
  }

  function stop() {
    var had = stopActive();
    if (queue) {
      var q = queue;
      queue = null;
      notify();
      beginInternal(q.spec).then(function (handle) {
        if (typeof q.resolve === "function") q.resolve(handle);
      });
      return had;
    }
    notify();
    return had;
  }

  function isBusy() {
    return !!active;
  }

  function current() {
    return snapshot().active;
  }

  function onChange(fn) {
    if (typeof fn === "function") listeners.push(fn);
    return function () {
      listeners = listeners.filter(function (x) {
        return x !== fn;
      });
    };
  }

  function bindStopButton(btn, opts) {
    opts = opts || {};
    if (!btn) return function () {};
    function sync() {
      var snap = snapshot();
      var mine =
        snap.busy &&
        (!opts.kinds ||
          opts.kinds.indexOf(snap.active && snap.active.kind) >= 0);
      btn.hidden = !mine;
      btn.disabled = !mine;
      if (mine && snap.active) {
        btn.title =
          "Detener: " +
          (snap.active.label || "") +
          (snap.active.summary ? " · " + snap.active.summary : "");
      } else {
        btn.title = "Stop · sin corrida activa de este panel";
      }
    }
    btn.addEventListener("click", function () {
      stop();
      if (typeof opts.onStop === "function") opts.onStop();
    });
    var off = onChange(sync);
    sync();
    return off;
  }

  function bindBusyHost(root, opts) {
    opts = opts || {};
    if (!root) return function () {};
    function sync() {
      var snap = snapshot();
      var mine =
        snap.busy &&
        (!opts.kinds ||
          opts.kinds.indexOf(snap.active && snap.active.kind) >= 0);
      mountLocalBusy(root, !!mine);
      var label = root.querySelector(".ql-pane-busy-label");
      if (label && mine && snap.active) {
        label.textContent =
          "procesando · " +
          (snap.active.label || "") +
          (snap.progress != null
            ? " · " + Math.round(snap.progress) + "%"
            : "…");
      }
      var bar = root.querySelector(".ql-pane-busy-bar");
      if (bar) {
        var det = snap.progress != null && isFinite(snap.progress);
        bar.classList.toggle("indeterminate", !det);
        if (det) bar.style.width = snap.progress + "%";
        else bar.style.width = "";
      }
    }
    var off = onChange(sync);
    sync();
    return off;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      ensureBusyBanner();
    });
  } else {
    ensureBusyBanner();
  }

  global.QLRunGate = {
    begin: begin,
    end: endActive,
    stop: stop,
    isBusy: isBusy,
    current: current,
    snapshot: snapshot,
    onChange: onChange,
    setProgress: setProgress,
    bindStopButton: bindStopButton,
    bindBusyHost: bindBusyHost,
  };
})(window);
