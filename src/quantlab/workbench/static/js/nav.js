/** Navegación / deep-link entre paneles del Workbench (Scan → BT → MC). */
(function (global) {
  "use strict";

  var pending = {};

  function setFocus(paneId, payload) {
    if (!paneId) return;
    pending[String(paneId)] = payload || {};
  }

  function takeFocus(paneId) {
    var key = String(paneId || "");
    if (!Object.prototype.hasOwnProperty.call(pending, key)) return null;
    var p = pending[key];
    delete pending[key];
    return p;
  }

  function peekFocus(paneId) {
    return pending[String(paneId)] || null;
  }

  function paneRoot(paneId) {
    var win = document.querySelector('.win[data-id="' + paneId + '"]');
    if (!win) return null;
    var body = win.querySelector(".win-body");
    return body ? body.firstElementChild : null;
  }

  /**
   * Abre (o enfoca) un panel y aplica payload de deep-link.
   * Requiere QLShell.open que acepte (paneId, opts).
   */
  function open(paneId, opts) {
    opts = opts || {};
    if (opts.focus || opts.focusId || opts.prefill) {
      setFocus(paneId, {
        focusId: opts.focusId || (opts.focus && opts.focus.id) || null,
        focus: opts.focus || null,
        prefill: opts.prefill || null,
        message: opts.message || null,
      });
    }
    var ok = false;
    if (global.QLShell && typeof global.QLShell.open === "function") {
      ok = !!global.QLShell.open(paneId, opts);
    }
    var root = paneRoot(paneId);
    if (root && typeof root.applyNavFocus === "function") {
      try {
        root.applyNavFocus();
      } catch (e) {
        /* ignore */
      }
    } else if (root && typeof root.refresh === "function") {
      try {
        var p = root.refresh();
        if (p && typeof p.then === "function") {
          p.then(function () {
            if (typeof root.applyNavFocus === "function") root.applyNavFocus();
          });
        }
      } catch (e2) {
        /* ignore */
      }
    }
    return ok;
  }

  global.QLNav = {
    setFocus: setFocus,
    takeFocus: takeFocus,
    peekFocus: peekFocus,
    paneRoot: paneRoot,
    open: open,
  };
})(window);
