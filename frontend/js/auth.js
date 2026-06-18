/**
 * auth.js - Helpers de autenticação compartilhados.
 */
(function (global) {
  const api = global.WFApi;

  function isLoggedIn() {
    return !!api.getToken();
  }

  function logout() {
    api.clearAuth();
    global.location.href = "/login.html";
  }

  async function requireAuth() {
    if (!isLoggedIn()) {
      global.location.href = "/login.html";
      return null;
    }
    try {
      const user = await api.me();
      localStorage.setItem("whatsflow_user", JSON.stringify(user));
      return user;
    } catch (e) {
      // Token inválido
      api.clearAuth();
      global.location.href = "/login.html";
      return null;
    }
  }

  function renderUserChip(el, user) {
    if (!el) return;
    el.innerHTML = `
      <span style="font-size: 13px; color: var(--muted);">${user.company_name}</span>
      <button class="btn btn-secondary btn-sm" id="btn-logout">Sair</button>
    `;
    const btn = document.getElementById("btn-logout");
    if (btn) btn.addEventListener("click", logout);
  }

  global.WFAuth = { isLoggedIn, logout, requireAuth, renderUserChip };
})(window);
