/** Registro acumulable de simulaciones — ventana WM (arrastrar / tamaño / min / ×). */
(function (global) {
  "use strict";

  var STORAGE_KEY = "ql_sim_registry_v1";
  var WIN_ID = "sim_registry";
  var MAX_ENTRIES = 80;
  var contentEl = null;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function save(list) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ENTRIES)));
    } catch (e) {}
  }

  function stampId(kind) {
    return kind + "_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);
  }

  function kindLabel(kind) {
    if (kind === "compare") return "Comparar";
    if (kind === "rank") return "Ranking";
    if (kind === "montecarlo") return "Monte Carlo";
    return kind || "?";
  }

  function syncBadge() {
    var n = load().length;
    var btn = document.getElementById("sb-sim-registry");
    if (btn) {
      btn.textContent = n ? "Sims (" + n + ")" : "Sims";
      btn.classList.toggle("sb-sim-registry-hot", n > 0);
    }
  }

  function getWm() {
    return global.QLShell && global.QLShell.wm ? global.QLShell.wm : null;
  }

  function openMemo(memo, params) {
    if (!memo) return;
    var wm = getWm();
    var winId = "sim_memo_" + (memo.kind || "run") + "_view";
    var csvName = (memo.filenameBase || "quantlab-memo") + ".csv";
    var txtName = (memo.filenameBase || "quantlab-memo") + ".txt";
    var fullText = memo.text || "";
    if (params && typeof params === "object" && Object.keys(params).length) {
      fullText +=
        "\n\n— PARÁMETROS SELECCIONADOS (JSON) —\n" +
        JSON.stringify(params, null, 2);
    }
    var csvUrl = URL.createObjectURL(
      new Blob(["\ufeff" + (memo.csv || "")], { type: "text/csv;charset=utf-8" })
    );
    var txtUrl = URL.createObjectURL(
      new Blob([fullText], { type: "text/plain;charset=utf-8" })
    );
    var waText =
      fullText.length > 3500
        ? fullText.slice(0, 3400) +
          "\n\n…(recortado)\nDescargá el CSV/TXT completo para verificación."
        : fullText;
    var waHref =
      "https://api.whatsapp.com/send?text=" + encodeURIComponent(waText);

    var pane = document.createElement("div");
    pane.className = "pane-sim-memo";
    pane.innerHTML =
      '<div class="sim-memo-toolbar">' +
      '<a class="btn" href="' +
      csvUrl +
      '" download="' +
      esc(csvName) +
      '">Descargar CSV</a> ' +
      '<a class="btn secondary" href="' +
      txtUrl +
      '" download="' +
      esc(txtName) +
      '">Descargar TXT</a> ' +
      '<button type="button" class="btn secondary" id="reg-memo-copy">Copiar texto</button> ' +
      '<a class="btn secondary" href="' +
      waHref +
      '" target="_blank" rel="noopener noreferrer">Compartir WhatsApp</a>' +
      (memo.nRows != null
        ? '<span class="muted mono" style="font-size:0.72em">' +
          esc(memo.nRows) +
          " filas CSV</span>"
        : "") +
      "</div>" +
      '<p class="muted" style="font-size:0.75em;margin:0.35rem 0">' +
      "Memorando + parámetros · arrastrá bordes · × cierra." +
      "</p>" +
      '<pre class="sim-memo-body mono"></pre>';
    pane.querySelector(".sim-memo-body").textContent = fullText;
    var copyBtn = pane.querySelector("#reg-memo-copy");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var done = function () {
          copyBtn.textContent = "Copiado ✓";
          setTimeout(function () {
            copyBtn.textContent = "Copiar texto";
          }, 1600);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(fullText).then(done).catch(function () {
            window.prompt("Copiá:", fullText);
          });
        } else {
          window.prompt("Copiá:", fullText);
        }
      });
    }

    if (wm && typeof wm.open === "function") {
      if (wm.windows && wm.windows.has(winId)) wm.close(winId);
      var ws = wm.workspace;
      var ww = (ws && ws.clientWidth) || 900;
      var wh = (ws && ws.clientHeight) || 700;
      var w = Math.min(640, Math.max(420, ww - 80));
      var h = Math.min(560, Math.max(360, wh - 100));
      var x = Math.max(24, Math.floor((ww - w) / 2));
      var y = Math.max(24, Math.floor((wh - h) / 3));
      wm.open(winId, memo.title || "Memorando", pane, { x: x, y: y, w: w, h: h });
      if (typeof wm.focus === "function") wm.focus(winId);
      if (typeof wm.bringToFront === "function") {
        try {
          wm.bringToFront(winId);
        } catch (e) {}
      }
    } else {
      document.body.appendChild(pane);
    }
  }

  function renderList() {
    if (!contentEl) return;
    var listEl = contentEl.querySelector(".ql-sim-registry-list");
    var countEl = contentEl.querySelector(".ql-sim-registry-count");
    var list = load();
    if (countEl) countEl.textContent = String(list.length);
    syncBadge();
    if (!listEl) return;
    if (!list.length) {
      listEl.innerHTML =
        '<p class="muted" style="font-size:0.78em;margin:0.5rem">' +
        "Todavía no hay corridas.<br/>Corré <strong>Comparar</strong>, " +
        "<strong>Ranking</strong> o <strong>Monte Carlo</strong>." +
        "</p>";
      return;
    }
    listEl.innerHTML = list
      .map(function (e) {
        var when = e.created_at
          ? new Date(e.created_at).toLocaleString("es-AR")
          : "—";
        return (
          '<button type="button" class="ql-sim-registry-item" data-id="' +
          esc(e.id) +
          '">' +
          '<span class="ql-sim-registry-kind">' +
          esc(kindLabel(e.kind)) +
          "</span>" +
          '<span class="ql-sim-registry-title">' +
          esc(e.title || e.summary || e.id) +
          "</span>" +
          '<span class="ql-sim-registry-when muted mono">' +
          esc(when) +
          "</span>" +
          '<span class="ql-sim-registry-sum muted">' +
          esc(e.summary || "") +
          "</span>" +
          "</button>"
        );
      })
      .join("");
    listEl.querySelectorAll(".ql-sim-registry-item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-id");
        var hit = load().find(function (x) {
          return x.id === id;
        });
        if (hit && hit.memo) openMemo(hit.memo, hit.params);
      });
    });
  }

  function buildContent() {
    var root = document.createElement("div");
    root.className = "pane-sim-registry";
    root.innerHTML =
      '<div class="ql-sim-registry-toolbar">' +
      '<span class="muted" style="font-size:0.72em;flex:1">' +
      "Comparar · Ranking · Monte Carlo · click = memo" +
      "</span>" +
      '<span class="mono muted ql-sim-registry-count">0</span> ' +
      '<button type="button" class="btn secondary ql-sim-registry-clear" title="Vaciar historial">Vaciar</button>' +
      "</div>" +
      '<div class="ql-sim-registry-list"></div>';
    root.querySelector(".ql-sim-registry-clear").addEventListener("click", function () {
      if (!window.confirm("¿Vaciar el historial de simulaciones de este navegador?")) {
        return;
      }
      save([]);
      renderList();
    });
    root.refresh = renderList;
    root.dispose = function () {
      if (contentEl === root) contentEl = null;
    };
    contentEl = root;
    renderList();
    return root;
  }

  /**
   * Abre / enfoca / restaura la ventana del registro (como cualquier panel QL).
   * @param {object} [opts] geometría {x,y,w,h,minimized,maximized,z}
   */
  function openWindow(opts) {
    var wm = getWm();
    if (!wm || typeof wm.open !== "function") {
      setTimeout(function () {
        openWindow(opts);
      }, 120);
      return null;
    }
    opts = opts || {};
    if (wm.windows && wm.windows.has(WIN_ID)) {
      if (typeof wm.focus === "function") wm.focus(WIN_ID);
      var rec = wm.windows.get(WIN_ID);
      if (rec && rec.el && rec.el.classList.contains("minimized") && typeof wm.restore === "function") {
        wm.restore(WIN_ID);
      }
      if (rec && rec.body && rec.body.firstElementChild) {
        contentEl = rec.body.firstElementChild;
        if (typeof contentEl.refresh === "function") contentEl.refresh();
        else renderList();
      }
      if (typeof wm.bringToFront === "function") {
        try {
          wm.bringToFront(WIN_ID);
        } catch (e) {}
      }
      syncBadge();
      return rec;
    }
    var pane = buildContent();
    var defaults = { x: 12, y: 12, w: 360, h: 440 };
    var geo = {
      x: opts.x != null ? opts.x : defaults.x,
      y: opts.y != null ? opts.y : defaults.y,
      w: opts.w != null ? opts.w : defaults.w,
      h: opts.h != null ? opts.h : defaults.h,
    };
    if (opts.z != null) geo.z = opts.z;
    if (opts.minimized) geo.minimized = true;
    if (opts.maximized) geo.maximized = true;
    return wm.open(WIN_ID, "Mis simulaciones", pane, geo);
  }

  function show() {
    return openWindow();
  }

  function add(entry) {
    if (!entry || !entry.memo) return null;
    var list = load();
    var item = {
      id: entry.id || stampId(entry.kind || "run"),
      kind: entry.kind || entry.memo.kind || "run",
      title: entry.title || entry.memo.title || "Simulación",
      summary: entry.summary || "",
      created_at: entry.created_at || new Date().toISOString(),
      params: entry.params || {},
      memo: entry.memo,
    };
    list.unshift(item);
    save(list);
    openWindow();
    renderList();
    syncBadge();
    return item;
  }

  function init() {
    syncBadge();
    var sb = document.getElementById("sb-sim-registry");
    if (sb && !sb._qlSimBound) {
      sb._qlSimBound = true;
      sb.addEventListener("click", function () {
        if (global.QLShell && typeof global.QLShell.open === "function") {
          global.QLShell.open("sim_registry");
        } else {
          show();
        }
      });
    }
  }

  global.QLSimRegistry = {
    WIN_ID: WIN_ID,
    init: init,
    add: add,
    openMemo: openMemo,
    openWindow: openWindow,
    show: show,
    list: load,
    render: renderList,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
