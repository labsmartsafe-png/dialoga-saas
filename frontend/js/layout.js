(function (global) {
  const NAV_GROUPS = [
    { title: "Principal", items: [
      { id: "dashboard", label: "Dashboard", href: "dashboard.html", icon: "📊" },
      { id: "setup", label: "Setup", href: "setup.html", icon: "🚀" },
    ]},
    { title: "Atendimento", items: [
      { id: "leads", label: "Leads", href: "leads.html", icon: "👥" },
      { id: "inbox", label: "Inbox", href: "inbox.html", icon: "💬" },
      { id: "agenda", label: "Agenda", href: "agenda.html", icon: "🗓️" },
    ]},
    { title: "Automação", items: [
      { id: "builder", label: "Fluxos", href: "builder.html", icon: "🔀" },
      { id: "ia", label: "IA / Conhecimento", href: "ia.html", icon: "🧠" },
    ]},
    { title: "Comercial", items: [
      { id: "planos", label: "Planos", href: "planos.html", icon: "💳" },
    ]},
    { title: "Sistema", items: [
      { id: "configuracoes", label: "Configurações", href: "configuracoes.html", icon: "⚙️" },
      { id: "admin", label: "Admin", href: "admin.html", icon: "🛡️", adminOnly: true },
    ]},
  ];

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function renderSidebar(active) {
    const el = document.getElementById("app-sidebar");
    if (!el) return;
    let html = '' +
      '<div class="shell-brand"><img src="img/logo-dialoga.png" alt="dIAloga+"><span>dIAloga+</span></div>' +
      '<nav class="shell-nav">';
    NAV_GROUPS.forEach(function (group) {
      html += '<div class="shell-group"><div class="shell-group-title">' + escapeHtml(group.title) + '</div>';
      group.items.forEach(function (item) {
        const attrs = item.adminOnly ? ' data-admin-only style="display:none"' : '';
        html += '<a class="shell-link ' + (active === item.id ? 'active' : '') + '" href="' + item.href + '"' + attrs + '>' +
          '<span class="shell-icon">' + item.icon + '</span><span>' + escapeHtml(item.label) + '</span></a>';
      });
      html += '</div>';
    });
    html += '</nav>';
    el.innerHTML = html;
  }

  function renderTopbar(opts) {
    opts = opts || {};
    const titleEl = document.getElementById("app-topbar-title");
    if (titleEl) {
      titleEl.innerHTML = '<h1>' + escapeHtml(opts.title || "") + '</h1>' +
        (opts.subtitle ? '<p>' + escapeHtml(opts.subtitle) + '</p>' : '');
    }
    const actionsEl = document.getElementById("app-topbar-actions");
    if (actionsEl) actionsEl.innerHTML = opts.actionsHtml || "";
  }

  function render(opts) {
    opts = opts || {};
    renderSidebar(opts.active || "dashboard");
    renderTopbar(opts);
  }

  global.WFLayout = { render: render, renderSidebar: renderSidebar, renderTopbar: renderTopbar };
})(window);
