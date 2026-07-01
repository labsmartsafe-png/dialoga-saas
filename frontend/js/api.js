(function (global) {
  const API_BASE = global.API_BASE || "http://localhost:8000";

  function getToken() {
    return localStorage.getItem("whatsflow_token");
  }
  function setToken(t) {
    if (t) localStorage.setItem("whatsflow_token", t);
  }
  function clearAuth() {
    localStorage.removeItem("whatsflow_token");
    localStorage.removeItem("whatsflow_user");
  }

  async function request(path, opts) {
    opts = opts || {};
    const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    const t = getToken();
    if (t) headers["Authorization"] = "Bearer " + t;
    const url = path.startsWith("http") ? path : API_BASE + path;
    let res;
    try {
      res = await fetch(url, {
        method: opts.method || "GET",
        headers: headers,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
      });
    } catch (e) {
      throw new Error("Nao foi possivel conectar ao backend (" + API_BASE + "). Verifique se esta rodando.");
    }
    let data = null;
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
      throw new Error((data && (data.detail || data.message)) || ("Erro HTTP " + res.status));
    }
    return data;
  }

  global.WFApi = {
    base: API_BASE,
    getToken: getToken,
    setToken: setToken,
    clearAuth: clearAuth,
    register: function (b) { return request("/api/auth/register", { method: "POST", body: b }); },
    login: function (b) { return request("/api/auth/login", { method: "POST", body: b }); },
    me: function () { return request("/api/auth/me"); },
    passwordResetRequest: function (b) { return request("/api/auth/password-reset/request", { method: "POST", body: b }); },
    listTemplates: function () { return request("/api/templates"); },
    importTemplate: function (slug) { return request("/api/templates/" + slug + "/import", { method: "POST" }); },
    listFlows: function () { return request("/api/flows"); },
    getFlow: function (id) { return request("/api/flows/" + id); },
    createFlow: function (b) { return request("/api/flows", { method: "POST", body: b }); },
    updateFlow: function (id, b) { return request("/api/flows/" + id, { method: "PUT", body: b }); },
    deleteFlow: function (id) { return request("/api/flows/" + id, { method: "DELETE" }); },
    simulateStart: function (id, b) { return request("/api/flows/" + id + "/simulate/start", { method: "POST", body: b || {} }); },
    simulateMessage: function (b) { return request("/api/flows/simulate/message", { method: "POST", body: b }); },
    listLeads: function (qs) { return request("/api/leads" + (qs || "")); },
    updateLead: function (id, b) { return request("/api/leads/" + id, { method: "PUT", body: b }); },
    deleteLead: function (id) { return request("/api/leads/" + id, { method: "DELETE" }); },
    exportLeadsUrl: function (qs) { return API_BASE + "/api/leads/export/csv" + (qs || ""); },
    metrics: function () { return request("/api/dashboard/metrics"); },

    // ---- WhatsApp Conexões (Fase 3) ----
    listConnections: function () { return request("/api/whatsapp/connections"); },
    createConnection: function (b) { return request("/api/whatsapp/connections", { method: "POST", body: b }); },
    deleteConnection: function (id) { return request("/api/whatsapp/connections/" + id, { method: "DELETE" }); },
    sendTestMessage: function (id, b) { return request("/api/whatsapp/connections/" + id + "/send-test", { method: "POST", body: b }); },

    // ---- IA + RAG (Fase A) ----
    listKnowledgeBases: function () { return request("/api/ai/knowledge-bases"); },
    createKnowledgeBase: function (b) { return request("/api/ai/knowledge-bases", { method: "POST", body: b }); },
    deleteKnowledgeBase: function (id) { return request("/api/ai/knowledge-bases/" + id, { method: "DELETE" }); },
    indexKnowledge: function (id, b) { return request("/api/ai/knowledge-bases/" + id + "/index", { method: "POST", body: b }); },
    getAiSettings: function () { return request("/api/ai/settings"); },
    updateAiSettings: function (b) { return request("/api/ai/settings", { method: "PUT", body: b }); },
    aiAsk: function (b) { return request("/api/ai/ask", { method: "POST", body: b }); },
  };
})(window);
