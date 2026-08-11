/** Menú QL personalizable: barra rápida + secciones (orden / visibilidad). */
(function (global) {
  "use strict";

  var STORAGE_KEY = "ql_menu_config_v6";
  var openersRef = null;
  var onOpenRef = null;

  function getSections() {
    if (global.QLPanelRegistry && QLPanelRegistry.getMenuSections) {
      return QLPanelRegistry.getMenuSections();
    }
    return [
      {
        id: "inicio",
        label: "Inicio",
        defaultOpen: true,
        items: [{ id: "home", label: "Inicio", tip: "Orientación." }],
      },
    ];
  }

  function getTaskbarDefault() {
    if (global.QLPanelRegistry && QLPanelRegistry.taskbarDefault) {
      return QLPanelRegistry.taskbarDefault.slice();
    }
    return ["home", "scanner", "simulator", "strategy_live_test", "sim_registry", "chat"];
  }

  function paneMeta(id) {
    if (global.QLPanelRegistry && QLPanelRegistry.getPanel) {
      var p = QLPanelRegistry.getPanel(id);
      return { id: p.id, label: p.label, tip: p.tip };
    }
    var sections = getSections();
    for (var s = 0; s < sections.length; s++) {
      var items = sections[s].items;
      for (var i = 0; i < items.length; i++) {
        if (items[i].id === id) return items[i];
      }
    }
    return { id: id, label: id, tip: id };
  }

  function defaultConfig() {
    var SECTIONS = getSections();
    var TASKBAR_DEFAULT = getTaskbarDefault();
    var sections = {};
    SECTIONS.forEach(function (sec) {
      sections[sec.id] = {
        order: sec.items.map(function (it) {
          return it.id;
        }),
        hidden: [],
        open: sec.defaultOpen !== false,
      };
    });
    return {
      v: 2,
      taskbar: TASKBAR_DEFAULT.slice(),
      sectionOrder: SECTIONS.map(function (s) {
        return s.id;
      }),
      sections: sections,
    };
  }

  function loadConfig() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var cfg = JSON.parse(raw);
        return normalizeConfig(cfg);
      }
      var legacy = localStorage.getItem("ql_menu_favorites_v4");
      if (legacy) {
        var tb = JSON.parse(legacy);
        if (Array.isArray(tb) && tb.length) {
          var c = defaultConfig();
          c.taskbar = tb.filter(function (id) {
            return openersRef && openersRef[id];
          });
          saveConfig(c);
          return c;
        }
      }
    } catch (e) {}
    return defaultConfig();
  }

  function normalizeConfig(cfg) {
    var base = defaultConfig();
    var SECTIONS = getSections();
    var TASKBAR_DEFAULT = getTaskbarDefault();
    if (!cfg || typeof cfg !== "object") return base;
    var out = {
      v: 2,
      taskbar: Array.isArray(cfg.taskbar) ? cfg.taskbar.slice() : base.taskbar.slice(),
      sectionOrder: Array.isArray(cfg.sectionOrder) ? cfg.sectionOrder.slice() : base.sectionOrder.slice(),
      sections: {},
    };
    SECTIONS.forEach(function (sec) {
      var src = (cfg.sections && cfg.sections[sec.id]) || {};
      var order = Array.isArray(src.order) ? src.order.slice() : base.sections[sec.id].order.slice();
      var ids = sec.items.map(function (it) {
        return it.id;
      });
      order = order.filter(function (id) {
        return ids.indexOf(id) >= 0;
      });
      ids.forEach(function (id) {
        if (order.indexOf(id) < 0) order.push(id);
      });
      out.sections[sec.id] = {
        order: order,
        hidden: Array.isArray(src.hidden) ? src.hidden.filter(function (id) { return ids.indexOf(id) >= 0; }) : [],
        open: src.open != null ? !!src.open : base.sections[sec.id].open,
      };
    });
    out.taskbar = out.taskbar.filter(function (id) {
      return openersRef && openersRef[id];
    });
    TASKBAR_DEFAULT.forEach(function (id) {
      if (out.taskbar.indexOf(id) < 0 && openersRef && openersRef[id]) {
        out.taskbar.push(id);
      }
    });
    return out;
  }

  function saveConfig(cfg) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeConfig(cfg)));
    } catch (e) {}
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderTaskbarQuick() {
    var bar = document.getElementById("taskbar-quick");
    if (!bar) return;
    var cfg = loadConfig();
    bar.innerHTML = cfg.taskbar
      .filter(function (id) {
        return openersRef && openersRef[id];
      })
      .map(function (id) {
        var meta = paneMeta(id);
        return (
          '<button type="button" class="tb-quick-btn" data-open="' +
          esc(id) +
          '" data-tip="' +
          esc(meta.tip) +
          '" title="' +
          esc(meta.label) +
          '">' +
          esc(meta.label) +
          "</button>"
        );
      })
      .join("");
  }

  function renderDynamicSections() {
    var host = document.getElementById("ql-menu-dynamic");
    if (!host) return;
    var SECTIONS = getSections();
    var cfg = loadConfig();
    var html = "";
    cfg.sectionOrder.forEach(function (secId) {
      var secDef = null;
      for (var i = 0; i < SECTIONS.length; i++) {
        if (SECTIONS[i].id === secId) {
          secDef = SECTIONS[i];
          break;
        }
      }
      if (!secDef) return;
      var secCfg = cfg.sections[secId] || { order: [], hidden: [], open: false };
      var openAttr = secCfg.open ? " open" : "";
      html +=
        '<details class="start-acc"' +
        openAttr +
        ' data-sec="' +
        esc(secId) +
        '">' +
        '<summary class="start-acc-sum">' +
        esc(secDef.label) +
        "</summary>" +
        '<div class="start-acc-body ql-menu-sec-body">';
      secCfg.order.forEach(function (paneId) {
        if (secCfg.hidden.indexOf(paneId) >= 0) return;
        if (!openersRef || !openersRef[paneId]) return;
        var meta = paneMeta(paneId);
        html +=
          '<button type="button" data-open="' +
          esc(paneId) +
          '" data-tip="' +
          esc(meta.tip) +
          '">' +
          esc(meta.label) +
          "</button>";
      });
      html += "</div></details>";
    });
    host.innerHTML = html;
  }

  function moveInArray(arr, idx, dir) {
    var j = idx + dir;
    if (j < 0 || j >= arr.length) return arr;
    var t = arr[j];
    arr[j] = arr[idx];
    arr[idx] = t;
    return arr;
  }

  function renderCustomize() {
    var box = document.getElementById("ql-menu-customize-list");
    if (!box) return;
    var SECTIONS = getSections();
    var cfg = loadConfig();
    var html = "";
    cfg.sectionOrder.forEach(function (secId) {
      var secDef = SECTIONS.find(function (s) {
        return s.id === secId;
      });
      if (!secDef) return;
      var secCfg = cfg.sections[secId];
      html += '<div class="ql-menu-sec-block" data-sec="' + esc(secId) + '">';
      html +=
        '<div class="ql-menu-sec-head">' +
        "<b>" +
        esc(secDef.label) +
        "</b>" +
        '<span class="ql-menu-sec-moves">' +
        '<button type="button" class="ql-mc-sec-up" title="Subir sección">↑ sec</button>' +
        '<button type="button" class="ql-mc-sec-down" title="Bajar sección">↓ sec</button>' +
        "</span></div>";
      secCfg.order.forEach(function (paneId, idx) {
        if (!openersRef || !openersRef[paneId]) return;
        var meta = paneMeta(paneId);
        var inBar = cfg.taskbar.indexOf(paneId) >= 0;
        var inMenu = secCfg.hidden.indexOf(paneId) < 0;
        html +=
          '<div class="ql-menu-row" data-pane="' +
          esc(paneId) +
          '" data-sec="' +
          esc(secId) +
          '">' +
          '<label class="ql-mc-check"><input type="checkbox" class="ql-mc-bar"' +
          (inBar ? " checked" : "") +
          " /> Barra</label>" +
          '<label class="ql-mc-check"><input type="checkbox" class="ql-mc-menu"' +
          (inMenu ? " checked" : "") +
          " /> Menú</label>" +
          '<span class="ql-mc-label">' +
          esc(meta.label) +
          "</span>" +
          '<span class="ql-mc-btns">' +
          '<button type="button" class="ql-mc-up" title="Subir">↑</button>' +
          '<button type="button" class="ql-mc-down" title="Bajar">↓</button>' +
          '<button type="button" class="ql-mc-top-bar" title="Primero en barra">⤒ barra</button>' +
          '<button type="button" class="ql-mc-top-sec" title="Primero en sección">⤒ menú</button>' +
          "</span></div>";
      });
      html += "</div>";
    });
    box.innerHTML = html;
  }

  function renderAll() {
    renderTaskbarQuick();
    renderDynamicSections();
    renderCustomize();
    var favList = document.getElementById("ql-fav-list");
    if (favList) {
      favList.innerHTML =
        '<p class="muted ql-menu-hint">Usá «Personalizar menú QL» abajo para ordenar barra y menú.</p>';
    }
  }

  function bindCustomizeEvents() {
    var box = document.getElementById("ql-menu-customize-list");
    if (!box || box._qlBound) return;
    box._qlBound = true;
    box.addEventListener("click", function (ev) {
      var btn = ev.target.closest("button");
      if (!btn) return;
      ev.preventDefault();
      ev.stopPropagation();
      var row = btn.closest(".ql-menu-row");
      var secBlock = btn.closest(".ql-menu-sec-block");
      var cfg = loadConfig();
      if (btn.classList.contains("ql-mc-sec-up") && secBlock) {
        var sid = secBlock.getAttribute("data-sec");
        var si = cfg.sectionOrder.indexOf(sid);
        if (si > 0) {
          var t = cfg.sectionOrder[si - 1];
          cfg.sectionOrder[si - 1] = cfg.sectionOrder[si];
          cfg.sectionOrder[si] = t;
          saveConfig(cfg);
          renderAll();
        }
        return;
      }
      if (btn.classList.contains("ql-mc-sec-down") && secBlock) {
        var sid2 = secBlock.getAttribute("data-sec");
        var si2 = cfg.sectionOrder.indexOf(sid2);
        if (si2 >= 0 && si2 < cfg.sectionOrder.length - 1) {
          var t2 = cfg.sectionOrder[si2 + 1];
          cfg.sectionOrder[si2 + 1] = cfg.sectionOrder[si2];
          cfg.sectionOrder[si2] = t2;
          saveConfig(cfg);
          renderAll();
        }
        return;
      }
      if (!row) return;
      var paneId = row.getAttribute("data-pane");
      var secId = row.getAttribute("data-sec");
      var secCfg = cfg.sections[secId];
      var idx = secCfg.order.indexOf(paneId);
      if (btn.classList.contains("ql-mc-up") && idx > 0) {
        moveInArray(secCfg.order, idx, -1);
        saveConfig(cfg);
        renderAll();
        return;
      }
      if (btn.classList.contains("ql-mc-down") && idx >= 0 && idx < secCfg.order.length - 1) {
        moveInArray(secCfg.order, idx, 1);
        saveConfig(cfg);
        renderAll();
        return;
      }
      if (btn.classList.contains("ql-mc-top-sec") && idx > 0) {
        secCfg.order.splice(idx, 1);
        secCfg.order.unshift(paneId);
        saveConfig(cfg);
        renderAll();
        return;
      }
      if (btn.classList.contains("ql-mc-top-bar")) {
        var bi = cfg.taskbar.indexOf(paneId);
        if (bi < 0) cfg.taskbar.unshift(paneId);
        else if (bi > 0) {
          cfg.taskbar.splice(bi, 1);
          cfg.taskbar.unshift(paneId);
        }
        saveConfig(cfg);
        renderAll();
      }
    });
    box.addEventListener("change", function (ev) {
      var inp = ev.target;
      if (!inp || inp.tagName !== "INPUT") return;
      var row = inp.closest(".ql-menu-row");
      if (!row) return;
      var paneId = row.getAttribute("data-pane");
      var secId = row.getAttribute("data-sec");
      var cfg = loadConfig();
      var secCfg = cfg.sections[secId];
      if (inp.classList.contains("ql-mc-bar")) {
        var bi = cfg.taskbar.indexOf(paneId);
        if (inp.checked && bi < 0) cfg.taskbar.push(paneId);
        if (!inp.checked && bi >= 0) cfg.taskbar.splice(bi, 1);
      }
      if (inp.classList.contains("ql-mc-menu")) {
        var hi = secCfg.hidden.indexOf(paneId);
        if (inp.checked && hi >= 0) secCfg.hidden.splice(hi, 1);
        if (!inp.checked && hi < 0) secCfg.hidden.push(paneId);
      }
      saveConfig(cfg);
      renderAll();
    });
  }

  function bindMenuDelegation(startMenu) {
    if (!startMenu || startMenu._qlMenuDeleg) return;
    startMenu._qlMenuDeleg = true;
    startMenu.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-open]");
      if (!btn || !startMenu.contains(btn)) return;
      if (btn.closest("#ql-menu-customize-list")) return;
      ev.preventDefault();
      ev.stopPropagation();
      var key = btn.getAttribute("data-open");
      if (key === "about") {
        if (onOpenRef && onOpenRef.about) onOpenRef.about();
        return;
      }
      try {
        if (onOpenRef && onOpenRef.open && onOpenRef.open(key)) return;
        if (openersRef && openersRef[key]) openersRef[key]();
      } catch (err) {
        window.alert("No pude abrir «" + key + "»: " + (err.message || err));
      }
    });
  }

  function bindTaskbarDelegation() {
    var bar = document.getElementById("taskbar-quick");
    if (!bar || bar._qlTaskbarBound) return;
    bar._qlTaskbarBound = true;
    bar.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-open]");
      if (!btn || !bar.contains(btn)) return;
      ev.preventDefault();
      var key = btn.getAttribute("data-open");
      try {
        if (openersRef && openersRef[key]) openersRef[key]();
      } catch (err) {
        window.alert("No pude abrir «" + key + "»: " + (err.message || err));
      }
    });
  }

  function init(opts) {
    openersRef = opts.openers || {};
    onOpenRef = opts.handlers || {};
    bindCustomizeEvents();
    bindTaskbarDelegation();
    var resetBtn = document.getElementById("ql-menu-reset");
    if (resetBtn && !resetBtn._qlBound) {
      resetBtn._qlBound = true;
      resetBtn.addEventListener("click", function (ev) {
        ev.preventDefault();
        saveConfig(defaultConfig());
        renderAll();
      });
    }
    var favReset = document.getElementById("ql-fav-reset");
    if (favReset && !favReset._qlBound) {
      favReset._qlBound = true;
      favReset.addEventListener("click", function (ev) {
        ev.preventDefault();
        saveConfig(defaultConfig());
        renderAll();
      });
    }
    if (opts.startMenu) bindMenuDelegation(opts.startMenu);
    renderAll();
  }

  global.QLMenu = {
    init: init,
    renderAll: renderAll,
    loadConfig: loadConfig,
    saveConfig: saveConfig,
    paneMeta: paneMeta,
    TASKBAR_DEFAULT: TASKBAR_DEFAULT,
  };
})(typeof window !== "undefined" ? window : this);
