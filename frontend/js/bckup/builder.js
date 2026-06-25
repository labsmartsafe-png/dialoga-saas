/**
 * builder.js - Editor visual de fluxos.
 */
(async function () {
  const $ = (sel) => document.querySelector(sel);
  const alertArea = $("#alert-area");

  const state = {
    flows: [],
    templates: [],
    currentFlowId: null,
    nodes: [],
    selectedNodeIdx: -1,
  };

  function showAlert(msg, type = "error") {
    alertArea.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    setTimeout(() => { alertArea.innerHTML = ""; }, 5000);
  }

  const user = await WFAuth.requireAuth();
  if (!user) return;
  WFAuth.renderUserChip($("#user-area"), user);

  // ============ Inicialização ============
  async function init() {
    try {
      const [flows, templates] = await Promise.all([
        WFApi.listFlows(),
        WFApi.listTemplates(),
      ]);
      state.flows = flows;
      state.templates = templates;
      renderFlowsList();
      renderTemplatesList();

      // Verifica se veio um flow específico na URL
      const params = new URLSearchParams(window.location.search);
      const flowId = params.get("flow");
      if (flowId) {
        await loadFlow(parseInt(flowId, 10));
      }
    } catch (e) {
      console.error(e);
      showAlert("Erro ao carregar dados.");
    }
  }

  function renderFlowsList() {
    const c = $("#flows-list");
    if (!state.flows.length) {
      c.innerHTML = `<p class="text-muted" style="font-size: 13px;">Nenhum fluxo.</p>`;
      return;
    }
    c.innerHTML = state.flows.map(f => `
      <div class="node-item ${state.currentFlowId === f.id ? 'active' : ''}" data-flow="${f.id}">
        <div class="label">${escapeHtml(f.name)}</div>
        <small class="text-muted">${(f.nodes || []).length} nós</small>
      </div>
    `).join("");
    c.querySelectorAll("[data-flow]").forEach(el => {
      el.addEventListener("click", () => loadFlow(parseInt(el.dataset.flow, 10)));
    });
  }

  function renderTemplatesList() {
    const c = $("#templates-list");
    c.innerHTML = state.templates.map(t => `
      <div class="node-item" data-tpl="${t.slug}">
        <div class="label">${t.icon} ${escapeHtml(t.name)}</div>
        <small class="text-muted">${t.node_count} nós &#183; ${escapeHtml(t.category)}</small>
      </div>
    `).join("");
    c.querySelectorAll("[data-tpl]").forEach(el => {
      el.addEventListener("click", () => importTemplate(el.dataset.tpl));
    });
  }

  async function importTemplate(slug) {
    if (!confirm("Importar este template criará um novo fluxo na sua conta. Continuar?")) return;
    try {
      const flow = await WFApi.importTemplate(slug);
      state.flows.unshift(flow);
      renderFlowsList();
      await loadFlow(flow.id);
      showAlert("Template importado com sucesso!", "success");
    } catch (e) {
      showAlert(e.message);
    }
  }

  async function loadFlow(id) {
    try {
      const flow = await WFApi.getFlow(id);
      state.currentFlowId = flow.id;
      state.nodes = (flow.nodes || []).map(n => ({ ...n }));
      state.selectedNodeIdx = -1;
      $("#flow-name").value = flow.name || "";
      $("#flow-description").value = flow.description || "";
      renderFlowsList();
      renderNodes();
      renderEditor();
    } catch (e) {
      showAlert(e.message);
    }
  }

  // ============ CRUD de nós ============
  function addNode(type) {
    const base = { id: `node_${Date.now()}_${Math.floor(Math.random()*1000)}`, type, content: "", next: null };
    if (type === "question") base.options = [];
    if (type === "input") base.variable = "resposta";
    if (type === "condition") base.condition = { variable: "", equals: "", next: null };
    if (type === "delay") base.delay_seconds = 1;
    state.nodes.push(base);
    state.selectedNodeIdx = state.nodes.length - 1;
    renderNodes();
    renderEditor();
  }

  function deleteNode(idx) {
    state.nodes.splice(idx, 1);
    state.selectedNodeIdx = -1;
    renderNodes();
    renderEditor();
  }

  function renderNodes() {
    const c = $("#nodes-canvas");
    if (!state.nodes.length) {
      c.innerHTML = `<div class="empty-state"><div class="icon">&#128203;</div>Adicione nós usando os botões acima.</div>`;
      return;
    }
    c.innerHTML = state.nodes.map((n, i) => `
      <div class="node-item ${state.selectedNodeIdx === i ? 'active' : ''}" data-idx="${i}">
        <span class="type type-${n.type}">${n.type}</span>
        <div class="label">${escapeHtml((n.content || n.id).slice(0, 80))}</div>
      </div>
    `).join("");
    c.querySelectorAll("[data-idx]").forEach(el => {
      el.addEventListener("click", () => {
        state.selectedNodeIdx = parseInt(el.dataset.idx, 10);
        renderNodes();
        renderEditor();
      });
    });
  }

  function renderEditor() {
    const empty = $("#editor-empty");
    const form = $("#editor-form");
    const idx = state.selectedNodeIdx;
    if (idx < 0 || !state.nodes[idx]) {
      empty.classList.remove("hidden");
      form.classList.add("hidden");
      form.innerHTML = "";
      return;
    }
    empty.classList.add("hidden");
    form.classList.remove("hidden");
    const n = state.nodes[idx];
    form.innerHTML = buildEditorForm(n, idx);
    wireEditor(idx);
  }

  function buildEditorForm(n, idx) {
    let opts = "";
    if (n.type === "question") {
      opts = `
        <div class="form-group">
          <label>Opções</label>
          <div id="opt-list">
            ${(n.options || []).map((o, i) => `
              <div class="form-group" style="border: 1px solid var(--border); padding: 8px; border-radius: 6px; margin-bottom: 6px;">
                <input class="form-control opt-label" placeholder="Label (visível)" value="${escapeHtml(o.label || '')}" style="margin-bottom: 6px;">
                <input class="form-control opt-value" placeholder="Valor (interno)" value="${escapeHtml(o.value || '')}" style="margin-bottom: 6px;">
                <input class="form-control opt-next" placeholder="Próximo nó (id)" value="${escapeHtml(o.next || '')}" style="margin-bottom: 6px;">
                <button class="btn btn-danger btn-sm" data-del-opt="${i}">Remover</button>
              </div>
            `).join("")}
          </div>
          <button class="btn btn-secondary btn-sm" id="btn-add-opt">+ Adicionar opção</button>
        </div>
      `;
    } else if (n.type === "condition") {
      opts = `
        <div class="form-group">
          <label>Variável</label>
          <input class="form-control" id="cond-var" value="${escapeHtml((n.condition || {}).variable || '')}" placeholder="ex: cidade">
        </div>
        <div class="form-group">
          <label>Equals</label>
          <input class="form-control" id="cond-eq" value="${escapeHtml((n.condition || {}).equals || '')}" placeholder="ex: São Paulo">
        </div>
        <div class="form-group">
          <label>Próximo (se verdadeiro)</label>
          <input class="form-control" id="cond-next" value="${escapeHtml((n.condition || {}).next || '')}" placeholder="id do próximo nó">
        </div>
      `;
    }

    let extra = "";
    if (n.type === "input" || n.type === "question") {
      extra = `
        <div class="form-group">
          <label>Variável a salvar</label>
          <input class="form-control" id="n-var" value="${escapeHtml(n.variable || '')}" placeholder="ex: nome">
        </div>
      `;
    } else if (n.type === "delay") {
      extra = `
        <div class="form-group">
          <label>Segundos de espera</label>
          <input class="form-control" id="n-delay" type="number" min="0" value="${n.delay_seconds || 1}">
        </div>
      `;
    }

    return `
      <div class="form-group">
        <label>Tipo</label>
        <input class="form-control" disabled value="${n.type}">
      </div>
      <div class="form-group">
        <label>ID do nó</label>
        <input class="form-control" id="n-id" value="${escapeHtml(n.id)}">
      </div>
      <div class="form-group">
        <label>Conteúdo / Mensagem</label>
        <textarea class="form-control" id="n-content" placeholder="Use {{variavel}} para substituir valores do contexto">${escapeHtml(n.content || '')}</textarea>
      </div>
      ${extra}
      ${opts}
      <div class="form-group">
        <label>Próximo nó (id)</label>
        <input class="form-control" id="n-next" value="${escapeHtml(n.next || '')}" placeholder="Deixe vazio se for fim de fluxo">
      </div>
      <div class="flex gap-1 mt-2">
        <button class="btn btn-primary btn-sm" id="btn-apply">Aplicar</button>
        <button class="btn btn-danger btn-sm" id="btn-del">Excluir nó</button>
      </div>
    `;
  }

  function wireEditor(idx) {
    const n = state.nodes[idx];

    $("#btn-apply").addEventListener("click", () => {
      n.id = $("#n-id").value || n.id;
      n.content = $("#n-content").value || "";
      n.next = $("#n-next").value || null;
      const varInput = $("#n-var");
      if (varInput) n.variable = varInput.value || null;
      const delayInput = $("#n-delay");
      if (delayInput) n.delay_seconds = parseInt(delayInput.value, 10) || 0;

      if (n.type === "question") {
        const opts = [];
        $("#opt-list").querySelectorAll("[data-del-opt]").forEach((el) => {
          const parent = el.parentElement;
          const lbl = parent.querySelector(".opt-label").value;
          const val = parent.querySelector(".opt-value").value;
          const nx = parent.querySelector(".opt-next").value;
          if (lbl || val) opts.push({ label: lbl, value: val || lbl, next: nx || null });
        });
        n.options = opts;
      } else if (n.type === "condition") {
        n.condition = {
          variable: $("#cond-var").value || "",
          equals: $("#cond-eq").value || "",
          next: $("#cond-next").value || null,
        };
      }
      renderNodes();
      showAlert("Alterações aplicadas ao nó (ainda não salvas no fluxo).", "info");
    });

    $("#btn-del").addEventListener("click", () => {
      if (confirm("Excluir este nó?")) deleteNode(idx);
    });

    if (n.type === "question") {
      const btnAdd = $("#btn-add-opt");
      if (btnAdd) btnAdd.addEventListener("click", () => {
        n.options = n.options || [];
        n.options.push({ label: "", value: "", next: null });
        renderEditor();
      });
      $("#opt-list").querySelectorAll("[data-del-opt]").forEach(el => {
        el.addEventListener("click", () => {
          const i = parseInt(el.dataset.delOpt, 10);
          n.options.splice(i, 1);
          renderEditor();
        });
      });
    }
  }

  // ============ Botões principais ============
  document.querySelectorAll("[data-add]").forEach(btn => {
    btn.addEventListener("click", () => addNode(btn.dataset.add));
  });

  $("#btn-new-flow").addEventListener("click", async () => {
    const name = prompt("Nome do novo fluxo:");
    if (!name) return;
    try {
      const flow = await WFApi.createFlow({ name, description: "", nodes: [] });
      state.flows.unshift(flow);
      renderFlowsList();
      await loadFlow(flow.id);
      showAlert("Fluxo criado!", "success");
    } catch (e) {
      showAlert(e.message);
    }
  });

  $("#btn-save").addEventListener("click", async () => {
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
      showAlert("Fluxo salvo com sucesso! &#9989;", "success");
      // Atualiza lista lateral
      const updated = await WFApi.getFlow(state.currentFlowId);
      const idx = state.flows.findIndex(f => f.id === updated.id);
      if (idx >= 0) state.flows[idx] = updated;
      renderFlowsList();
    } catch (e) {
      showAlert(e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "&#128190; Salvar";
    }
  });

  $("#btn-test").addEventListener("click", () => {
    if (!state.currentFlowId) {
      showAlert("Salve o fluxo antes de testar.");
      return;
    }
    // Salva antes de testar
    WFApi.updateFlow(state.currentFlowId, {
      name: $("#flow-name").value,
      description: $("#flow-description").value,
      nodes: state.nodes,
      start_node_id: state.nodes.length ? state.nodes[0].id : null,
    }).then(() => {
      openSimulator(state.currentFlowId);
    }).catch(err => showAlert("Erro ao preparar teste: " + err.message));
  });

  // ============ Util ============
  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  init();
})();
