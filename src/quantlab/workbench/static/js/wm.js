/** Window manager MDI — ventanas arrastrables / redimensionables. */
(function (global) {
  "use strict";

  let zCounter = 10;

  function WindowManager(workspaceEl, taskbarEl) {
    this.workspace = workspaceEl;
    this.taskbar = taskbarEl;
    this.windows = new Map();
  }

  WindowManager.prototype.open = function (id, title, contentEl, opts) {
    opts = opts || {};
    if (this.windows.has(id)) {
      this.focus(id);
      const existing = this.windows.get(id);
      if (existing.el.classList.contains("minimized")) {
        this.restore(id);
      }
      return existing;
    }

    const win = document.createElement("div");
    win.className = "win";
    win.dataset.id = id;
    win.style.left = (opts.x != null ? opts.x : 40) + "px";
    win.style.top = (opts.y != null ? opts.y : 40) + "px";
    win.style.width = (opts.w != null ? opts.w : 420) + "px";
    win.style.height = (opts.h != null ? opts.h : 320) + "px";

    const titlebar = document.createElement("div");
    titlebar.className = "win-titlebar";
    const titleSpan = document.createElement("span");
    titleSpan.className = "win-title";
    titleSpan.textContent = title;
    const controls = document.createElement("div");
    controls.className = "win-controls";
    const btnMin = document.createElement("button");
    btnMin.type = "button";
    btnMin.title = "Minimizar";
    btnMin.textContent = "—";
    const btnClose = document.createElement("button");
    btnClose.type = "button";
    btnClose.className = "btn-close";
    btnClose.title = "Cerrar";
    btnClose.textContent = "×";
    controls.appendChild(btnMin);
    controls.appendChild(btnClose);
    titlebar.appendChild(titleSpan);
    titlebar.appendChild(controls);

    const body = document.createElement("div");
    body.className = "win-body";
    if (contentEl) {
      body.appendChild(contentEl);
    }

    const resize = document.createElement("div");
    resize.className = "win-resize";

    win.appendChild(titlebar);
    win.appendChild(body);
    win.appendChild(resize);
    this.workspace.appendChild(win);

    const taskBtn = document.createElement("button");
    taskBtn.type = "button";
    taskBtn.className = "task-btn";
    taskBtn.textContent = title;
    taskBtn.dataset.id = id;
    this.taskbar.appendChild(taskBtn);

    const record = {
      id: id,
      title: title,
      el: win,
      body: body,
      taskBtn: taskBtn,
    };
    this.windows.set(id, record);

    const self = this;
    titlebar.addEventListener("mousedown", function (ev) {
      if (ev.target.closest(".win-controls")) return;
      self._startDrag(win, ev);
    });
    resize.addEventListener("mousedown", function (ev) {
      self._startResize(win, ev);
    });
    win.addEventListener("mousedown", function () {
      self.focus(id);
    });
    btnMin.addEventListener("click", function (ev) {
      ev.stopPropagation();
      self.minimize(id);
    });
    btnClose.addEventListener("click", function (ev) {
      ev.stopPropagation();
      self.close(id);
    });
    taskBtn.addEventListener("click", function () {
      if (win.classList.contains("minimized")) {
        self.restore(id);
      } else if (win.classList.contains("focused")) {
        self.minimize(id);
      } else {
        self.focus(id);
      }
    });

    requestAnimationFrame(function () {
      win.classList.add("open");
    });
    this.focus(id);
    taskBtn.classList.add("flash");
    setTimeout(function () {
      taskBtn.classList.remove("flash");
    }, 450);
    return record;
  };

  WindowManager.prototype.focus = function (id) {
    const rec = this.windows.get(id);
    if (!rec) return;
    zCounter += 1;
    rec.el.style.zIndex = String(zCounter);
    this.windows.forEach(function (w) {
      w.el.classList.remove("focused");
      w.taskBtn.classList.remove("active");
    });
    rec.el.classList.add("focused");
    rec.taskBtn.classList.add("active");
  };

  WindowManager.prototype.minimize = function (id) {
    const rec = this.windows.get(id);
    if (!rec) return;
    rec.el.classList.add("minimized");
    rec.el.classList.remove("focused");
    rec.taskBtn.classList.remove("active");
  };

  WindowManager.prototype.restore = function (id) {
    const rec = this.windows.get(id);
    if (!rec) return;
    rec.el.classList.remove("minimized");
    this.focus(id);
  };

  WindowManager.prototype.close = function (id) {
    const rec = this.windows.get(id);
    if (!rec) return;
    rec.el.remove();
    rec.taskBtn.remove();
    this.windows.delete(id);
  };

  WindowManager.prototype._startDrag = function (win, ev) {
    ev.preventDefault();
    const startX = ev.clientX;
    const startY = ev.clientY;
    const origL = win.offsetLeft;
    const origT = win.offsetTop;
    const workspace = this.workspace;

    function onMove(e) {
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      let nl = origL + dx;
      let nt = origT + dy;
      const maxL = Math.max(0, workspace.clientWidth - 80);
      const maxT = Math.max(0, workspace.clientHeight - 40);
      nl = Math.max(-20, Math.min(nl, maxL));
      nt = Math.max(0, Math.min(nt, maxT));
      win.style.left = nl + "px";
      win.style.top = nt + "px";
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  WindowManager.prototype._startResize = function (win, ev) {
    ev.preventDefault();
    ev.stopPropagation();
    const startX = ev.clientX;
    const startY = ev.clientY;
    const origW = win.offsetWidth;
    const origH = win.offsetHeight;

    function onMove(e) {
      const nw = Math.max(280, origW + (e.clientX - startX));
      const nh = Math.max(180, origH + (e.clientY - startY));
      win.style.width = nw + "px";
      win.style.height = nh + "px";
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  global.QLWindowManager = WindowManager;
})(window);
