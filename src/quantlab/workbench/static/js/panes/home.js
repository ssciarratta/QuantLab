/** Panel Inicio — orientación, estado y accesos por tarea. */
(function (global) {
  "use strict";

  function createHomePane(opts) {
    opts = opts || {};
    var onOpen = typeof opts.onOpen === "function" ? opts.onOpen : function () {};

    var root = document.createElement("div");
    root.className = "pane-home";

    var headerHost = document.createElement("div");
    root.appendChild(headerHost);

    var safetyHost = document.createElement("div");
    safetyHost.className = "pane-home-safety";
    root.appendChild(safetyHost);

    var statusRow = document.createElement("div");
    statusRow.className = "pane-home-status";
    statusRow.innerHTML =
      '<span id="home-health-chip" class="ql-status-chip">—</span>' +
      '<span class="mono muted" id="home-session">session —</span>' +
      '<span class="mono muted" id="home-version">v—</span>';
    root.appendChild(statusRow);

    var flowHost = document.createElement("div");
    flowHost.className = "pane-home-flow";
    root.appendChild(flowHost);

    var actionsHost = document.createElement("div");
    actionsHost.className = "pane-home-actions";
    root.appendChild(actionsHost);

    var layoutsTitle = document.createElement("h3");
    layoutsTitle.className = "pane-home-section-title";
    layoutsTitle.textContent = "Espacios de trabajo";
    root.appendChild(layoutsTitle);

    var layoutsRow = document.createElement("div");
    layoutsRow.className = "pane-home-layouts";
    root.appendChild(layoutsRow);

    var hint = document.createElement("p");
    hint.className = "muted pane-home-hint";
    hint.textContent =
      "Tip: Ctrl+K abre la paleta. Monte Carlo también desde el Simulador con la misma moneda.";
    root.appendChild(hint);

    function renderHeader() {
      headerHost.innerHTML = "";
      if (global.QLUi && QLUi.panelHeader) {
        headerHost.appendChild(
          QLUi.panelHeader({
            title: "Inicio",
            subtitle: "Elegí una tarea — todo el flujo a un clic",
            actions: [
              QLUi.primaryAction({
                label: "Estado",
                variant: "secondary",
                onClick: function () {
                  onOpen("health");
                },
              }),
            ],
          })
        );
      }
    }

    function renderFlow() {
      flowHost.innerHTML = "";
      var steps =
        global.QLPanelRegistry && QLPanelRegistry.flowSteps
          ? QLPanelRegistry.flowSteps
          : [];
      if (global.QLUi && QLUi.flowRail && steps.length) {
        flowHost.appendChild(
          QLUi.flowRail({
            steps: steps,
            onStep: function (paneId) {
              onOpen(paneId);
            },
          })
        );
      }
    }

    function renderActions() {
      actionsHost.innerHTML = "";
      var panels =
        global.QLPanelRegistry && QLPanelRegistry.getPrimaryHomeActions
          ? QLPanelRegistry.getPrimaryHomeActions()
          : [];

      var title = document.createElement("h3");
      title.className = "pane-home-section-title";
      title.textContent = "Accesos rápidos";
      actionsHost.appendChild(title);

      var grid = document.createElement("div");
      grid.className = "ql-action-grid ql-action-grid--home";

      panels.forEach(function (p) {
        if (!global.QLUi || !QLUi.actionCard || !p) return;
        grid.appendChild(
          QLUi.actionCard({
            title: p.label,
            subtitle: p.subtitle || "",
            icon: p.icon || "",
            compact: true,
            onClick: function () {
              onOpen(p.id);
            },
          })
        );
      });
      actionsHost.appendChild(grid);
    }

    function renderLayouts() {
      layoutsRow.innerHTML = "";
      var presets =
        global.QLPanelRegistry && QLPanelRegistry.layoutPresets
          ? QLPanelRegistry.layoutPresets
          : {};
      Object.keys(presets).forEach(function (key) {
        var preset = presets[key];
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn secondary ql-layout-preset-btn";
        btn.textContent = preset.label;
        btn.title = preset.tip || preset.label;
        btn.addEventListener("click", function () {
          if (global.QLLayoutPresets && QLLayoutPresets.apply) {
            QLLayoutPresets.apply(key, onOpen);
          }
        });
        layoutsRow.appendChild(btn);
      });
    }

    async function refresh() {
      renderHeader();
      renderFlow();
      renderActions();
      renderLayouts();

      var modePayload = null;
      try {
        modePayload = await QLApi.getMode();
      } catch (e) {}

      safetyHost.innerHTML = "";
      if (global.QLUi && QLUi.safetyBadge) {
        safetyHost.appendChild(
          QLUi.safetyBadge({
            mode: modePayload && modePayload.mode,
            liveBlocked: !modePayload || modePayload.live_blocked !== false,
            venue: modePayload && modePayload.connected_venue,
          })
        );
      }

      var healthChip = root.querySelector("#home-health-chip");
      var sessionEl = root.querySelector("#home-session");
      var versionEl = root.querySelector("#home-version");

      try {
        var h = await QLApi.health();
        if (healthChip) {
          healthChip.textContent = h.ok ? "Todo bien" : "Revisar salud";
          healthChip.className =
            "ql-status-chip ql-status-chip--" + (h.ok ? "ok" : "bad");
        }
      } catch (e) {
        if (healthChip) {
          healthChip.textContent = "Sin conexión";
          healthChip.className = "ql-status-chip ql-status-chip--bad";
        }
      }

      try {
        var sess = await QLApi.session();
        var sid =
          (sess && sess.session && sess.session.session_id) ||
          (sess && sess.session_id) ||
          "—";
        if (sessionEl) sessionEl.textContent = "session " + sid;
      } catch (e) {
        if (sessionEl) sessionEl.textContent = "session —";
      }

      if (versionEl && global.QLApi && QLApi.getVersion) {
        QLApi.getVersion()
          .then(function (v) {
            if (v && v.version) versionEl.textContent = "v" + v.version;
          })
          .catch(function () {});
      }
    }

    renderHeader();
    renderFlow();
    renderActions();
    renderLayouts();

    root.refresh = refresh;
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createHomePane = createHomePane;
})(typeof window !== "undefined" ? window : globalThis);
