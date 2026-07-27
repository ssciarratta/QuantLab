/** Panel Chat IA — asistente con memoria + acciones UI (abrir/correr). */
(function (global) {
  "use strict";

  var QUICK_CHIPS = [
    {
      label: "Abrí Guided Lab",
      tip: "Pide al asistente que abra el panel Guided Lab.\nListo para venue → scan → simular.",
    },
    {
      label: "Corré alpha en Binance",
      tip: "Ejecuta ranking alpha con MD público Binance.\nSin órdenes; solo research.",
    },
    {
      label: "Corré pipeline con inventory_mm",
      tip: "Pipeline scan→backtest top-5 con inventory_mm.\nSimulación paper.",
    },
    {
      label: "Ya tengo el ranking, ¿qué MM probamos?",
      tip: "Pregunta de instructor: qué market making probar.\nUsa el contexto del último ranking.",
    },
    {
      label: "Dale, siguiente paso",
      tip: "Continúa el flujo sugerido por el asistente.\nFollow-up corto multi-turno.",
    },
    {
      label: "¿Cómo empiezo?",
      tip: "Guía paso a paso para arrancar el lab.\nExplica sin ejecutar aún.",
    },
  ];

  function createChatPane() {
    const root = document.createElement("div");
    root.className = "pane-chat";

    root.innerHTML =
      '<div class="chat-safe-banner" role="status">' +
      '<span class="chat-safe-badge">asistente</span> ' +
      "Puede abrir paneles y correr alpha/pipeline (sin órdenes) " +
      '<button type="button" class="btn secondary" id="chat-clear" style="margin-left:0.5em" data-tip="Borra el historial y la memoria local del chat.\nNo afecta otros paneles.">Limpiar memoria</button>' +
      "</div>" +
      '<div class="chat-chips pane-row" id="chat-chips"></div>' +
      '<div class="chat-history" id="chat-history" aria-live="polite"></div>' +
      '<form class="chat-compose" id="chat-form">' +
      '<input type="text" id="chat-input" maxlength="2000" ' +
      'placeholder="Ej: abrí Guided Lab · corré alpha en Binance · corré pipeline…" autocomplete="off" />' +
      '<button type="submit" class="btn" id="chat-send" data-tip="Envía el mensaje al asistente.\nPuede abrir paneles o correr alpha/pipeline.">Enviar</button>' +
      "</form>" +
      '<p class="muted mono chat-meta" id="chat-meta">tools —</p>';

    const history = root.querySelector("#chat-history");
    const form = root.querySelector("#chat-form");
    const input = root.querySelector("#chat-input");
    const meta = root.querySelector("#chat-meta");
    const chipsEl = root.querySelector("#chat-chips");
    let memoryTurns = 0;

    function appendBubble(role, text) {
      const div = document.createElement("div");
      div.className = "chat-bubble chat-" + role;
      div.textContent = text;
      if (role === "assistant" || role === "system") {
        div.style.whiteSpace = "pre-wrap";
      }
      history.appendChild(div);
      history.scrollTop = history.scrollHeight;
    }

    function runActions(actions) {
      if (!Array.isArray(actions) || !actions.length) return;
      actions.forEach(function (act) {
        if (!act || typeof act !== "object") return;
        if (act.type === "open_pane" && act.pane && window.QLShell) {
          try {
            QLShell.open(String(act.pane));
          } catch (e) {}
        }
        if (act.type === "toast" && act.message && window.QLToasts) {
          try {
            QLToasts.success(String(act.message));
          } catch (e) {}
        }
      });
    }

    function sendMessage(msg) {
      const trimmed = (msg || "").trim();
      if (!trimmed) return;
      appendBubble("user", trimmed);
      meta.textContent = "…";
      QLApi.chat(trimmed, { pane: "chat", guided_lab: true })
        .then(function (data) {
          appendBubble("assistant", data.reply || "(sin respuesta)");
          runActions(data.actions || []);
          memoryTurns = data.memory_turns || memoryTurns;
          const tools = (data.tools_used || []).join(", ") || "—";
          const nAct = (data.actions || []).length;
          const prov = data.provider || "?";
          meta.textContent =
            "memoria=" +
            String(data.memory_turns || memoryTurns) +
            " · provider=" +
            prov +
            " · actions=" +
            String(nAct) +
            " · tools: " +
            tools;
        })
        .catch(function (err) {
          appendBubble("assistant", "Error: " + err.message);
          meta.textContent = "error";
        });
    }

    function loadHistory() {
      return QLApi.chatHistory()
        .then(function (data) {
          const msgs = data.messages || [];
          memoryTurns = data.count || msgs.length;
          if (!msgs.length) {
            appendBubble(
              "system",
              "Soy tu asistente QuantLab.\n\n" +
                "Puedo ABRIR paneles («abrí Guided Lab») y CORRER cosas seguras:\n" +
                "«corré alpha en Binance» · «corré pipeline con inventory_mm».\n" +
                "No envío órdenes. A−/A+ en la barra de abajo agrandan la letra."
            );
            return;
          }
          msgs.forEach(function (m) {
            if (m.role === "user" || m.role === "assistant") {
              appendBubble(m.role, m.content || "");
            }
          });
        })
        .catch(function () {
          appendBubble("system", "Asistente QuantLab — memoria local activa.");
        });
    }

    QUICK_CHIPS.forEach(function (chip) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn secondary chat-chip";
      btn.textContent = chip.label;
      btn.setAttribute("data-tip", chip.tip);
      btn.addEventListener("click", function () {
        sendMessage(chip.label);
      });
      chipsEl.appendChild(btn);
    });

    root.querySelector("#chat-clear").addEventListener("click", function () {
      QLApi.chatClear()
        .then(function () {
          history.innerHTML = "";
          memoryTurns = 0;
          loadHistory();
          meta.textContent = "memoria limpiada";
        })
        .catch(function (err) {
          meta.textContent = "clear error: " + err.message;
        });
    });

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      const msg = input.value;
      input.value = "";
      sendMessage(msg);
    });

    root.refresh = async function () {
      try {
        const t = await QLApi.chatTools();
        meta.textContent =
          "allowlist: " +
          ((t.allowlist || []).join(", ") || "—") +
          " · memoria_turns=" +
          String(t.memory_turns || memoryTurns);
      } catch (err) {
        meta.textContent = "tools error: " + err.message;
      }
    };

    loadHistory();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createChatPane = createChatPane;
})(window);
