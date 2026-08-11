/** Panel Estrategias — guías del catálogo (fuera del Simulador). */
(function (global) {
  "use strict";

  var FAMILY_ORDER = [
    "demo",
    "trend",
    "momentum",
    "mean_reversion",
    "market_making",
    "stats",
    "ml",
    "multi_asset",
    "microstructure",
    "arbitrage",
    "options",
  ];

  var GUIDE_WIN = "strategy_guide";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function foldText(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function renderGuideHtml(s) {
    var g = s.how_it_works || {};
    var steps = (g.steps || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    var exSteps = (g.example_steps || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    var params = (g.params_explained || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    var risks = (g.risks || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    var notes = (g.lab_notes || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    var whenUse = (g.when_to_use || [])
      .map(function (x) {
        return "<li>" + esc(x) + "</li>";
      })
      .join("");
    return (
      '<p class="sim-guide-plain"><strong>En simple</strong><br>' +
      esc(g.in_plain_words || g.idea || s.description || "—") +
      "</p>" +
      (whenUse
        ? "<p><strong>Cuándo usarla</strong></p>" +
          '<ul class="sim-guide-list">' +
          whenUse +
          "</ul>"
        : "") +
      "<p><strong>Paso a paso (cómo decide el lab)</strong></p>" +
      '<ol class="sim-guide-list">' +
      (steps || "<li>—</li>") +
      "</ol>" +
      "<p><strong>Cuándo compra</strong></p><p class=\"sim-guide-line\">" +
      esc(g.when_buy || "—") +
      "</p>" +
      "<p><strong>Cuándo vende / queda en efectivo</strong></p><p class=\"sim-guide-line\">" +
      esc(g.when_sell || "—") +
      "</p>" +
      '<div class="sim-guide-example"><strong>Ejemplo</strong><br>' +
      esc(g.example || "—") +
      (exSteps
        ? '<p style="margin:0.45rem 0 0.2rem"><strong>Ejemplo paso a paso</strong></p>' +
          '<ol class="sim-guide-list">' +
          exSteps +
          "</ol>"
        : "") +
      "</div>" +
      "<p><strong>Runnable:</strong> " +
      (s.runnable === false ? "no (stub research)" : "sí") +
      (g.runnable_note ? " — " + esc(g.runnable_note) : "") +
      "</p>" +
      "<p><strong>Familia:</strong> " +
      esc(s.family_label_es || s.family || "—") +
      " · <span class=\"muted\">id=" +
      esc(s.id) +
      "</span></p>" +
      "<details class=\"sim-guide-detail\"><summary><strong>Parámetros, riesgos y notas del lab</strong></summary>" +
      "<p><strong>Parámetros</strong></p><ul class=\"sim-guide-list\">" +
      params +
      "</ul>" +
      "<p><strong>Riesgos / límites</strong></p><ul class=\"sim-guide-list\">" +
      risks +
      "</ul>" +
      "<p><strong>Notas del lab</strong></p><ul class=\"sim-guide-list\">" +
      notes +
      "</ul></details>"
    );
  }

  function openStrategyGuideWindow(strategyId, strategiesCache) {
    var s =
      (strategiesCache || []).find(function (x) {
        return (x.id || x.strategy_id) === strategyId;
      }) || null;
    if (!s) {
      if (QLApi && QLApi.labStrategies) {
        QLApi.labStrategies().then(function (d) {
          openStrategyGuideWindow(strategyId, d.strategies || []);
        });
      }
      return;
    }
    var wm = global.QLShell && global.QLShell.wm;
    if (!wm && global.QLWindowManager) {
      /* fallback: open strategies pane */
      if (global.QLShell && QLShell.open) {
        QLShell.open("strategies", { focusId: strategyId });
      }
      return;
    }
    /* Prefer shell openers path — guide as child window via shell helper */
    if (global.QLShell && typeof global.QLShell.openStrategyGuide === "function") {
      global.QLShell.openStrategyGuide(s);
      return;
    }
    if (global.QLShell && QLShell.open) {
      QLShell.open("strategies", { focusId: strategyId });
    }
  }

  function createStrategiesPane(opts) {
    opts = opts || {};
    var root = document.createElement("div");
    root.className = "pane-strategies";
    root.innerHTML =
      '<div class="pane-section">' +
      '<div class="pane-head"><h3>Estrategias</h3>' +
      '<p class="muted pane-sub">Guías del catálogo · usá «Abrir en Simulador» para comparar</p></div>' +
      '<div class="sim-actions" style="margin:0.3rem 0">' +
      '<input type="search" id="st-search" placeholder="Buscar estrategia o familia…" ' +
      'style="flex:1;min-width:10rem;font-size:1.08rem">' +
      '<span class="mono muted" id="st-count">—</span>' +
      "</div>" +
      '<div id="st-list">cargando…</div>' +
      "</div>";

    var strategiesCache = [];
    var familyLabels = {};
    var focusId = opts.focusId || null;

    function findStrategy(id) {
      return strategiesCache.find(function (s) {
        return (s.id || s.strategy_id) === id;
      });
    }

    function strategyCardHtml(s, openCard) {
      var id = s.id || s.strategy_id;
      var runnable = s.runnable !== false;
      var g = s.how_it_works || {};
      var teaser = (g.in_plain_words || s.description || "").slice(0, 110);
      return (
        '<details class="sim-strat-card" data-strat-id="' +
        esc(id) +
        '"' +
        (openCard ? " open" : "") +
        ">" +
        "<summary>" +
        "<strong>" +
        esc(s.name || id) +
        "</strong> " +
        '<span class="muted mono">' +
        esc(id) +
        "</span>" +
        (runnable
          ? ' <span class="data-badge">runnable</span>'
          : ' <span class="data-badge data-badge-synth">stub · aún no corre</span>') +
        (teaser
          ? '<div class="muted" style="font-weight:400;font-size:1.04em;margin-top:0.15rem">' +
            esc(teaser) +
            (teaser.length >= 110 ? "…" : "") +
            "</div>"
          : "") +
        "</summary>" +
        '<div class="sim-strat-card-body">' +
        renderGuideHtml(s) +
        '<div class="sim-strat-actions" style="margin-top:0.5rem">' +
        '<button type="button" class="btn st-use" data-id="' +
        esc(id) +
        '"' +
        (runnable ? "" : " disabled") +
        ">Abrir en Simulador</button>" +
        "</div></div></details>"
      );
    }

    function bindActions() {
      root.querySelectorAll(".st-use").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          var id = btn.getAttribute("data-id");
          if (global.QLShell && QLShell.open) {
            QLShell.open("simulator", { prefill: { strategy_id: id } });
          }
        });
      });
    }

    function renderCatalog() {
      var listEl = root.querySelector("#st-list");
      var countEl = root.querySelector("#st-count");
      var q = foldText(
        (root.querySelector("#st-search") && root.querySelector("#st-search").value) ||
          ""
      );
      var byFam = {};
      strategiesCache.forEach(function (s) {
        var f = s.family || "other";
        if (!byFam[f]) byFam[f] = [];
        byFam[f].push(s);
      });
      var famKeys = FAMILY_ORDER.filter(function (f) {
        return byFam[f];
      }).concat(
        Object.keys(byFam)
          .filter(function (f) {
            return FAMILY_ORDER.indexOf(f) < 0;
          })
          .sort()
      );
      var shown = 0;
      var html = famKeys
        .map(function (fam) {
          var label = familyLabels[fam] || fam;
          var cards = (byFam[fam] || [])
            .filter(function (s) {
              if (!q) return true;
              var hay = foldText(
                [s.id, s.name, s.family, s.family_label_es, s.description]
                  .filter(Boolean)
                  .join(" ")
              );
              return hay.indexOf(q) >= 0;
            })
            .map(function (s) {
              shown += 1;
              return strategyCardHtml(
                s,
                focusId && (s.id || s.strategy_id) === focusId
              );
            })
            .join("");
          if (!cards) return "";
          return (
            '<details class="sim-strat-group" open>' +
            "<summary>" +
            esc(label) +
            "</summary>" +
            cards +
            "</details>"
          );
        })
        .join("");
      listEl.innerHTML = html || '<p class="muted">Sin coincidencias.</p>';
      if (countEl) countEl.textContent = shown + " fichas";
      bindActions();
      if (focusId) {
        var el = listEl.querySelector('[data-strat-id="' + focusId + '"]');
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
        focusId = null;
      }
    }

    function load() {
      if (!QLApi || !QLApi.labStrategies) {
        root.querySelector("#st-list").textContent = "API no disponible";
        return;
      }
      QLApi.labStrategies()
        .then(function (d) {
          strategiesCache = d.strategies || [];
          familyLabels = d.family_labels_es || {};
          renderCatalog();
        })
        .catch(function (e) {
          root.querySelector("#st-list").textContent = e.message || String(e);
        });
    }

    var search = root.querySelector("#st-search");
    if (search) {
      search.addEventListener("input", renderCatalog);
    }

    root.refresh = load;
    root.focusStrategy = function (id) {
      focusId = id;
      renderCatalog();
    };

    load();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createStrategiesPane = createStrategiesPane;
  global.QLPanes.renderStrategyGuideHtml = renderGuideHtml;
  global.QLPanes.openStrategyGuideWindow = openStrategyGuideWindow;
})(window);
