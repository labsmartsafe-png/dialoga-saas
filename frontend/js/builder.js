/**
 * builder.js - Editor visual de fluxos do dIAloga+ (versao com canvas).
 */
(async function () {
  const $ = (sel) => document.querySelector(sel);
  const alertArea = $("#alert-area");

  const state = {
    flows: [],
    templates: [],
    currentFlowId: null,
    nodes: [],
    selectedNodeId: null,
  };

  function showAlert(msg, type) {
    type = type || "error";
    alertArea.innerHTML = '<div class="alert alert-' + type + '">' + msg + '</div>';
    setTimeout(function () { alertArea.innerHTML = ""; }, 5000);
  }

  const user = await WFAuth.requireAuth();
  if (!user) return;
  WFAuth.renderUserChip($("#user-area"), user);

  async function init() {
    try {
      const results = await Promise.all([WFApi.listFlows(), WFApi.listTemplates()]);
      state.flows = results[0];
      state.templates = results[1];
      renderFlowsList();
      renderTemplatesList();
      const params = new URLSearchParams(window.location.search);
      const flowId = params.get("flow");
      if (flowId) await loadFlow(parseInt(flowId, 10));
    } catch (e) {
      console.error(e);
      showAlert("Erro ao carregar dados: " + e.message);
    }
  }

  function renderFlowsList() {
    const c = $("#flows-list");
    if (!state.flows.length) {
      c.innerHTML = '<p class="text-muted" style="font-size: 13px;">Nenhum fluxo. Clique em "+ Novo fluxo" abaixo.</p>';
      return;
    }
    c.innerHTML = state.flows.map(function (f) {
      return '<div class="node-item ' + (state.currentFlowId === f.id ? "active" : "") + '" data-flow="' + f.id + '">' +
        '<div class="label">' + escapeHtml(f.name) + '</div>' +
        '<small class="text-muted">' + (f.nodes || []).length + ' nos</small>' +
        '</div>';
    }).join("");
    c.querySelectorAll("[data-flow]").forEach(function (el) {
      el.addEventListener("click", function () { loadFlow(parseInt(el.dataset.flow, 10)); });
    });
  }

  function renderTemplatesList() {
    const c = $("#templates-list");
    c.innerHTML = state.templates.map(function (t) {
      return '<div class="node-item" data-tpl="' + t.slug + '">' +
        '<div class="label">' + t.icon + ' ' + escapeHtml(t.name) + '</div>' +
        '<small class="text-muted">' + t.node_count + ' nos</small>' +
        '</div>';
    }).join("");
    c.querySelectorAll("[data-tpl]").forEach(function (el) {
      el.addEventListener("click", function () { importTemplate(el.dataset.tpl); });
    });
  }

  async function importTemplate(slug) {
    if (!confirm("Importar este template criara um novo fluxo na sua conta. Continuar?")) return;
    try {
      const flow = await WFApi.importTemplate(slug);
      state.flows.unshift(flow);
      renderFlowsList();
      await loadFlow(flow.id);
      showAlert("Template importado com sucesso! Posicoes calculadas automaticamente.", "success");
    } catch (e) {
      showAlert(e.message);
    }
  }

  async function loadFlow(id) {
    try {
      const flow = await WFApi.getFlow(id);
      state.currentFlowId = flow.id;
      state.nodes = (flow.nodes || []).map(function (n) { return Object.assign({}, n); });
      state.selectedNodeId = null;
      $("#flow-name").value = flow.name || "";
      $("#flow-description").value = flow.description || "";
      $("#btn-delete").style.display = "";
      renderFlowsList();
      renderCanvas();
      renderEditor();
    } catch (e) {
      showAlert(e.message);
    }
  }

  function addNode(type) {
    const base = {
      id: "node_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
      type: type,
      content: "",
      next: null,
      position_x: null,
      position_y: null,
    };
    if (type === "question") base.options = [];
    if (type === "input") base.variable = "resposta";
    if (type === "condition") base.condition = { variable: "", equals: "", next: null };
    if (type === "delay") base.delay_seconds = 1;

    // Calcula posicao: coloca em uma area livre (canto inferior direito do canvas)
    const maxX = state.nodes.reduce(function (acc, n) {
      return Math.max(acc, (n.position_x || 0));
    }, 0);
    const maxY = state.nodes.reduce(function (acc, n) {
      return Math.max(acc, (n.position_y || 0));
    }, 0);
    base.position_x = maxX + 280 > 50 ? maxX + 280 : 50;
    base.position_y = maxY + 130 > 50 ? maxY + 130 : 50;

    state.nodes.push(base);
    state.selectedNodeId = base.id;
    renderCanvas();
    renderEditor();
  }

  function deleteNode(id) {
    state.nodes = state.nodes.filter(function (n) { return n.id !== id; });
    // Remove referencias em outros nos
    state.nodes.forEach(function (n) {
      if (n.next === id) n.next = null;
      if (n.options) n.options.forEach(function (o) { if (o.next === id) o.next = null; });
      if (n.condition && n.condition.next === id) n.condition.next = null;
      if (n.fallback === id) n.fallback = null;
    });
    if (state.selectedNodeId === id) state.selectedNodeId = null;
    renderCanvas();
    renderEditor();
  }

  function renderCanvas() {
    if (typeof WFCanvas !== "undefined") {
      // Callback: quando usuario arrasta da porta de saida para entrada
      WFCanvas.onRemoveConnection = function (fromNodeId, target) {
        removeConnection(fromNodeId, target);
      };

      // Callback: quando usuario clica no "+" da seta (estilo n8n)
      WFCanvas.onInsertNodeBetween = function (fromNodeId, target, nodeType) {
        insertNodeBetween(fromNodeId, target, nodeType);
      };
      WFCanvas.renderNodes(
        state.nodes,
        // onSelect
        function (nodeId) {
          state.selectedNodeId = nodeId;
          renderEditor();
        },
        // onMove (drag-and-drop do no)
        function (nodeId, x, y) {
          const n = state.nodes.find(function (item) { return item.id === nodeId; });
          if (n) {
            n.position_x = x;
            n.position_y = y;
          }
          renderCanvas();
        },
        // onConnect (criou nova conexao)
        function (fromNodeId, toNodeId) {
          createConnection(fromNodeId, toNodeId);
        }
      );
    }
  }
  /**
   * Cria uma conexão entre dois nós.
   * Para nós do tipo "question", cria uma nova opção automaticamente.
   */
  function createConnection(fromNodeId, toNodeId) {
    const from = state.nodes.find(function (n) { return n.id === fromNodeId; });
    const to = state.nodes.find(function (n) { return n.id === toNodeId; });
    if (!from || !to) return;

    // Se for uma pergunta, cria uma opção automaticamente
    if (from.type === "question") {
      const opcoes = from.options || [];
      opcoes.push({
        label: "Opção " + (opcoes.length + 1),
        value: "opcao_" + (opcoes.length + 1),
        next: toNodeId,
      });
      from.options = opcoes;
    } else if (from.type === "condition") {
      // Para condição, conecta como "true" (campo next)
      if (!from.condition) from.condition = { variable: "", equals: "", next: null };
      from.condition.next = toNodeId;
    } else {
      // Para outros tipos, usa o campo "next" direto
      from.next = toNodeId;
    }

    renderCanvas();
    renderEditor();
    showAlert("Conexão criada: " + fromNodeId + " -> " + toNodeId, "success");
  }
  /**
   * Remove uma conexao entre dois nos.
   */
  function removeConnection(fromNodeId, target) {
    const from = state.nodes.find(function (n) { return n.id === fromNodeId; });
    if (!from) return;

    if (target.type === "option") {
      // Remove a opcao
      if (from.options && from.options[target.index]) {
        from.options.splice(target.index, 1);
      }
    } else if (target.label === "sim" && from.condition) {
      from.condition.next = null;
    } else if (target.label === "nao") {
      from.fallback = null;
    } else {
      from.next = null;
    }

    renderCanvas();
    renderEditor();
    showAlert("Conexao removida.", "info");
  }

  function renderEditor() {
    const empty = $("#editor-empty");
    const form = $("#editor-form");
    const id = state.selectedNodeId;
    if (!id) {
      empty.classList.remove("hidden");
      form.classList.add("hidden");
      form.innerHTML = "";
      return;
    }
    const n = state.nodes.find(function (x) { return x.id === id; });
    if (!n) {
      empty.classList.remove("hidden");
      form.classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    form.classList.remove("hidden");
    form.innerHTML = buildEditorForm(n);
    wireEditor();
  }

  function buildEditorForm(n) {
    let opts = "";
    if (n.type === "question") {
      opts = '<div class="form-group"><label>Opcoes</label><div id="opt-list">' +
        (n.options || []).map(function (o, i) {
          return '<div class="form-group" style="border: 1px solid var(--border); padding: 8px; border-radius: 6px; margin-bottom: 6px;">' +
            '<input class="form-control opt-label" placeholder="Label (visivel)" value="' + escapeHtml(o.label || "") + '" style="margin-bottom: 6px;">' +
            '<input class="form-control opt-value" placeholder="Valor (interno)" value="' + escapeHtml(o.value || "") + '" style="margin-bottom: 6px;">' +
            '<input class="form-control opt-next" placeholder="Proximo no (id)" value="' + escapeHtml(o.next || "") + '" style="margin-bottom: 6px;">' +
            '<button class="btn btn-danger btn-sm" data-del-opt="' + i + '">Remover</button>' +
            '</div>';
        }).join("") + '</div><button class="btn btn-secondary btn-sm" id="btn-add-opt">+ Adicionar opcao</button></div>';
    } else if (n.type === "condition") {
      opts = '<div class="form-group"><label>Variavel</label>' +
        '<input class="form-control" id="cond-var" value="' + escapeHtml((n.condition || {}).variable || "") + '"></div>' +
        '<div class="form-group"><label>Equals</label>' +
        '<input class="form-control" id="cond-eq" value="' + escapeHtml((n.condition || {}).equals || "") + '"></div>' +
        '<div class="form-group"><label>Proximo (se verdadeiro)</label>' +
        '<input class="form-control" id="cond-next" value="' + escapeHtml((n.condition || {}).next || "") + '"></div>' +
        '<div class="form-group"><label>Fallback (opcional)</label>' +
        '<input class="form-control" id="cond-fallback" value="' + escapeHtml(n.fallback || "") + '"></div>';
    }

    let extra = "";
    if (n.type === "input" || n.type === "question") {
      extra = '<div class="form-group"><label>Variavel a salvar</label>' +
        '<input class="form-control" id="n-var" value="' + escapeHtml(n.variable || "") + '" placeholder="ex: nome"></div>';
    } else if (n.type === "delay") {
      extra = '<div class="form-group"><label>Segundos de espera</label>' +
        '<input class="form-control" id="n-delay" type="number" min="0" value="' + (n.delay_seconds || 1) + '"></div>';
    }

    // Painel de conexoes deste no (substitui o campo "next" por visual)
    let connectionsPanel = '<div class="form-group"><label>Conexoes deste no</label>';
    connectionsPanel += '<div id="conn-list" style="background: #f9fafb; padding: 8px; border-radius: 6px; min-height: 30px;">';
    if (n.type === "question") {
      connectionsPanel += '<p class="text-muted" style="font-size: 12px; margin-bottom: 8px;">Conexoes sao criadas automaticamente como opcoes. Veja abaixo.</p>';
    } else {
      const mainNext = n.next;
      connectionsPanel += '<div style="display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 4px 0;">' +
        '<span style="color: var(--primary);">→</span>' +
        (mainNext ? '<span>' + escapeHtml(mainNext) + '</span> <button class="btn btn-danger btn-sm" data-rm-conn="main" style="margin-left: auto;">X</button>' : '<span class="text-muted">Sem conexao (fim de fluxo)</span>') +
        '</div>';
      if (n.condition && n.condition.next) {
        connectionsPanel += '<div style="display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 4px 0; margin-top: 4px;">' +
          '<span style="color: #10b981; font-weight: 600;">se sim:</span>' +
          '<span>' + escapeHtml(n.condition.next) + '</span> <button class="btn btn-danger btn-sm" data-rm-conn="sim" style="margin-left: auto;">X</button>' +
          '</div>';
      }
      if (n.fallback) {
        connectionsPanel += '<div style="display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 4px 0; margin-top: 4px;">' +
          '<span style="color: #f59e0b; font-weight: 600;">se nao:</span>' +
          '<span>' + escapeHtml(n.fallback) + '</span> <button class="btn btn-danger btn-sm" data-rm-conn="nao" style="margin-left: auto;">X</button>' +
          '</div>';
      }
    }
    connectionsPanel += '<p class="text-muted" style="font-size: 11px; margin-top: 8px;">Arraste da bolinha direita de um no ate outro para criar uma conexao.</p>';
    connectionsPanel += '</div></div>';

    return '<div class="form-group"><label>Tipo</label>' +
      '<input class="form-control" disabled value="' + n.type + '"></div>' +
      '<div class="form-group"><label>ID do no</label>' +
      '<input class="form-control" id="n-id" value="' + escapeHtml(n.id) + '"></div>' +
      '<div class="form-group"><label>Conteudo / Mensagem</label>' +
      '<textarea class="form-control" id="n-content" placeholder="Use {{variavel}} para substituir valores do contexto">' + escapeHtml(n.content || "") + '</textarea></div>' +
      extra + opts +
      connectionsPanel +
      '<div class="flex gap-1 mt-2">' +
      '<button class="btn btn-primary btn-sm" id="btn-apply">Aplicar</button>' +
      '<button class="btn btn-danger btn-sm" id="btn-del">Excluir no</button>' +
      '</div>';
  }

  function wireEditor() {
    const id = state.selectedNodeId;
    const n = state.nodes.find(function (x) { return x.id === id; });
    if (!n) return;

    $("#btn-apply").addEventListener("click", function () {
      n.id = $("#n-id").value || n.id;
      n.content = $("#n-content").value || "";
      const varInput = $("#n-var");
      if (varInput) n.variable = varInput.value || null;
      const delayInput = $("#n-delay");
      if (delayInput) n.delay_seconds = parseInt(delayInput.value, 10) || 0;

      if (n.type === "question") {
        const opts = [];
        $("#opt-list").querySelectorAll("[data-del-opt]").forEach(function (el) {
          const p = el.parentElement;
          const lbl = p.querySelector(".opt-label").value;
          const val = p.querySelector(".opt-value").value;
          const nx = p.querySelector(".opt-next").value;
          if (lbl || val) opts.push({ label: lbl, value: val || lbl, next: nx || null });
        });
        n.options = opts;
      } else if (n.type === "condition") {
        n.condition = {
          variable: $("#cond-var").value || "",
          equals: $("#cond-eq").value || "",
          next: $("#cond-next").value || null,
        };
        n.fallback = $("#cond-fallback").value || null;
      }
      renderCanvas();
      showAlert("Alteracoes aplicadas (clique em Salvar para persistir).", "info");
    });

    $("#btn-del").addEventListener("click", function () {
      if (confirm("Excluir este no?")) deleteNode(id);
    });

    // Botoes para remover conexao
    $("#conn-list").querySelectorAll("[data-rm-conn]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const tipo = btn.dataset.rmConn;
        removeConnection(id, { type: tipo === "main" ? "main" : (tipo === "sim" ? "main" : "main"), label: tipo });
      });
    });

    if (n.type === "question") {
      const btnAdd = $("#btn-add-opt");
      if (btnAdd) btnAdd.addEventListener("click", function () {
        n.options = n.options || [];
        n.options.push({ label: "", value: "", next: null });
        renderEditor();
      });
      $("#opt-list").querySelectorAll("[data-del-opt]").forEach(function (el) {
        el.addEventListener("click", function () {
          const i = parseInt(el.dataset.delOpt, 10);
          n.options.splice(i, 1);
          renderEditor();
        });
      });
    }
  }

  document.querySelectorAll("[data-add]").forEach(function (btn) {
    btn.addEventListener("click", function () { addNode(btn.dataset.add); });
  });

  $("#btn-new-flow").addEventListener("click", async function () {
    const name = prompt("Nome do novo fluxo:");
    if (!name) return;
    try {
      const flow = await WFApi.createFlow({ name: name, description: "", nodes: [] });
      state.flows.unshift(flow);
      renderFlowsList();
      await loadFlow(flow.id);
      showAlert("Fluxo criado!", "success");
    } catch (e) {
      showAlert(e.message);
    }
  });

  $("#btn-save").addEventListener("click", async function () {
    if (!state.currentFlowId) {
      showAlert("Selecione ou crie um fluxo primeiro.");
      return;
    }
    const btn = $("#btn-save");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Salvando...';
    try {
      await WFApi.updateFlow(state.currentFlowId, {
        name: $("#flow-name").value,
        description: $("#flow-description").value,
        nodes: state.nodes,
        start_node_id: state.nodes.length ? state.nodes[0].id : null,
      });
      showAlert("Fluxo salvo com sucesso!", "success");
      const updated = await WFApi.getFlow(state.currentFlowId);
      const idx = state.flows.findIndex(function (f) { return f.id === updated.id; });
      if (idx >= 0) state.flows[idx] = updated;
      renderFlowsList();
    } catch (e) {
      showAlert(e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Salvar";
    }
  });

  $("#btn-test").addEventListener("click", function () {
    if (!state.currentFlowId) {
      showAlert("Salve o fluxo antes de testar.");
      return;
    }
    WFApi.updateFlow(state.currentFlowId, {
      name: $("#flow-name").value,
      description: $("#flow-description").value,
      nodes: state.nodes,
      start_node_id: state.nodes.length ? state.nodes[0].id : null,
    }).then(function () {
      if (typeof WFSimulator !== "undefined" && WFSimulator.open) {
        WFSimulator.open(state.currentFlowId);
      } else {
        showAlert("Simulador nao carregado. Recarregue a pagina (Ctrl+F5).", "error");
      }
    }).catch(function (err) { showAlert("Erro ao preparar teste: " + err.message); });
  });

  $("#btn-delete").addEventListener("click", async function () {
    if (!state.currentFlowId) {
      showAlert("Selecione um fluxo primeiro.");
      return;
    }
    const flowName = $("#flow-name").value || "este fluxo";
    if (!confirm("Tem certeza que deseja EXCLUIR o fluxo \"" + flowName + "\"?")) return;
    const btn = $("#btn-delete");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Excluindo...';
    try {
      await WFApi.deleteFlow(state.currentFlowId);
      showAlert("Fluxo excluido!", "success");
      state.currentFlowId = null;
      state.nodes = [];
      state.selectedNodeId = null;
      $("#flow-name").value = "";
      $("#flow-description").value = "";
      $("#btn-delete").style.display = "none";
      renderCanvas();
      renderEditor();
      const flows = await WFApi.listFlows();
      state.flows = flows;
      renderFlowsList();
    } catch (err) {
      showAlert("Erro ao excluir: " + err.message);
      btn.disabled = false;
      btn.textContent = "Excluir";
    }
  });

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // ============ UNDO/REDO ============
  const history = {
    stack: [],
    current: -1,
    max: 50,

    save: function (state) {
      // Remove estados futuros (se estamos no meio do historico)
      this.stack = this.stack.slice(0, this.current + 1);
      // Salva snapshot
      this.stack.push(JSON.stringify(state));
      this.current++;
      // Limita tamanho
      if (this.stack.length > this.max) {
        this.stack.shift();
        this.current--;
      }
    },

    undo: function () {
      if (this.current <= 0) return null;
      this.current--;
      return JSON.parse(this.stack[this.current]);
    },

    redo: function () {
      if (this.current >= this.stack.length - 1) return null;
      this.current++;
      return JSON.parse(this.stack[this.current]);
    },

    canUndo: function () { return this.current > 0; },
    canRedo: function () { return this.current < this.stack.length - 1; }
  };

  function saveHistory() {
    history.save({
      nodes: state.nodes,
      selectedNodeId: state.selectedNodeId,
      flowName: document.getElementById("flow-name").value,
      flowDescription: document.getElementById("flow-description").value,
    });
  }

  function undo() {
    const snap = history.undo();
    if (!snap) return;
    state.nodes = snap.nodes || [];
    state.selectedNodeId = snap.selectedNodeId || null;
    if (snap.flowName !== undefined) document.getElementById("flow-name").value = snap.flowName;
    if (snap.flowDescription !== undefined) document.getElementById("flow-description").value = snap.flowDescription;
    renderCanvas();
    renderEditor();
    showAlert("Desfeito (Ctrl+Z)", "info");
  }

  function redo() {
    const snap = history.redo();
    if (!snap) return;
    state.nodes = snap.nodes || [];
    state.selectedNodeId = snap.selectedNodeId || null;
    if (snap.flowName !== undefined) document.getElementById("flow-name").value = snap.flowName;
    if (snap.flowDescription !== undefined) document.getElementById("flow-description").value = snap.flowDescription;
    renderCanvas();
    renderEditor();
    showAlert("Refeito (Ctrl+Y)", "info");
  }

  // ============ AUTO-SAVE ============
  let lastSavedSnapshot = null;
  let autoSaveTimer = null;

  function setupAutoSave() {
    setInterval(function () {
      if (!state.currentFlowId) return;
      const currentSnapshot = JSON.stringify({ nodes: state.nodes, flowName: $("#flow-name").value });
      if (currentSnapshot !== lastSavedSnapshot) {
        autoSave();
      }
    }, 30000); // 30 segundos
  }

  async function autoSave() {
    if (!state.currentFlowId) return;
    try {
      await WFApi.updateFlow(state.currentFlowId, {
        name: $("#flow-name").value,
        description: $("#flow-description").value,
        nodes: state.nodes,
        start_node_id: state.nodes.length ? state.nodes[0].id : null,
      });
      lastSavedSnapshot = JSON.stringify({ nodes: state.nodes, flowName: $("#flow-name").value });
      showAutoSaveIndicator();
    } catch (e) {
      console.error("Auto-save falhou:", e);
    }
  }

  function showAutoSaveIndicator() {
    let indicator = document.getElementById("autosave-indicator");
    if (!indicator) {
      indicator = document.createElement("div");
      indicator.id = "autosave-indicator";
      indicator.style.cssText = "position:fixed;bottom:60px;right:240px;background:linear-gradient(135deg,#06b6d4,#7c3aed);color:white;padding:6px 14px;border-radius:20px;font-size:11px;font-weight:600;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:1000;opacity:0;transition:opacity 0.3s;";
      document.body.appendChild(indicator);
    }
    const ts = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    indicator.textContent = "Salvo " + ts;
    indicator.style.opacity = "1";
    setTimeout(function () { indicator.style.opacity = "0"; }, 2000);
  }

  // ============ DARK MODE ============
  function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
    const enabled = document.body.classList.contains("dark-mode");
    localStorage.setItem("dialoog-dark-mode", enabled ? "1" : "0");
    showAlert(enabled ? "Modo escuro ativado" : "Modo claro ativado", "info");
  }

  function initDarkMode() {
    if (localStorage.getItem("dialoog-dark-mode") === "1") {
      document.body.classList.add("dark-mode");
    }
  }
  initDarkMode();

  // ============ SNAP VISUAL ============
  function setupSnapGuides() {
    // Snap guides serao adicionados ao canvas.js se necessario
    // Por enquanto, snap to grid ja funciona no canvas.js
  }

  // ============ ATALHOS DE TECLADO ============
  function initKeyboardShortcuts() {
    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

      // Ctrl+S = Salvar
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        document.getElementById("btn-save").click();
      }

      // Ctrl+Z = Undo
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === "z") {
        e.preventDefault();
        undo();
      }

      // Ctrl+Y ou Ctrl+Shift+Z = Redo
      if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.shiftKey && e.key === "Z"))) {
        e.preventDefault();
        redo();
      }

      // Delete = Deletar no selecionado
      if (e.key === "Delete" && state.selectedNodeId) {
        e.preventDefault();
        if (confirm("Excluir este no?")) {
          deleteNode(state.selectedNodeId);
          saveHistory();
        }
      }

      // F = Fit to screen
      if (e.key === "f" && typeof WFCanvas !== "undefined") {
        WFCanvas.fitToScreen();
      }

      // D = Toggle dark mode
      if (e.key === "d" && !e.ctrlKey && !e.metaKey) {
        toggleDarkMode();
      }

      // Ctrl+D = Duplicar no selecionado
      if ((e.ctrlKey || e.metaKey) && e.key === "d" && state.selectedNodeId) {
        e.preventDefault();
        duplicateNode(state.selectedNodeId);
      }
    });
  }

  function duplicateNode(nodeId) {
    const original = state.nodes.find(function (n) { return n.id === nodeId; });
    if (!original) return;
    const copy = JSON.parse(JSON.stringify(original));
    copy.id = "node_" + Date.now() + "_" + Math.floor(Math.random() * 1000);
    copy.position_x = (original.position_x || 0) + 50;
    copy.position_y = (original.position_y || 0) + 50;
    state.nodes.push(copy);
    state.selectedNodeId = copy.id;
    renderCanvas();
    renderEditor();
    saveHistory();
    showAlert("No duplicado!", "success");
  }

    /**
   * Insere um novo nó entre dois nós conectados.
   * Chamado pelo menu suspenso da conexão.
   * nodeType: tipo do nó a inserir (message, question, input, etc.)
   */
  function insertNodeBetween(fromNodeId, target, nodeType) {
    nodeType = nodeType || "message"; // padrão se não vier
    const from = state.nodes.find(function (n) { return n.id === fromNodeId; });
    if (!from) return;

    const fromPos = { x: from.position_x || 0, y: from.position_y || 0 };
    const targetPos = getNodePosition(target.id);
    if (!targetPos) return;

    const midX = (fromPos.x + targetPos.x) / 2;
    const midY = (fromPos.y + targetPos.y) / 2;

    const newNodeId = "node_" + Date.now() + "_" + Math.floor(Math.random() * 1000);
    const newNode = {
      id: newNodeId,
      type: nodeType,
      content: "Novo nó (clique para editar)",
      next: target.id,
      position_x: Math.round(midX / 20) * 20,
      position_y: Math.round(midY / 20) * 20,
    };

    // Inicializa campos extras conforme o tipo
    if (nodeType === "question") newNode.options = [];
    if (nodeType === "input") newNode.variable = "resposta";
    if (nodeType === "condition") newNode.condition = { variable: "", equals: "", next: null };
    if (nodeType === "delay") newNode.delay_seconds = 1;
    if (nodeType === "human" || nodeType === "end") newNode.content = "";

    // Reconecta o nó origem para apontar para o novo nó
    if (target.type === "option") {
      from.options[target.index].next = newNodeId;
    } else if (target.type === "condition") {
      from.condition.next = newNodeId;
    } else if (target.label === "se não") {
      from.fallback = newNodeId;
    } else {
      from.next = newNodeId;
    }

    state.nodes.push(newNode);
    state.selectedNodeId = newNodeId;
    renderCanvas();
    renderEditor();
    saveHistory();

    const typeLabels = {
      message: "Mensagem", question: "Pergunta", input: "Entrada",
      condition: "Condição", delay: "Espera", webhook: "Webhook",
      human: "Humano", end: "Fim"
    };
    showAlert("Nó " + (typeLabels[nodeType] || nodeType) + " inserido!", "success");
  }

  function getNodePosition(nodeId) {
    var n = state.nodes.find(function (item) { return item.id === nodeId; });
    if (!n) return null;
    return { x: n.position_x || 0, y: n.position_y || 0 };
  }

  // Modifica funcoes existentes para salvar historico
  var origAddNode = addNode;
  addNode = function (type) {
    origAddNode(type);
    saveHistory();
  };

  var origDeleteNode = deleteNode;
  deleteNode = function (id) {
    origDeleteNode(id);
    saveHistory();
  };

  var origCreateConnection = createConnection;
  createConnection = function (fromNodeId, toNodeId) {
    origCreateConnection(fromNodeId, toNodeId);
    saveHistory();
  };

  var origRemoveConnection = removeConnection;
  removeConnection = function (fromNodeId, target) {
    origRemoveConnection(fromNodeId, target);
    saveHistory();
  };

  initKeyboardShortcuts();
  setupAutoSave();

  // Botoes de Undo/Redo e Dark Mode
  document.getElementById("btn-undo").addEventListener("click", undo);
  document.getElementById("btn-redo").addEventListener("click", redo);
  document.getElementById("btn-dark-mode").addEventListener("click", toggleDarkMode);

  // Salva estado inicial quando carrega fluxo
  var origLoadFlow = loadFlow;
  loadFlow = async function (id) {
    await origLoadFlow(id);
    // Reseta historico
    history.stack = [];
    history.current = -1;
    saveHistory();
    lastSavedSnapshot = JSON.stringify({ nodes: state.nodes, flowName: $("#flow-name").value });
  };

  init();
})();
