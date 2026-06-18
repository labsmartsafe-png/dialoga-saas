/**
 * api.js - Cliente HTTP para a API do WhatsFlow.
 *
 * Detecta automaticamente a base da API:
 * - Em produção, usa o mesmo host (window.location.origin).
 * - Em desenvolvimento, pode usar API_BASE customizada via window.API_BASE.
 */
(function (global) {
  const API_BASE = global.API_BASE || global.location.origin;

  function getToken() {
    return localStorage.getItem("whatsflow_token");
  }

  function setToken(token) {
    if (token) localStorage.setItem("whatsflow_token", token);
  }

  function clearAuth() {
    localStorage.removeItem("whatsflow_token");
    localStorage.removeItem("whatsflow_user");
  }

  async function request(path, opts = {}) {
    const headers = Object.assign(
      { "Content-Type": "application/json" },
      opts.headers || {}
    );
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
    const res = await fetch(url, {
      method: opts.method || "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });

    // Tenta parsear JSON; pode vir vazio em 204
    const ct = res.headers.get("content-type") || "";
    let data = null;
    if (ct.includes("application/json")) {
      try { data = await res.json(); } catch (e) { data = null; }
    } else if (res.status !== 204) {
      try { data = await res.text(); } catch (e) { data = null; }
    }

    if (!res.ok) {
      const err = new Error(
        (data && (data.detail || data.message || data.error)) ||
        `Erro HTTP ${res.status}`
      );
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  const api = {
    base: API_BASE,
    getToken,
    setToken,
    clearAuth,

    // Auth
    register: (body) => request("/api/auth/register", { method: "POST", body }),
    login: (body) => request("/api/auth/login", { method: "POST", body }),
    me: () => request("/api/auth/me"),
    passwordResetRequest: (body) => request("/api/auth/password-reset/request", { method: "POST", body }),
    passwordResetConfirm: (body) => request("/api/auth/password-reset/confirm", { method: "POST", body }),

    // Templates
    listTemplates: () => request("/api/templates"),
    getTemplate: (slug) => request(`/api/templates/${slug}`),
    importTemplate: (slug) => request(`/api/templates/${slug}/import`, { method: "POST" }),

    // Flows
    listFlows: () => request("/api/flows"),
    getFlow: (id) => request(`/api/flows/${id}`),
    createFlow: (body) => request("/api/flows", { method: "POST", body }),
    updateFlow: (id, body) => request(`/api/flows/${id}`, { method: "PUT", body }),
    deleteFlow: (id) => request(`/api/flows/${id}`, { method: "DELETE" }),
    simulateStart: (id, body) => request(`/api/flows/${id}/simulate/start`, { method: "POST", body }),
    simulateMessage: (body) => request(`/api/flows/simulate/message`, { method: "POST", body }),

    // Leads
    listLeads: (qs = "") => request(`/api/leads${qs}`),
    updateLead: (id, body) => request(`/api/leads/${id}`, { method: "PUT", body }),
    deleteLead: (id) => request(`/api/leads/${id}`, { method: "DELETE" }),
    exportLeadsUrl: (qs = "") => `${API_BASE}/api/leads/export/csv${qs}`,

    // Dashboard
    metrics: () => request("/api/dashboard/metrics"),

    // WhatsApp
    sendWhatsApp: (body) => request("/api/whatsapp/send", { method: "POST", body }),
  };

  global.WFApi = api;
})(window);
