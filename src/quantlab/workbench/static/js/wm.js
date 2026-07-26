/** Window manager MDI — ventanas arrastrables / redimensionables + layout persist. */
(function (global) {
  "use strict";

  let zCounter = 10;
  const SAVE_DEBOUNCE_MS = 400;
  const SNAP_THRESHOLD_PX = 12;
  const CASCADE_OFFSET_PX = 28;
  const CASCADE_BASE_X = 24;
  const CASCADE_BASE_Y = 24;
  const CASCADE_WIN_W = 420;
  const CASCADE_WIN_H = 320;
  const TILE_GAP_PX = 4;
  const TILE_MARGIN_PX = 4;
  const MIN_WIN_W = 280;
  const MIN_WIN_H = 180;

  /**
   * Snap (x,y) to viewport edges when distance < threshold (F82).
   * Pure geometry — mirrored by quantlab.workbench.snap_position.snap_position.
   * @returns {{x: number, y: number}}
   */
  function snapPosition(x, y, w, h, vw, vh, threshold) {
    let nx = x | 0;
    let ny = y | 0;
    const ww = w | 0;
    const hh = h | 0;
    const viewW = vw | 0;
    const viewH = vh | 0;
    const thr =
      threshold == null || threshold === undefined
        ? SNAP_THRESHOLD_PX
        : Math.max(0, threshold | 0);
    if (nx < thr) {
      nx = 0;
    } else if (viewW - (nx + ww) < thr) {
      nx = viewW - ww;
    }
    if (ny < thr) {
      ny = 0;
    } else if (viewH - (ny + hh) < thr) {
      ny = viewH - hh;
    }
    return { x: nx, y: ny };
  }

  /**
   * Cascade rects for n windows (F84).
   * Pure geometry — mirrored by quantlab.workbench.window_layout.cascade_rects.
   * @returns {Array<{x:number,y:number,w:number,h:number}>}
   */
  function cascadeRects(n, vw, vh, opts) {
    opts = opts || {};
    const count = Math.max(0, n | 0);
    if (count === 0) return [];
    const viewW = Math.max(1, vw | 0);
    const viewH = Math.max(1, vh | 0);
    const step = Math.max(
      1,
      opts.offset != null ? opts.offset | 0 : CASCADE_OFFSET_PX
    );
    const originX = Math.max(
      0,
      opts.baseX != null ? opts.baseX | 0 : CASCADE_BASE_X
    );
    const originY = Math.max(
      0,
      opts.baseY != null ? opts.baseY | 0 : CASCADE_BASE_Y
    );
    const rawW = opts.winW != null ? opts.winW | 0 : CASCADE_WIN_W;
    const rawH = opts.winH != null ? opts.winH | 0 : CASCADE_WIN_H;
    const width = Math.max(MIN_WIN_W, Math.min(rawW, viewW));
    const height = Math.max(MIN_WIN_H, Math.min(rawH, viewH));
    const maxX = Math.max(0, viewW - width);
    const maxY = Math.max(0, viewH - height);
    const wrapX = Math.max(originX, maxX);
    const wrapY = Math.max(originY, maxY);
    const rects = [];
    let cx = originX;
    let cy = originY;
    for (let i = 0; i < count; i++) {
      if (cx > maxX || cy > maxY) {
        cx = originX;
        cy = originY;
      }
      rects.push({ x: cx, y: cy, w: width, h: height });
      cx += step;
      cy += step;
      if (cx > wrapX && cy > wrapY) {
        cx = originX;
        cy = originY;
      }
    }
    return rects;
  }

  /**
   * Tile rects for n windows in a near-square grid (F84).
   * Pure geometry — mirrored by quantlab.workbench.window_layout.tile_rects.
   * @returns {Array<{x:number,y:number,w:number,h:number}>}
   */
  function tileRects(n, vw, vh, opts) {
    opts = opts || {};
    const count = Math.max(0, n | 0);
    if (count === 0) return [];
    const viewW = Math.max(1, vw | 0);
    const viewH = Math.max(1, vh | 0);
    const cellGap = Math.max(
      0,
      opts.gap != null ? opts.gap | 0 : TILE_GAP_PX
    );
    const outer = Math.max(
      0,
      opts.margin != null ? opts.margin | 0 : TILE_MARGIN_PX
    );
    let cols = Math.floor(Math.sqrt(count));
    if (cols * cols < count) cols += 1;
    if (cols < 1) cols = 1;
    const rows = Math.ceil(count / cols);
    const availW = Math.max(1, viewW - 2 * outer - (cols - 1) * cellGap);
    const availH = Math.max(1, viewH - 2 * outer - (rows - 1) * cellGap);
    const cellW = Math.max(1, Math.floor(availW / cols));
    const cellH = Math.max(1, Math.floor(availH / rows));
    const rects = [];
    for (let i = 0; i < count; i++) {
      const row = Math.floor(i / cols);
      const col = i % cols;
      rects.push({
        x: outer + col * (cellW + cellGap),
        y: outer + row * (cellH + cellGap),
        w: cellW,
        h: cellH,
      });
    }
    return rects;
  }

  function WindowManager(workspaceEl, taskbarEl) {
    this.workspace = workspaceEl;
    this.taskbar = taskbarEl;
    this.windows = new Map();
    this.focusedId = null;
    this._onLayoutChange = null;
    this._saveTimer = null;
  }

  WindowManager.prototype.setLayoutChangeHandler = function (fn) {
    this._onLayoutChange = typeof fn === "function" ? fn : null;
  };

  WindowManager.prototype.scheduleSave = function () {
    const self = this;
    if (!self._onLayoutChange) return;
    if (self._saveTimer) clearTimeout(self._saveTimer);
    self._saveTimer = setTimeout(function () {
      self._saveTimer = null;
      try {
        self._onLayoutChange(self.snapshotLayout());
      } catch (err) {
        /* ignore save errors in UI */
      }
    }, SAVE_DEBOUNCE_MS);
  };

  WindowManager.prototype.snapshotLayout = function () {
    const windows = {};
    this.windows.forEach(function (rec) {
      const el = rec.el;
      windows[rec.id] = {
        x: parseInt(el.style.left, 10) || 0,
        y: parseInt(el.style.top, 10) || 0,
        w: el.offsetWidth,
        h: el.offsetHeight,
        minimized: el.classList.contains("minimized"),
        z: parseInt(el.style.zIndex, 10) || 0,
      };
    });
    return { version: 1, windows: windows };
  };

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
    taskBtn.setAttribute("aria-label", "Ventana " + title);
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
      self.scheduleSave();
    });
    btnClose.addEventListener("click", function (ev) {
      ev.stopPropagation();
      self.close(id);
      self.scheduleSave();
    });
    taskBtn.addEventListener("click", function () {
      if (win.classList.contains("minimized")) {
        self.restore(id);
      } else if (win.classList.contains("focused")) {
        self.minimize(id);
      } else {
        self.focus(id);
      }
      self.scheduleSave();
    });

    requestAnimationFrame(function () {
      win.classList.add("open");
    });
    this.focus(id);
    if (opts.minimized) {
      this.minimize(id);
    }
    taskBtn.classList.add("flash");
    setTimeout(function () {
      taskBtn.classList.remove("flash");
    }, 450);
    this.scheduleSave();
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
    this.focusedId = id;
  };

  WindowManager.prototype.minimize = function (id) {
    const rec = this.windows.get(id);
    if (!rec) return;
    rec.el.classList.add("minimized");
    rec.el.classList.remove("focused");
    rec.taskBtn.classList.remove("active");
    if (this.focusedId === id) this.focusedId = null;
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
    const content = rec.body && rec.body.firstElementChild;
    if (content && typeof content.dispose === "function") {
      try {
        content.dispose();
      } catch (err) {
        /* ignore dispose errors */
      }
    }
    rec.el.remove();
    rec.taskBtn.remove();
    this.windows.delete(id);
    if (this.focusedId === id) this.focusedId = null;
  };

  WindowManager.prototype.closeFocused = function () {
    if (!this.focusedId) return false;
    const id = this.focusedId;
    this.close(id);
    this.scheduleSave();
    return true;
  };

  WindowManager.prototype.closeAll = function (opts) {
    opts = opts || {};
    const ids = Array.from(this.windows.keys());
    for (let i = 0; i < ids.length; i++) {
      this.close(ids[i]);
    }
    this.focusedId = null;
    if (!opts.silent) {
      this.scheduleSave();
    }
  };

  /** Minimize every open window and persist layout (F83). */
  WindowManager.prototype.minimizeAll = function (opts) {
    opts = opts || {};
    const ids = Array.from(this.windows.keys());
    for (let i = 0; i < ids.length; i++) {
      this.minimize(ids[i]);
    }
    this.focusedId = null;
    if (!opts.silent) {
      this.scheduleSave();
    }
  };

  /** Restore every minimized window and persist layout (F83). */
  WindowManager.prototype.restoreAll = function (opts) {
    opts = opts || {};
    const ids = Array.from(this.windows.keys());
    for (let i = 0; i < ids.length; i++) {
      const rec = this.windows.get(ids[i]);
      if (rec && rec.el.classList.contains("minimized")) {
        this.restore(ids[i]);
      }
    }
    if (!opts.silent) {
      this.scheduleSave();
    }
  };

  /**
   * Cascade open windows diagonally and persist layout (F84).
   * Restores minimized windows first so geometry is visible.
   */
  WindowManager.prototype.cascadeWindows = function (opts) {
    opts = opts || {};
    const ids = Array.from(this.windows.keys());
    for (let i = 0; i < ids.length; i++) {
      const rec = this.windows.get(ids[i]);
      if (rec && rec.el.classList.contains("minimized")) {
        this.restore(ids[i]);
      }
    }
    const rects = cascadeRects(
      ids.length,
      this.workspace.clientWidth,
      this.workspace.clientHeight,
      opts
    );
    for (let i = 0; i < ids.length; i++) {
      const rec = this.windows.get(ids[i]);
      if (!rec || !rects[i]) continue;
      const r = rects[i];
      rec.el.style.left = r.x + "px";
      rec.el.style.top = r.y + "px";
      rec.el.style.width = r.w + "px";
      rec.el.style.height = r.h + "px";
    }
    if (ids.length) {
      this.focus(ids[ids.length - 1]);
    }
    if (!opts.silent) {
      this.scheduleSave();
    }
  };

  /**
   * Tile open windows in a grid and persist layout (F84).
   * Restores minimized windows first so geometry is visible.
   */
  WindowManager.prototype.tileWindows = function (opts) {
    opts = opts || {};
    const ids = Array.from(this.windows.keys());
    for (let i = 0; i < ids.length; i++) {
      const rec = this.windows.get(ids[i]);
      if (rec && rec.el.classList.contains("minimized")) {
        this.restore(ids[i]);
      }
    }
    const rects = tileRects(
      ids.length,
      this.workspace.clientWidth,
      this.workspace.clientHeight,
      opts
    );
    for (let i = 0; i < ids.length; i++) {
      const rec = this.windows.get(ids[i]);
      if (!rec || !rects[i]) continue;
      const r = rects[i];
      rec.el.style.left = r.x + "px";
      rec.el.style.top = r.y + "px";
      rec.el.style.width = r.w + "px";
      rec.el.style.height = r.h + "px";
    }
    if (ids.length) {
      this.focus(ids[ids.length - 1]);
    }
    if (!opts.silent) {
      this.scheduleSave();
    }
  };

  WindowManager.prototype.getFocusedId = function () {
    return this.focusedId;
  };

  WindowManager.prototype._startDrag = function (win, ev) {
    ev.preventDefault();
    const startX = ev.clientX;
    const startY = ev.clientY;
    const origL = win.offsetLeft;
    const origT = win.offsetTop;
    const workspace = this.workspace;
    const self = this;

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
      const curX = parseInt(win.style.left, 10) || 0;
      const curY = parseInt(win.style.top, 10) || 0;
      const snapped = snapPosition(
        curX,
        curY,
        win.offsetWidth,
        win.offsetHeight,
        workspace.clientWidth,
        workspace.clientHeight,
        SNAP_THRESHOLD_PX
      );
      win.style.left = snapped.x + "px";
      win.style.top = snapped.y + "px";
      self.scheduleSave();
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
    const self = this;

    function onMove(e) {
      const nw = Math.max(280, origW + (e.clientX - startX));
      const nh = Math.max(180, origH + (e.clientY - startY));
      win.style.width = nw + "px";
      win.style.height = nh + "px";
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      self.scheduleSave();
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  WindowManager.snapPosition = snapPosition;
  WindowManager.SNAP_THRESHOLD_PX = SNAP_THRESHOLD_PX;
  WindowManager.cascadeRects = cascadeRects;
  WindowManager.tileRects = tileRects;
  WindowManager.CASCADE_OFFSET_PX = CASCADE_OFFSET_PX;
  WindowManager.TILE_GAP_PX = TILE_GAP_PX;
  global.QLSnapPosition = snapPosition;
  global.QLCascadeRects = cascadeRects;
  global.QLTileRects = tileRects;
  global.QLWindowManager = WindowManager;
})(window);
