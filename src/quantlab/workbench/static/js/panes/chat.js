/** Panel Chat IA — asistente con memoria (F112/F113). */
(function (global) {
  "use strict";

  var QUICK_CHIPS = [
    "Vamos a correr alpha en Binance y detectar monedas",
    "Ya tengo el ranking, ¿qué MM probamos?",
    "Dale, siguiente paso",
    "¿Cómo empiezo?",
    "Explícame inventory_mm",
  ];

  function createChatPane() {
    const root = document.createElement("div");
    root.className = "pane-chat";

    root.innerHTML =
      '<div class="chat-safe-banner" role="status">' +
      '<span class="chat-safe-badge">asistente</span> ' +
      "Memoria de conversación activa — no envía órdenes " +
      '<button type="button" class="btn secondary" id="chat-clear" style="margin-left:0.5em">Limpiar memoria</button>' +
      "</div>" +
      '<div class="chat-chips pane-row" id="chat-chips"></div>' +
      '<div class="chat-history" id="chat-history" aria-live="polite"></div>' +
      '<form class="chat-compose" id="chat-form">' +
      '<input type="text" id="chat-input" maxlength="2000" ' +
      'placeholder="Hablame natural: planes, dudas, «dale», «siguiente paso»…" autocomplete="off" />' +
      '<button type="submit" class="btn" id="chat-send">Enviar</button>' +
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

    function sendMessage(msg) {
      const trimmed = (msg || "").trim();
      if (!trimmed) return;
      appendBubble("user", trimmed);
      meta.textContent = "…";
      QLApi.chat(trimmed, { pane: "chat", guided_lab: true })
        .then(function (data) {
          appendBubble("assistant", data.reply || "(sin respuesta)");
          memoryTurns = data.memory_turns || memoryTurns;
          const tools = (data.tools_used || []).join(", ") || "—";
          const prov = data.provider || "?";
          meta.textContent =
            "memoria=" +
            String(data.memory_turns || memoryTurns) +
            " · provider=" +
            prov +
            " · tools: " +
            tools +
            " · live_blocked=" +
            String(data.live_blocked !== false);
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
              "Soy tu asistente QuantLab con memoria.\n\n" +
                "Hablame como a un colega: «vamos a correr alpha en Binance», " +
                "después «dale» o «siguiente paso», y sigo el hilo.\n\n" +
                "Con QUANTLAB_LLM_API_KEY en .env respondo más natural (OpenAI-compatible)."
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

    QUICK_CHIPS.forEach(function (label) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn secondary chat-chip";
      btn.textContent = label;
      btn.addEventListener("click", function () {
        sendMessage(label);
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
          String(t.memory_turns || memoryTurns) +
          " · safe_mode=" +
          String(t.safe_mode !== false);
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
