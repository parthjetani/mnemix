// Shared Alpine.js data factory used by every authenticated page.
// Usage: <div x-data="appBase('dashboard')"> ... </div>
// Pages spread this and add their own data:
//   x-data="{ ...appBase('memory'), memories: [], async init() { await this._init(); ... } }"

function appBase(pageName) {
  return {
    page: pageName,
    userEmail: '',
    userInitials: 'U',
    userDisplayName: 'User',
    loading: true,

    // Call at the top of every page's init()
    async _init() {
      const session = await Auth.requireAuth();
      if (!session) return; // requireAuth redirects if no session
      this.userEmail = session.user.email || '';
      this.userInitials = Auth.getUserInitials(this.userEmail);
      this.userDisplayName = Auth.getUserDisplayName(this.userEmail);
    },

    async logout() {
      await Auth.logout();
    },

    // Shared error handler — shows a toast and logs
    handleError(err, fallback = 'Something went wrong') {
      const msg = err?.detail || err?.message || fallback;
      Utils.toast(msg, 'error');
      console.error(err);
    },
  };
}

// Sidebar component — handles active state
function sidebarData(activePage) {
  return {
    active: activePage,
    navItems: [
      { id: 'dashboard', label: 'Dashboard',  href: '/dashboard.html',  icon: 'layout-dashboard' },
      { id: 'memory',    label: 'Memory',      href: '/memory.html',     icon: 'brain' },
      { id: 'documents', label: 'Documents',   href: '/documents.html',  icon: 'folder' },
      { id: 'interview', label: 'Interview',   href: '/interview.html',  icon: 'target' },
      { id: 'history',   label: 'History',     href: '/history.html',    icon: 'bar-chart-2' },
      { id: 'chat',      label: 'Chat',        href: '/chat.html',       icon: 'message-circle' },
    ],
    accountItems: [
      { id: 'settings',  label: 'Settings',    href: '/settings.html',   icon: 'settings' },
    ],
  };
}

// Shared HTML template injected into every authenticated page sidebar
function renderSidebar(activePage, userEmail) {
  const items = [
    { id: 'dashboard', label: 'Dashboard', href: '/dashboard.html', icon: 'layout-dashboard' },
    { id: 'memory',    label: 'Memory',    href: '/memory.html',    icon: 'brain' },
    { id: 'documents', label: 'Documents', href: '/documents.html', icon: 'folder' },
    { id: 'interview', label: 'Interview', href: '/interview.html', icon: 'target' },
    { id: 'history',   label: 'History',   href: '/history.html',   icon: 'bar-chart-2' },
    { id: 'chat',      label: 'Chat',      href: '/chat.html',      icon: 'message-circle' },
  ];

  const initials = Auth.getUserInitials(userEmail);
  const displayName = Auth.getUserDisplayName(userEmail);
  const shortEmail = userEmail.length > 22 ? userEmail.slice(0, 22) + '…' : userEmail;

  const navHTML = items.map(item => `
    <a href="${item.href}" class="nav-item ${activePage === item.id ? 'active' : ''}">
      <i data-lucide="${item.icon}"></i>
      <span>${item.label}</span>
    </a>
  `).join('');

  return `
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="sidebar-logo-mark">M</div>
        <span class="sidebar-logo-text">MNEMIX</span>
      </div>
      <nav class="sidebar-nav">
        <span class="nav-section-label">Main</span>
        ${navHTML}
        <div class="nav-divider"></div>
        <span class="nav-section-label">Account</span>
        <a href="/settings.html" class="nav-item ${activePage === 'settings' ? 'active' : ''}">
          <i data-lucide="settings"></i>
          <span>Settings</span>
        </a>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info" onclick="Auth.logout()">
          <div class="user-avatar">${initials}</div>
          <div class="user-details">
            <div class="user-name">${displayName}</div>
            <div class="user-email">${shortEmail}</div>
          </div>
        </div>
      </div>
    </aside>
  `;
}

// Bottom nav for mobile
function renderBottomNav(activePage) {
  const items = [
    { id: 'dashboard', label: 'Home',      href: '/dashboard.html', icon: 'layout-dashboard' },
    { id: 'memory',    label: 'Memory',    href: '/memory.html',    icon: 'brain' },
    { id: 'interview', label: 'Interview', href: '/interview.html', icon: 'target' },
    { id: 'history',   label: 'History',   href: '/history.html',   icon: 'bar-chart-2' },
    { id: 'chat',      label: 'Chat',      href: '/chat.html',      icon: 'message-circle' },
  ];

  const itemsHTML = items.map(item => `
    <a href="${item.href}" class="bottom-nav-item ${activePage === item.id ? 'active' : ''}">
      <i data-lucide="${item.icon}"></i>
      <span>${item.label}</span>
    </a>
  `).join('');

  return `<nav class="bottom-nav">${itemsHTML}</nav>`;
}
