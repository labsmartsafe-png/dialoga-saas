/**
 * dashboard.js - Renderiza métricas e listas no dashboard.
 */
(async function () {
  const alertArea = document.getElementById("alert-area");

  function showError(msg) {
    alertArea.innerHTML = `<div class="alert alert-error">${msg}</div>`;
  }

  const user = await WFAuth.requireAuth();
  if (!user) return;
  WFAuth.renderUserChip(document.getElementById("user-area"), user);

  async function load() {
    try {
      const m = await WFApi.metrics();
      renderMetrics(m);
      renderChart(m.leads_by_day || []);
      renderFlows(m.recent_flows || []);
      renderLeads(m.recent_leads || []);
    } catch (e) {
      console.error(e);
      showError("Não foi possível carregar as métricas. Faça login novamente.");
    }
  }

  function renderMetrics(m) {
    document.getElementById("m-flows").textContent = m.flows_count;
    document.getElementById("m-flows-active").textContent = m.active_flows_count;
    document.getElementById("m-leads").textContent = m.leads_count;
    document.getElementById("m-leads-today").textContent = m.leads_today;
    document.getElementById("m-leads-week").textContent = m.leads_this_week;
    document.getElementById("m-conv").textContent = m.conversations_total;
    document.getElementById("m-conv-sim").textContent = m.conversations_simulated;
    document.getElementById("m-conv-real").textContent = m.conversations_real;
  }

  function renderChart(days) {
    const container = document.getElementById("bar-chart");
    if (!days.length) {
      container.innerHTML = `<div class="empty-state">Sem dados ainda.</div>`;
      return;
    }
    const max = Math.max(...days.map(d => d.count), 1);
    container.innerHTML = days.map(d => {
      const pct = (d.count / max) * 100;
      const day = new Date(d.date).toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit" });
      return `
        <div class="bar" style="height: ${pct}%;">
          <span class="value">${d.count}</span>
          <span class="label">${day}</span>
        </div>
      `;
    }).join("");
  }

  function renderFlows(flows) {
    const c = document.getElementById("recent-flows");
    if (!flows.length) {
      c.innerHTML = `<div class="empty-state"><div class="icon">&#129302;</div>Nenhum fluxo ainda.<br><a href="builder.html" class="btn btn-primary btn-sm mt-2">Criar primeiro fluxo</a></div>`;
      return;
    }
    c.innerHTML = flows.map(f => `
      <div class="list-item">
        <div class="info">
          <h4><a href="builder.html?flow=${f.id}">${escapeHtml(f.name)}</a></h4>
          <small>${f.node_count} nós &#183; ${f.active ? "Ativo" : "Inativo"}</small>
        </div>
        <a href="builder.html?flow=${f.id}" class="btn btn-secondary btn-sm">Editar</a>
      </div>
    `).join("");
  }

  function renderLeads(leads) {
    const c = document.getElementById("recent-leads");
    if (!leads.length) {
      c.innerHTML = `<div class="empty-state"><div class="icon">&#127919;</div>Nenhum lead capturado ainda. <br>Teste um fluxo no simulador!</div>`;
      return;
    }
    c.innerHTML = `
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>Nome</th><th>Telefone</th><th>Status</th><th>Quando</th></tr></thead>
          <tbody>
            ${leads.map(l => `
              <tr>
                <td>${escapeHtml(l.name || "&#8212;")}</td>
                <td>${escapeHtml(l.phone || "&#8212;")}</td>
                <td><span class="badge">${escapeHtml(l.status || "novo")}</span></td>
                <td>${formatDate(l.created_at)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function formatDate(iso) {
    if (!iso) return "&#8212;";
    try {
      return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
    } catch { return iso; }
  }

  document.getElementById("btn-refresh").addEventListener("click", load);
  load();
})();
