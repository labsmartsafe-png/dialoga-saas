/**
 * simulator.js - Modal de simulação de chatbot.
 *
 * Usa window.WFSimulator (criado na abertura do modal) para
 * conversar com a API do dIAloga+.
 */
(function (global) {
  const $ = (sel) => document.querySelector(sel);

  let conv = { id: null, finished: false, awaiting_input: false, options: [], bot_message: null, context: {} };
  let sending = false; // BUGFIX: previne envios duplicados

  async function open(flowId) {
    $("#sim-modal").classList.remove("hidden");
    $("#sim-messages").innerHTML = "";
    $("#sim-options").classList.add("hidden");
    $("#sim-options").innerHTML = "";
    $("#sim-context").innerHTML = "";
    sending = false;

    try {
      const res = await WFApi.simulateStart(flowId, { user_name: "Visitante" });
      conv = res;
      renderMessages(res.messages || []);
      renderContext(res.context || {});
      renderCurrentNode(res);
    } catch (e) {
      $("#sim-messages").innerHTML = '<div class="alert alert-error">' + escapeHtml(e.message) + '</div>';
    }
  }

  function close() {
    $("#sim-modal").classList.add("hidden");
    sending = false;
  }

  function renderMessages(msgs) {
    const c = $("#sim-messages");
    c.innerHTML = msgs.map(function (m) {
      const cls = m.sender === "bot" ? "bot" : m.sender === "user" ? "user" : "system";
      return '<div class="chat-bubble ' + cls + '">' + escapeHtml(m.content) + '</div>';
    }).join("");
    c.scrollTop = c.scrollHeight;
  }

  function appendMessage(content, cls) {
    const c = $("#sim-messages");
    const div = document.createElement("div");
    div.className = "chat-bubble " + cls;
    div.textContent = content;
    c.appendChild(div);
    c.scrollTop = c.scrollHeight;
  }

  function renderContext(ctx) {
    const keys = Object.keys(ctx || {});
    if (!keys.length) {
      $("#sim-context").innerHTML = "";
      return;
    }
    $("#sim-context").innerHTML = "<strong>Variaveis capturadas:</strong> " +
      keys.map(function (k) { return '<span class="key">' + escapeHtml(k) + ':</span> ' + escapeHtml(ctx[k]); }).join(" | ");
  }

  function renderCurrentNode(res) {
    conv = res;
    if (res.finished) {
      $("#sim-options").classList.add("hidden");
      $("#sim-options").innerHTML = "";
      $("#sim-input").disabled = true;
      $("#sim-input").placeholder = "Conversa encerrada.";
      appendMessage("Conversa encerrada.", "system");
      return;
    }
    $("#sim-input").disabled = false;
    $("#sim-input").placeholder = "Digite sua resposta...";

    if (res.options && res.options.length) {
      $("#sim-options").classList.remove("hidden");
      $("#sim-options").innerHTML = res.options.map(function (o) {
        return '<button data-opt="' + escapeHtml(o.value || o.label) + '">' + escapeHtml(o.label || o.value) + '</button>';
      }).join("");
      $("#sim-options").querySelectorAll("[data-opt]").forEach(function (btn) {
        btn.addEventListener("click", function () { sendOption(btn.dataset.opt); });
      });
    } else {
      $("#sim-options").classList.add("hidden");
    }
  }

  async function sendOption(value) {
    if (sending) return; // BUGFIX
    sending = true;
    $("#sim-options").classList.add("hidden");
    try {
      const res = await WFApi.simulateMessage({ conversation_id: conv.conversation_id, selected_option: value });
      afterResponse(res);
    } catch (e) {
      appendMessage("Erro: " + e.message, "system");
    } finally {
      sending = false;
    }
  }

  async function sendText(text) {
    if (!text || sending) return; // BUGFIX
    sending = true;
    $("#sim-input").disabled = true;
    try {
      const res = await WFApi.simulateMessage({ conversation_id: conv.conversation_id, text: text });
      afterResponse(res);
    } catch (e) {
      appendMessage("Erro: " + e.message, "system");
    } finally {
      sending = false;
      $("#sim-input").disabled = false;
    }
  }

  function afterResponse(res) {
    renderMessages(res.messages || []);
    renderContext(res.context || {});
    renderCurrentNode(res);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // Eventos
  if ($("#sim-close")) $("#sim-close").addEventListener("click", close);
  if ($("#sim-form")) $("#sim-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const v = $("#sim-input").value.trim();
    if (!v || sending) return;
    $("#sim-input").value = "";
    sendText(v);
  });

  global.WFSimulator = { open: open, close: close };
})(window);
