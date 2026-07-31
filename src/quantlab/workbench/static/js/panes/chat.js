/** Panel Chat IA — mentor QuantLab (mapa paneles · abrir · explicar · safe). */
(function (global) {
  "use strict";

  var SUGGESTIONS = [
    { label: "Mapa", msg: "Mapa de paneles: ¿para qué sirve cada uno?" },
    { label: "Scanner", msg: "Explicame el Alpha Scanner" },
    { label: "Simulador", msg: "Cómo uso el Simulador para comparar" },
    { label: "Monte Carlo", msg: "Explicame los parámetros de Monte Carlo uno por uno" },
    { label: "Abrir Sim", msg: "Abrí el Simulador" },
    { label: "Empezar", msg: "Cómo empiezo en QuantLab" },
  ];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Markdown mínimo seguro: **negrita**, listas, saltos. */
  function formatAssistantHtml(text) {
    var lines = String(text || "").split("\n");
    var html = [];
    var inList = false;
    function closeList() {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
    }
    function inlineFmt(line) {
      return esc(line).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    }
    lines.forEach(function (raw) {
      var line = raw.replace(/\s+$/, "");
      var m = line.match(/^(\s*)([•\-\*]|\d+\.)\s+(.+)$/);
      if (m) {
        if (!inList) {
          html.push('<ul class="chat-list">');
          inList = true;
        }
        html.push("<li>" + inlineFmt(m[3]) + "</li>");
        return;
      }
      closeList();
      if (!line.trim()) {
        html.push("<br/>");
        return;
      }
      html.push("<p>" + inlineFmt(line) + "</p>");
    });
    closeList();
    return html.join("") || "<p>(sin respuesta)</p>";
  }

  function createChatPane() {
    const root = document.createElement("div");
    root.className = "pane-chat";

    root.innerHTML =
      '<div class="chat-safe-banner" role="status">' +
      '<span class="chat-safe-badge">asistente</span> ' +
      "<span>Mentor del lab · abre paneles · sin órdenes LIVE</span> " +
      '<button type="button" class="btn secondary" id="chat-clear" ' +
      'data-tip="Borra el historial local del chat.">Limpiar</button>' +
      "</div>" +
      '<div class="chat-suggestions" id="chat-suggestions"></div>' +
      '<div class="chat-history" id="chat-history" aria-live="polite"></div>' +
      '<div class="chat-status muted mono" id="chat-status" hidden></div>' +
      '<form class="chat-compose" id="chat-form">' +
      '<input type="text" id="chat-input" maxlength="2000" ' +
      'placeholder="Ej: explicame Monte Carlo · abrí Simulador…" autocomplete="off" />' +
      '<button type="submit" class="btn" id="chat-send">Enviar</button>' +
      "</form>";

    const history = root.querySelector("#chat-history");
    const form = root.querySelector("#chat-form");
    const input = root.querySelector("#chat-input");
    const sendBtn = root.querySelector("#chat-send");
    const statusEl = root.querySelector("#chat-status");
    const sugBox = root.querySelector("#chat-suggestions");
    var busy = false;

    SUGGESTIONS.forEach(function (s) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "chat-chip";
      b.textContent = s.label;
      b.title = s.msg;
      b.addEventListener("click", function () {
        if (busy) return;
        input.value = s.msg;
        sendMessage(s.msg);
        input.value = "";
      });
      sugBox.appendChild(b);
    });

    function setBusy(on) {
      busy = !!on;
      sendBtn.disabled = busy;
      input.disabled = busy;
      if (busy) {
        statusEl.hidden = false;
        statusEl.textContent = "Pensando…";
      } else {
        statusEl.hidden = true;
        statusEl.textContent = "";
      }
    }

    function appendBubble(role, text, meta) {
      const div = document.createElement("div");
      div.className = "chat-bubble chat-" + role;
      if (role === "assistant") {
        div.innerHTML = formatAssistantHtml(text);
        if (meta && meta.provider) {
          var badge = document.createElement("div");
          badge.className = "chat-meta muted mono";
          badge.textContent =
            "vía " +
            meta.provider +
            (meta.tools && meta.tools.length
              ? " · " + meta.tools.slice(0, 4).join(", ")
              : "");
          div.appendChild(badge);
        }
      } else {
        div.textContent = text;
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

    function openPanesHint() {
      var open = [];
      try {
        var wm = window.QLShell && QLShell.wm;
        if (wm && wm.windows) {
          wm.windows.forEach(function (_rec, id) {
            open.push(String(id));
          });
        }
      } catch (e) {}
      return open.slice(0, 12);
    }

    function sendMessage(msg) {
      const trimmed = (msg || "").trim();
      if (!trimmed || busy) return;
      appendBubble("user", trimmed);
      setBusy(true);
      var ctx = {
        pane: "chat",
        open_panes: openPanesHint(),
        focus: "workbench",
      };
      QLApi.chat(trimmed, ctx)
        .then(function (data) {
          appendBubble("assistant", data.reply || "(sin respuesta)", {
            provider: data.provider,
            tools: data.tools_used || [],
          });
          runActions(data.actions || []);
        })
        .catch(function (err) {
          appendBubble(
            "assistant",
            "No pude responder: " +
              (err.message || String(err)) +
              "\n\nProbá reformular o pedime «mapa de paneles»."
          );
        })
        .then(function () {
          setBusy(false);
          input.focus();
        });
    }

    function loadHistory() {
      return QLApi.chatHistory()
        .then(function (data) {
          const msgs = data.messages || [];
          if (!msgs.length) {
            appendBubble(
              "system",
              "Soy tu mentor de QuantLab.\n\n" +
                "Te ayudo con Scanner, Simulador, Monte Carlo, Guided Lab y Mis simulaciones.\n" +
                "Puedo abrir paneles. No envío órdenes (LIVE_BLOCKED).\n\n" +
                "Probá un chip arriba o preguntá en castellano."
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
          appendBubble(
            "system",
            "Asistente QuantLab — memoria local. Preguntá por Scanner, Simulador o Monte Carlo."
          );
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

    root.refresh = async function () {};

    loadHistory();
    return root;
  }

  global.QLPanes = global.QLPanes || {};
  global.QLPanes.createChatPane = createChatPane;
})(window);
