/** Componentes UI compartidos — design system ligero (sin build). */

(function (global) {

  "use strict";



  function esc(s) {

    return String(s == null ? "" : s)

      .replace(/&/g, "&amp;")

      .replace(/</g, "&lt;")

      .replace(/>/g, "&gt;")

      .replace(/"/g, "&quot;");

  }



  /** @param {{ title: string, subtitle?: string, actions?: HTMLElement[] }} opts */

  function panelHeader(opts) {

    var wrap = document.createElement("header");

    wrap.className = "ql-panel-header";

    var text = document.createElement("div");

    text.className = "ql-panel-header-text";

    text.innerHTML =

      "<h2 class=\"ql-panel-title\">" +

      esc(opts.title) +

      "</h2>" +

      (opts.subtitle

        ? '<p class="muted ql-panel-subtitle">' + esc(opts.subtitle) + "</p>"

        : "");

    wrap.appendChild(text);

    if (opts.actions && opts.actions.length) {

      var acts = document.createElement("div");

      acts.className = "ql-panel-header-actions";

      opts.actions.forEach(function (el) {

        acts.appendChild(el);

      });

      wrap.appendChild(acts);

    }

    return wrap;

  }



  /** @param {{ mode?: string, liveBlocked?: boolean, venue?: string }} opts */

  function safetyBadge(opts) {

    var el = document.createElement("p");

    el.className = "ql-safety-badge";

    el.setAttribute("role", "status");

    var mode = (opts.mode || "paper").toLowerCase();

    var modeLabel =

      mode === "paper" ? "Modo prueba (paper)" : "Modo " + mode.toUpperCase();

    var blocked = opts.liveBlocked !== false;

    var parts = [modeLabel, "datos de mercado reales"];

    if (blocked) parts.push("sin órdenes en producción");

    else parts.push("live habilitado — cuidado");

    if (opts.venue) parts.push(String(opts.venue));

    el.textContent = parts.join(" · ");

    if (!blocked) el.classList.add("ql-safety-badge--warn");

    return el;

  }



  /** @param {{ label: string, variant?: string, onClick?: function, disabled?: boolean, title?: string }} opts */

  function primaryAction(opts) {

    var btn = document.createElement("button");

    btn.type = "button";

    btn.className = "btn ql-primary-action";

    if (opts.variant === "secondary") btn.classList.add("secondary");

    if (opts.variant === "ghost") btn.classList.add("ghost");

    btn.textContent = opts.label;

    if (opts.title) btn.title = opts.title;

    if (opts.disabled) btn.disabled = true;

    if (typeof opts.onClick === "function") {

      btn.addEventListener("click", opts.onClick);

    }

    return btn;

  }



  /** @param {{ label: string, tone?: string }} opts */

  function statusChip(opts) {

    var span = document.createElement("span");

    span.className = "ql-status-chip";

    if (opts.tone) span.classList.add("ql-status-chip--" + opts.tone);

    span.textContent = opts.label;

    return span;

  }



  /** @param {{ steps: Array<{label:string,paneId?:string}>, onStep?: function(string), activePaneId?: string }} opts */

  function flowRail(opts) {

    var nav = document.createElement("nav");

    nav.className = "ql-flow-rail";

    nav.setAttribute("aria-label", "Flujo principal");

    var activeId = opts.activePaneId || "";

    (opts.steps || []).forEach(function (step, idx) {

      if (idx > 0) {

        var sep = document.createElement("span");

        sep.className = "ql-flow-sep";

        sep.setAttribute("aria-hidden", "true");

        sep.textContent = "›";

        nav.appendChild(sep);

      }

      var btn = document.createElement("button");

      btn.type = "button";

      btn.className = "ql-flow-step";

      if (step.paneId && step.paneId === activeId) {

        btn.classList.add("ql-flow-step--active");

        btn.setAttribute("aria-current", "step");

      }

      btn.textContent = step.label;

      if (step.paneId && typeof opts.onStep === "function") {

        btn.addEventListener("click", function () {

          opts.onStep(step.paneId);

        });

      }

      nav.appendChild(btn);

    });

    return nav;

  }



  /** Tarjeta de acción rápida en Home. */

  function actionCard(opts) {
    var card = document.createElement("button");
    card.type = "button";
    card.className = "ql-action-card";
    if (opts.compact) card.classList.add("ql-action-card--compact");
    card.innerHTML =
      (opts.icon
        ? '<span class="ql-action-card-icon" aria-hidden="true">' +
          esc(opts.icon) +
          "</span>"
        : "") +
      '<span class="ql-action-card-body">' +
      '<span class="ql-action-card-title">' +
      esc(opts.title) +
      "</span>" +
      (opts.subtitle
        ? '<span class="muted ql-action-card-sub">' + esc(opts.subtitle) + "</span>"
        : "") +
      "</span>";
    if (typeof opts.onClick === "function") {
      card.addEventListener("click", opts.onClick);
    }
    return card;
  }



  /** Inyecta header unificado + flujo en cualquier panel (Fases 6–11). */

  function enhancePaneRoot(root, paneId, opts) {

    opts = opts || {};

    if (!root || !paneId || paneId === "home") return root;

    if (root.querySelector(":scope > .ql-panel-header")) return root;



    var reg = global.QLPanelRegistry;

    var meta =

      reg && reg.getPanel ? reg.getPanel(paneId) : { label: paneId, tip: paneId };

    var actions = [];

    var next =

      reg && reg.getNextStep ? reg.getNextStep(paneId) : null;

    if (next && typeof opts.onOpen === "function") {

      actions.push(

        primaryAction({

          label: "Siguiente: " + next.label,

          variant: "secondary",

          title: next.label,

          onClick: function () {

            opts.onOpen(next.paneId);

          },

        })

      );

    }

    var flowPanes = {

      scanner: 1,

      simulator: 1,

      backtest: 1,

      montecarlo: 1,

      strategy_live_test: 1,

      monitor: 1,

      sim_registry: 1,

    };

    root.classList.add("ql-pane-v3");

    root.insertBefore(

      panelHeader({

        title: meta.label || paneId,

        subtitle: meta.subtitle || meta.tip || "",

        actions: actions,

      }),

      root.firstChild

    );

    if (

      flowPanes[paneId] &&

      reg &&

      reg.flowSteps &&

      reg.flowSteps.length &&

      typeof opts.onOpen === "function"

    ) {

      var rail = flowRail({

        steps: reg.flowSteps.slice(0, 6),

        onStep: opts.onOpen,

        activePaneId: paneId,

      });

      var railWrap = document.createElement("div");

      railWrap.className = "ql-panel-flow-wrap";

      railWrap.appendChild(rail);

      root.insertBefore(railWrap, root.children[1] || null);

    }

    return root;

  }



  global.QLUi = {

    esc: esc,

    panelHeader: panelHeader,

    safetyBadge: safetyBadge,

    primaryAction: primaryAction,

    statusChip: statusChip,

    flowRail: flowRail,

    actionCard: actionCard,

    enhancePaneRoot: enhancePaneRoot,

  };

})(typeof window !== "undefined" ? window : globalThis);

