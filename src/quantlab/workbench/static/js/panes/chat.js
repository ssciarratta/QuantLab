/** Panel Chat IA — asistente con memoria + acciones UI (abrir/correr). */
(function (global) {
  "use strict";

  function createChatPane() {
    const root = document.createElement("div");
    root.className = "pane-chat";

    root.innerHTML =
      '<div class="chat-safe-banner" role="status">' +
      '<span class="chat-safe-badge">asistente</span> ' +
      "Puede abrir paneles y correr alpha/pipeline (sin órdenes) " +
      '<button type="button" class="btn secondary" id="chat-clear" style="margin-left:0.5em" data-tip="Borra el historial y la memoria local del chat.\nNo afecta otros paneles.">Limpiar memoria</button>' +
      "</div>" +
      '<div class="chat-history" id="chat-history" aria-live="polite"></div>' +
      '<form class="chat-compose" id="chat-form">' +
      '<input type="text" id="chat-input" maxlength="2000" ' +
      'placeholder="Escribí tu mensaje…" autocomplete="off" />' +
      '<button type="submit" class="btn" id="chat-send" data-tip="Envía el mensaje al asistente.\nPuede abrir paneles o correr alpha/pipeline.">Enviar</button>' +
      "</form>";

    const history = root.querySelector("#chat-history");
    const form = root.querySelector("#chat-form");
    const input = root.querySelector("#chat-input");

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
      QLApi.chat(trimmed, { pane: "chat", guided_lab: true })
        .then(function (data) {
          appendBubble("assistant", data.reply || "(sin respuesta)");
          runActions(data.actions || []);
        })
        .catch(function (err) {
          appendBubble("assistant", "Error: " + err.message);
        });
    }

    function loadHistory() {
      return QLApi.chatHistory()
        .then(function (data) {
          const msgs = data.messages || [];
          if (!msgs.length) {
            appendBubble(
              "system",
              "Soy tu asistente QuantLab.\n\n" +
                "Puedo abrir paneles y correr alpha/pipeline (sin órdenes).\n" +
                "Preguntame lo que necesites."
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

    root.querySelector("#chat-clear").addEventListener("click", function () {
      QLApi.chatClear()
        .then(function () {
          history.innerHTML = "";
          loadHistory();
        })
        .catch(function (err) {
          appendBubble("system", "No pude limpiar memoria: " + err.message);
        });
    });

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      const msg = input.value;
      input.value = "";
      sendMessage(msg);
    });

    root.refresh = async function () {
      /* sin panel de tools / allowlist en UI */
    };

    loadHistory();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createChatPane = createChatPane;
})(window);
