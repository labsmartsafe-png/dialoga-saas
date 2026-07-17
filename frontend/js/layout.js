(function (global) {
  const NAV_GROUPS = [
    { title: "Principal", items: [
      { id: "dashboard", label: "Dashboard", href: "dashboard.html" },
      { id: "setup", label: "Setup guiado", href: "setup.html" },
    ]},
    { title: "Atendimento", items: [
      { id: "leads", label: "Leads", href: "leads.html" },
      { id: "inbox", label: "Inbox", href: "inbox.html" },
      { id: "agenda", label: "Agenda", href: "agenda.html" },
    ]},
    { title: "Automação", items: [
      { id: "builder", label: "Fluxos", href: "builder.html" },
      { id: "ia", label: "IA e conhecimento", href: "ia.html" },
    ]},
    { title: "Comercial", items: [
      { id: "planos", label: "Planos", href: "planos.html" },
    ]},
    { title: "Sistema", items: [
      { id: "configuracoes", label: "Configurações", href: "configuracoes.html" },
      { id: "admin", label: "Admin", href: "admin.html", adminOnly: true },
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
      '<nav class="shell-nav" aria-label="Navegação principal">';

    NAV_GROUPS.forEach(function (group) {
      html += '<div class="shell-group"><div class="shell-group-title">' + escapeHtml(group.title) + '</div>';
      group.items.forEach(function (item) {
        const attrs = item.adminOnly ? ' data-admin-only style="display:none"' : '';
        html += '<a class="shell-link ' + (active === item.id ? 'active' : '') + '" href="' + item.href + '"' + attrs + '>' +
          '<span class="shell-link-marker" aria-hidden="true"></span><span>' + escapeHtml(item.label) + '</span></a>';
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
