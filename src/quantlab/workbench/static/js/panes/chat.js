/** Panel Chat IA — safe-by-default (Fase 22). */
(function (global) {
  "use strict";

  function createChatPane() {
    const root = document.createElement("div");
    root.className = "pane-chat";

    root.innerHTML =
      '<div class="chat-safe-banner" role="status">' +
      '<span class="chat-safe-badge">safe-mode</span> ' +
      "Asistente research — no envía órdenes" +
      "</div>" +
      '<div class="chat-history" id="chat-history" aria-live="polite"></div>' +
      '<form class="chat-compose" id="chat-form">' +
      '<input type="text" id="chat-input" maxlength="2000" ' +
      'placeholder="Preguntá por salud, modo, backtest, LIVE…" autocomplete="off" />' +
      '<button type="submit" class="btn" id="chat-send">Enviar</button>' +
      "</form>" +
      '<p class="muted mono chat-meta" id="chat-meta">tools —</p>';

    const history = root.querySelector("#chat-history");
    const form = root.querySelector("#chat-form");
    const input = root.querySelector("#chat-input");
    const meta = root.querySelector("#chat-meta");

    function appendBubble(role, text) {
      const div = document.createElement("div");
      div.className = "chat-bubble chat-" + role;
      div.textContent = text;
      history.appendChild(div);
      history.scrollTop = history.scrollHeight;
    }

    appendBubble(
      "system",
      "Hola. Soy el asistente research de QuantLab. Solo lectura/explicación; LIVE bloqueado."
    );

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      const msg = (input.value || "").trim();
      if (!msg) return;
      input.value = "";
      appendBubble("user", msg);
      meta.textContent = "…";
      QLApi.chat(msg)
        .then(function (data) {
          appendBubble("assistant", data.reply || "(sin respuesta)");
          const tools = (data.tools_used || []).join(", ") || "—";
          meta.textContent =
            "tools: " +
            tools +
            " · mode=" +
            (data.mode || "?") +
            " · live_blocked=" +
            String(data.live_blocked !== false);
        })
        .catch(function (err) {
          appendBubble("assistant", "Error: " + err.message);
          meta.textContent = "error";
        });
    });

    root.refresh = async function () {
      try {
        const t = await QLApi.chatTools();
        meta.textContent =
          "allowlist: " +
          ((t.allowlist || []).join(", ") || "—") +
          " · safe_mode=" +
          String(t.safe_mode !== false);
      } catch (err) {
        meta.textContent = "tools error: " + err.message;
      }
    };

    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createChatPane = createChatPane;
})(window);
