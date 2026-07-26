/** Command Palette — Ctrl+K / Ctrl+Shift+P (F35); a11y focus trap (F59). */
(function (global) {
  "use strict";

  var FOCUSABLE =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
    'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function CommandPalette(opts) {
    this.openers = opts.openers || {};
    this.wm = opts.wm;
    this.onHealthRefresh = typeof opts.onHealthRefresh === "function" ? opts.onHealthRefresh : null;
    this.commands = [];
    this.filtered = [];
    this.activeIdx = 0;
    this.visible = false;
    this._el = null;
    this._input = null;
    this._list = null;
    this._prevFocus = null;
    this._onKeyDown = null;
    this._buildDom();
  }

  CommandPalette.prototype._focusables = function () {
    if (!this._el) return [];
    return Array.prototype.slice.call(this._el.querySelectorAll(FOCUSABLE)).filter(function (el) {
      return el.offsetParent !== null || el === document.activeElement;
    });
  };

  CommandPalette.prototype._trapFocus = function (ev) {
    if (!this.visible || ev.key !== "Tab") return;
    var nodes = this._focusables();
    if (!nodes.length) {
      ev.preventDefault();
      if (this._input) this._input.focus();
      return;
    }
    var first = nodes[0];
    var last = nodes[nodes.length - 1];
    if (ev.shiftKey) {
      if (document.activeElement === first || !this._el.contains(document.activeElement)) {
        ev.preventDefault();
        last.focus();
      }
    } else if (document.activeElement === last) {
      ev.preventDefault();
      first.focus();
    }
  };

  CommandPalette.prototype._buildDom = function () {
    var overlay = document.getElementById("command-palette");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "command-palette";
      overlay.className = "command-palette hidden";
      overlay.setAttribute("hidden", "");
      document.body.appendChild(overlay);
    }
    overlay.className = "command-palette hidden";
    overlay.setAttribute("hidden", "");
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Command Palette");
    if (!overlay.querySelector(".command-palette-panel")) {
      overlay.innerHTML =
        '<div class="command-palette-panel">' +
        '<div class="command-palette-header">' +
        "<span>Command Palette</span>" +
        '<span class="command-palette-hint">Ctrl+K · Esc</span>' +
        "</div>" +
        '<input type="search" class="command-palette-input" id="command-palette-input" ' +
        'placeholder="Buscar panel o acción…" autocomplete="off" spellcheck="false" ' +
        'aria-label="Buscar comando" />' +
        '<ul class="command-palette-list" id="command-palette-list" role="listbox" ' +
        'aria-label="Resultados"></ul>' +
        '<div class="command-palette-footer">' +
        "<span>↑↓ navegar · Enter ejecutar · Esc cerrar</span>" +
        '<span class="mono muted">LIVE_BLOCKED</span>' +
        "</div>" +
        "</div>";
    }
    this._el = overlay;
    this._input = overlay.querySelector("#command-palette-input");
    this._list = overlay.querySelector("#command-palette-list");

    const self = this;
    overlay.addEventListener("click", function (ev) {
      if (ev.target === overlay) self.hide();
    });
    this._input.addEventListener("input", function () {
      self._filter(self._input.value);
    });
    this._input.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        self._move(1);
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        self._move(-1);
      } else if (ev.key === "Enter") {
        ev.preventDefault();
        self._runActive();
      } else if (ev.key === "Escape") {
        ev.preventDefault();
        self.hide();
      }
    });
    this._onKeyDown = function (ev) {
      self._trapFocus(ev);
    };
  };

  CommandPalette.prototype.load = function () {
    const self = this;
    if (!QLApi || !QLApi.commands) {
      return Promise.resolve([]);
    }
    return QLApi.commands()
      .then(function (data) {
        self.commands = (data && data.commands) || [];
        return self.commands;
      })
      .catch(function () {
        self.commands = [];
        return self.commands;
      });
  };

  CommandPalette.prototype.show = function () {
    const self = this;
    const open = function () {
      self._prevFocus = document.activeElement;
      self.visible = true;
      self._el.removeAttribute("hidden");
      self._el.classList.remove("hidden");
      self._input.value = "";
      self._filter("");
      self._input.focus();
      self._input.select();
      document.addEventListener("keydown", self._onKeyDown, true);
    };
    if (!this.commands.length) {
      this.load().then(open);
    } else {
      open();
    }
  };

  CommandPalette.prototype.hide = function () {
    this.visible = false;
    this._el.setAttribute("hidden", "");
    this._el.classList.add("hidden");
    if (this._onKeyDown) {
      document.removeEventListener("keydown", this._onKeyDown, true);
    }
    if (this._prevFocus && typeof this._prevFocus.focus === "function") {
      try {
        this._prevFocus.focus();
      } catch (err) {
        /* ignore */
      }
    }
    this._prevFocus = null;
  };

  CommandPalette.prototype.toggle = function () {
    if (this.visible) this.hide();
    else this.show();
  };

  CommandPalette.prototype.isOpen = function () {
    return this.visible;
  };

  CommandPalette.prototype._score = function (cmd, q) {
    if (!q) return 1;
    const hay =
      (cmd.label || "") +
      " " +
      (cmd.id || "") +
      " " +
      (cmd.pane_id || "") +
      " " +
      (cmd.action || "") +
      " " +
      ((cmd.keywords || []).join(" "));
    const lower = hay.toLowerCase();
    const terms = q.toLowerCase().trim().split(/\s+/);
    let score = 0;
    for (let i = 0; i < terms.length; i++) {
      const t = terms[i];
      if (!t) continue;
      if (lower.indexOf(t) < 0) return 0;
      score += 10;
      if ((cmd.label || "").toLowerCase().indexOf(t) === 0) score += 5;
      if ((cmd.id || "").toLowerCase().indexOf(t) >= 0) score += 3;
    }
    return score;
  };

  CommandPalette.prototype._filter = function (query) {
    const q = (query || "").trim();
    const scored = [];
    for (let i = 0; i < this.commands.length; i++) {
      const cmd = this.commands[i];
      const s = this._score(cmd, q);
      if (s > 0) scored.push({ cmd: cmd, score: s });
    }
    scored.sort(function (a, b) {
      return b.score - a.score;
    });
    this.filtered = scored.map(function (x) {
      return x.cmd;
    });
    this.activeIdx = 0;
    this._render();
  };

  CommandPalette.prototype._render = function () {
    const self = this;
    this._list.innerHTML = "";
    if (!this.filtered.length) {
      const empty = document.createElement("li");
      empty.className = "command-palette-empty";
      empty.textContent = "Sin resultados";
      this._list.appendChild(empty);
      return;
    }
    this.filtered.forEach(function (cmd, idx) {
      const li = document.createElement("li");
      li.className = "command-palette-item" + (idx === self.activeIdx ? " active" : "");
      li.setAttribute("role", "option");
      li.dataset.idx = String(idx);
      const kind = cmd.kind === "action" ? "acción" : "panel";
      const shortcut = cmd.shortcut ? '<span class="command-palette-keys">' + cmd.shortcut + "</span>" : "";
      li.innerHTML =
        '<span class="command-palette-label">' +
        (cmd.label || cmd.id) +
        "</span>" +
        '<span class="command-palette-meta">' +
        kind +
        "</span>" +
        shortcut;
      li.addEventListener("mousedown", function (ev) {
        ev.preventDefault();
        self.activeIdx = idx;
        self._runActive();
      });
      self._list.appendChild(li);
    });
  };

  CommandPalette.prototype._move = function (delta) {
    if (!this.filtered.length) return;
    this.activeIdx = (this.activeIdx + delta + this.filtered.length) % this.filtered.length;
    this._render();
    const active = this._list.querySelector(".command-palette-item.active");
    if (active && active.scrollIntoView) active.scrollIntoView({ block: "nearest" });
  };

  CommandPalette.prototype._runActive = function () {
    const cmd = this.filtered[this.activeIdx];
    if (!cmd) return;
    this.hide();
    this.execute(cmd);
  };

  CommandPalette.prototype.execute = function (cmd) {
    if (!cmd) return;
    if (cmd.kind === "pane" && cmd.pane_id && this.openers[cmd.pane_id]) {
      this.openers[cmd.pane_id]();
      return;
    }
    if (cmd.kind === "action") {
      if (cmd.action === "health_refresh") {
        if (this.openers.health) this.openers.health();
        if (this.onHealthRefresh) this.onHealthRefresh();
        else if (QLApi && QLApi.health) QLApi.health().catch(function () {});
        return;
      }
      if (cmd.action === "close_focused" && this.wm && this.wm.closeFocused) {
        this.wm.closeFocused();
        return;
      }
      if (cmd.action === "minimize_all" && this.wm && this.wm.minimizeAll) {
        this.wm.minimizeAll();
        return;
      }
      if (cmd.action === "restore_all" && this.wm && this.wm.restoreAll) {
        this.wm.restoreAll();
      }
    }
  };

  global.QLCommandPalette = CommandPalette;
})(window);
