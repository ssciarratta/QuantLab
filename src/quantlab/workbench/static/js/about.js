/** About dialog (F45) — modal read-only; sin LIVE. */
(function (global) {
  "use strict";

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createOverlay() {
    var overlay = document.getElementById("about-dialog");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "about-dialog";
      overlay.className = "about-dialog hidden";
      overlay.setAttribute("hidden", "");
      document.body.appendChild(overlay);
    }
    overlay.className = "about-dialog hidden";
    overlay.setAttribute("hidden", "");
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Acerca de QuantLab");
    if (!overlay.querySelector(".about-panel")) {
      overlay.innerHTML =
        '<div class="about-panel">' +
        '  <header class="about-header">' +
        '    <div class="about-brand">QuantLab</div>' +
        '    <button type="button" class="btn ghost about-close" id="about-close" aria-label="Cerrar">×</button>' +
        "  </header>" +
        '  <div class="about-body" id="about-body">' +
        '    <p class="muted">Cargando…</p>' +
        "  </div>" +
        '  <footer class="about-footer">' +
        '    <span class="live-badge" id="about-live">LIVE_BLOCKED</span>' +
        '    <button type="button" class="btn primary" id="about-ok" aria-label="Cerrar Acerca de">Cerrar</button>' +
        "  </footer>" +
        "</div>";
    }
    return overlay;
  }

  function renderBody(data) {
    var bp = (data && data.bind_policy) || {};
    var blocked = !data || data.live_blocked !== false;
    return (
      "<h2>Acerca de</h2>" +
      '<p class="about-lead">' +
      escapeHtml((data && data.name) || "QuantLab Workbench") +
      "</p>" +
      '<dl class="about-dl">' +
      "<dt>Versión</dt><dd class=\"mono\">" +
      escapeHtml((data && data.version) || "?") +
      "</dd>" +
      "<dt>Fases</dt><dd>" +
      escapeHtml((data && data.phases_summary) || "—") +
      "</dd>" +
      "<dt>Python</dt><dd class=\"mono\">" +
      escapeHtml((data && data.python_version) || "?") +
      "</dd>" +
      "<dt>Bind</dt><dd class=\"mono\">" +
      escapeHtml(bp.policy || "—") +
      "</dd>" +
      "<dt>Bind detail</dt><dd class=\"muted about-bind\">" +
      escapeHtml(bp.summary || "—") +
      "</dd>" +
      "<dt>Paper kill</dt><dd class=\"mono\">" +
      escapeHtml(String(data && data.paper_kill_engaged === true)) +
      "</dd>" +
      "<dt>Auto-backup (min)</dt><dd class=\"mono\">" +
      escapeHtml(
        String(
          data && data.auto_backup_minutes != null ? data.auto_backup_minutes : 0
        )
      ) +
      "</dd>" +
      "<dt>Access log</dt><dd class=\"mono\">" +
      escapeHtml(String(!(data && data.access_log === false))) +
      "</dd>" +
      "</dl>" +
      '<p class="muted about-note">Research-safe · REAL ≠ LIVE · ' +
      (blocked ? "LIVE_BLOCKED" : "LIVE_UNLOCKED") +
      '</p>' +
      '<p class="about-api-link"><a href="/api/openapi.json" target="_blank" rel="noopener">API (OpenAPI)</a></p>'
    );
  }

  function AboutDialog() {
    this._el = createOverlay();
    this._body = this._el.querySelector("#about-body");
    this._live = this._el.querySelector("#about-live");
    var self = this;
    function close() {
      self.hide();
    }
    this._el.querySelector("#about-close").addEventListener("click", close);
    this._el.querySelector("#about-ok").addEventListener("click", close);
    this._el.addEventListener("click", function (ev) {
      if (ev.target === self._el) close();
    });
  }

  AboutDialog.prototype.show = function () {
    var self = this;
    this._el.removeAttribute("hidden");
    this._el.classList.remove("hidden");
    this._body.innerHTML = '<p class="muted">Cargando…</p>';
    var fetchAbout =
      global.QLApi && global.QLApi.about
        ? global.QLApi.about()
        : Promise.reject(new Error("QLApi.about ausente"));
    return fetchAbout
      .then(function (data) {
        self._body.innerHTML = renderBody(data);
        if (self._live) {
          var blocked = !data || data.live_blocked !== false;
          self._live.textContent = blocked ? "LIVE_BLOCKED" : "LIVE_UNLOCKED";
          self._live.classList.toggle("unlocked", !blocked);
        }
        return data;
      })
      .catch(function (err) {
        self._body.innerHTML =
          '<p class="muted">No se pudo cargar About: ' +
          escapeHtml(err && err.message ? err.message : err) +
          "</p>";
      });
  };

  AboutDialog.prototype.hide = function () {
    this._el.setAttribute("hidden", "");
    this._el.classList.add("hidden");
  };

  AboutDialog.prototype.isOpen = function () {
    return !this._el.hasAttribute("hidden");
  };

  var singleton = null;

  function getDialog() {
    if (!singleton) singleton = new AboutDialog();
    return singleton;
  }

  global.QLAbout = {
    open: function () {
      return getDialog().show();
    },
    close: function () {
      if (singleton) singleton.hide();
    },
    isOpen: function () {
      return singleton ? singleton.isOpen() : false;
    },
  };
})(window);
