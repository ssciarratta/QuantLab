/** Helpers compartidos para paneles lab. */
(function (global) {
  "use strict";

  function preJson(obj) {
    return (
      '<pre class="lab-json mono">' +
      escapeHtml(JSON.stringify(obj, null, 2)) +
      "</pre>"
    );
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function setStatus(el, ok, msg) {
    el.textContent = msg;
    el.className = "mono " + (ok ? "status-ok" : "status-bad");
  }

  function isAbortError(err) {
    if (!err) return false;
    if (err.name === "AbortError") return true;
    var msg = String(err.message || err);
    return /abort/i.test(msg);
  }

  /**
   * @param {function(AbortSignal|null): Promise} runner
   * @param {object} [opts] kind, label, summary, stopSel, kinds, renderJson
   */
  function bindRun(root, btnSel, statusSel, outSel, runner, opts) {
    opts = opts || {};
    const btn = root.querySelector(btnSel);
    const status = root.querySelector(statusSel);
    const out = root.querySelector(outSel);
    var stopBtn = opts.stopSel ? root.querySelector(opts.stopSel) : null;
    if (stopBtn && global.QLRunGate) {
      QLRunGate.bindStopButton(stopBtn, {
        kinds: opts.kinds || (opts.kind ? [opts.kind] : null),
      });
    }
    if (global.QLRunGate && opts.busyHost !== false) {
      QLRunGate.bindBusyHost(root, {
        kinds: opts.kinds || (opts.kind ? [opts.kind] : null),
      });
    }
    btn.addEventListener("click", function () {
      var gateP =
        global.QLRunGate && opts.gate !== false
          ? QLRunGate.begin({
              kind: opts.kind || "lab_run",
              label: opts.label || "Corrida",
              summary:
                typeof opts.summary === "function"
                  ? opts.summary(root)
                  : opts.summary || "",
              busyRoot: root,
            })
          : Promise.resolve({
              signal: null,
              end: function () {},
              setProgress: function () {},
            });
      gateP.then(function (handle) {
        if (!handle) return;
        status.textContent = "ejecutando…";
        status.className = "mono muted";
        var p;
        try {
          p = runner(handle.signal || null, handle);
        } catch (e) {
          handle.end();
          setStatus(status, false, e.message || String(e));
          return;
        }
        Promise.resolve(p)
          .then(function (data) {
            setStatus(status, true, "OK");
            if (opts.renderJson !== false && out) {
              out.innerHTML = preJson(data);
            }
            return data;
          })
          .catch(function (err) {
            if (isAbortError(err)) {
              setStatus(status, false, "detenido");
            } else {
              setStatus(status, false, err.message || String(err));
            }
            if (out) out.innerHTML = "";
          })
          .then(function () {
            handle.end();
          });
      });
    });
  }

  /** Formato numérico UI — siempre 2 decimales (es-AR). */
  function num(v, digits) {
    if (v == null || v === "") return "—";
    var n = typeof v === "number" ? v : Number(v);
    if (!isFinite(n)) return escapeHtml(v);
    var d = digits == null ? 2 : digits;
    return n.toLocaleString("es-AR", {
      minimumFractionDigits: d,
      maximumFractionDigits: d,
    });
  }

  function pct(v) {
    if (v == null || v === "") return "—";
    var n = typeof v === "number" ? v : Number(v);
    if (!isFinite(n)) return escapeHtml(v);
    return num(n, 2) + "%";
  }

  global.QLLabUI = {
    preJson: preJson,
    escapeHtml: escapeHtml,
    setStatus: setStatus,
    bindRun: bindRun,
    isAbortError: isAbortError,
  };
  global.QLFmt = { num: num, pct: pct, money: num };
})(window);
