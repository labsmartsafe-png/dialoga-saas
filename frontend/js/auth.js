(function (global) {
  const api = global.WFApi;

  function isLoggedIn() { return !!api.getToken(); }

  function logout() {
    api.clearAuth();
    window.location.href = "/login.html";
  }

  async function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = "/login.html";
      return null;
    }
    try {
      const user = await api.me();
      localStorage.setItem("whatsflow_user", JSON.stringify(user));
      return user;
    } catch (e) {
      api.clearAuth();
      window.location.href = "/login.html";
      return null;
    }
  }

  function renderUserChip(el, user) {
    if (!el) return;
    el.innerHTML = '<span style="font-size: 13px; color: var(--muted);">' + escapeHtml(user.company_name) + '</span> <button class="btn btn-secondary btn-sm" id="btn-logout">Sair</button>';
    const btn = document.getElementById("btn-logout");
    if (btn) btn.addEventListener("click", logout);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  global.WFAuth = { isLoggedIn: isLoggedIn, logout: logout, requireAuth: requireAuth, renderUserChip: renderUserChip };
})(window);