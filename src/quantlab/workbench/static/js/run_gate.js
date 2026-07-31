/** Coordinador global de corridas lab (Sim / Ranking / MC / Scanner / …). */
(function (global) {
  "use strict";

  var active = null;
  var queue = null;
  var seq = 0;
  var listeners = [];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function notify() {
    listeners.forEach(function (fn) {
      try {
        fn(snapshot());
      } catch (e) {}
    });
  }

  function snapshot() {
    return {
      busy: !!active,
      active: active
        ? {
            id: active.id,
            kind: active.kind,
            label: active.label,
            summary: active.summary,
          }
        : null,
      queued: queue
        ? { kind: queue.kind, label: queue.label, summary: queue.summary }
        : null,
    };
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
      '<p class="muted" style="font-size:0.78em">¿Qué querés hacer?</p>' +
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
    active = null;
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
    active = null;
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
    active = {
      id: id,
      kind: spec.kind || "run",
      label: spec.label || spec.kind || "Corrida",
      summary: spec.summary || "",
      controller: controller,
      onCancel: spec.onCancel || null,
      startedAt: Date.now(),
    };
    notify();
    return Promise.resolve({
      id: id,
      kind: active.kind,
      label: active.label,
      summary: active.summary,
      signal: controller ? controller.signal : null,
      end: function () {
        endActive(id);
      },
      stop: function () {
        if (active && active.id === id) stopActive();
      },
    });
  }

  /**
   * Pide permiso para iniciar una corrida.
   * @returns {Promise<object|null>} handle con signal/end, o null si el usuario cancela.
   */
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
      // cut
      stopActive();
      return beginInternal(spec);
    });
  }

  function stop() {
    var had = stopActive();
    // Si había alguien esperando, arranca esa corrida (Stop = cortar actual).
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

  /** Helper: monta/ sincroniza un botón Stop en un panel. */
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

  global.QLRunGate = {
    begin: begin,
    end: endActive,
    stop: stop,
    isBusy: isBusy,
    current: current,
    snapshot: snapshot,
    onChange: onChange,
    bindStopButton: bindStopButton,
  };
})(window);
