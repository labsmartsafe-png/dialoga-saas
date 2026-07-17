(function (global) {
  const api = global.WFApi;

  function isLoggedIn() { return !!api.getToken(); }

  function logout() {
    api.clearAuth();
    window.location.href = "/login.html";
  }

  function avatarKey(user) {
    return "dialoga_user_avatar_" + ((user && user.email) || "default").toLowerCase();
  }

  function getAvatar(user) {
    return localStorage.getItem(avatarKey(user));
  }

  function saveAvatar(user, dataUrl) {
    try { localStorage.setItem(avatarKey(user), dataUrl); } catch (e) {}
  }

  function initials(user) {
    const source = (user && (user.full_name || user.company_name || user.email)) || "U";
    return String(source).trim().charAt(0).toUpperCase() || "U";
  }

  function isAdmin(user) {
    return !!(user && user.is_admin);
  }

  function applyRoleVisibility(user) {
    document.querySelectorAll("[data-admin-only]").forEach(function (el) {
      el.style.display = isAdmin(user) ? "" : "none";
    });
  }

  async function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = "/login.html";
      return null;
    }
    try {
      const user = await api.me();
      localStorage.setItem("whatsflow_user", JSON.stringify(user));
      applyRoleVisibility(user);
      return user;
    } catch (e) {
      api.clearAuth();
      window.location.href = "/login.html";
      return null;
    }
  }

  function renderUserChip(el, user) {
    if (!el) return;
    const avatar = getAvatar(user);
    const avatarHtml = avatar
      ? '<img src="' + avatar + '" alt="Avatar">'
      : '<span>' + escapeHtml(initials(user)) + '</span>';
    el.innerHTML = '' +
      '<div class="wf-user-chip">' +
        '<button class="wf-avatar" id="btn-avatar" title="Alterar foto do usuário" type="button">' + avatarHtml + '</button>' +
        '<div class="wf-user-meta"><strong>' + escapeHtml(user.company_name || user.email || "Usuário") + '</strong><small>' + escapeHtml(user.email || "") + '</small></div>' +
        '<button class="btn btn-secondary btn-sm" id="btn-logout">Sair</button>' +
        '<input type="file" id="avatar-file" accept="image/*" style="display:none">' +
      '</div>';

    const btn = document.getElementById("btn-logout");
    if (btn) btn.addEventListener("click", logout);

    const avatarBtn = document.getElementById("btn-avatar");
    const file = document.getElementById("avatar-file");
    if (avatarBtn && file) {
      avatarBtn.addEventListener("click", function () { file.click(); });
      file.addEventListener("change", function () {
        const f = file.files && file.files[0];
        if (!f) return;
        if (!f.type.startsWith("image/")) return;
        if (f.size > 1024 * 1024) { alert("Use uma imagem de até 1MB."); return; }
        const reader = new FileReader();
        reader.onload = function () {
          saveAvatar(user, reader.result);
          renderUserChip(el, user);
        };
        reader.readAsDataURL(f);
      });
    }

    applyRoleVisibility(user);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  global.WFAuth = {
    isLoggedIn: isLoggedIn,
    logout: logout,
    requireAuth: requireAuth,
    renderUserChip: renderUserChip,
    applyRoleVisibility: applyRoleVisibility,
  };
})(window);
