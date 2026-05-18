// Utils — shared helpers used across all pages

const Utils = {

  // ── Score colors ──────────────────────────────────────────
  scoreColor(score) {
    if (score >= 70) return 'var(--color-success)';
    if (score >= 50) return 'var(--color-warning)';
    return 'var(--color-danger)';
  },
  scoreBadgeClass(score) {
    if (score >= 70) return 'badge-success';
    if (score >= 50) return 'badge-warning';
    return 'badge-danger';
  },
  scoreProgressClass(score) {
    if (score >= 70) return 'progress-success';
    if (score >= 50) return 'progress-warning';
    return 'progress-danger';
  },
  priorityColor(priority) {
    return { high: 'var(--color-danger)', medium: 'var(--color-warning)', low: 'var(--color-success)' }[priority] || 'var(--color-muted)';
  },
  priorityBadgeClass(priority) {
    return { high: 'badge-danger', medium: 'badge-warning', low: 'badge-success' }[priority] || 'badge-neutral';
  },
  coverageColor(have, need) {
    const pct = need > 0 ? have / need : 1;
    if (pct >= 1) return 'var(--color-success)';
    if (pct >= 0.5) return 'var(--color-warning)';
    return 'var(--color-danger)';
  },
  coverageProgressClass(have, need) {
    const pct = need > 0 ? have / need : 1;
    if (pct >= 1) return 'progress-success';
    if (pct >= 0.5) return 'progress-warning';
    return 'progress-danger';
  },

  // ── Dates ─────────────────────────────────────────────────
  formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  },
  formatTime(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  },
  timeAgo(iso) {
    if (!iso) return '—';
    const diff = Date.now() - new Date(iso).getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days  = Math.floor(diff / 86400000);
    if (mins < 1)   return 'Just now';
    if (mins < 60)  return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days === 1) return 'Yesterday';
    if (days < 30)  return `${days} days ago`;
    return this.formatDate(iso);
  },

  // ── Category display names ────────────────────────────────
  categoryLabel(cat) {
    const labels = {
      leadership:              'Leadership',
      conflict_resolution:     'Conflict Resolution',
      failure_learning:        'Failure & Learning',
      technical_achievement:   'Technical Achievement',
      collaboration:           'Collaboration',
      ambiguity_handling:      'Ambiguity',
      initiative:              'Initiative',
      communication:           'Communication',
      pressure_handling:       'Under Pressure',
      system_design:           'System Design',
      debugging:               'Debugging',
      tech_decisions:          'Tech Decisions',
      performance_optimization:'Performance',
      architecture:            'Architecture',
      career_goal:             'Career Goals',
      value:                   'Values',
      strength:                'Strengths',
      working_style:           'Working Style',
      self_awareness:          'Self Awareness',
    };
    return labels[cat] || cat.replace(/_/g, ' ');
  },

  // ── Source display names ──────────────────────────────────
  sourceLabel(src) {
    return { resume: 'Resume', chatgpt: 'ChatGPT', claude: 'Claude', gemini: 'Gemini', manual: 'Manual' }[src] || src;
  },

  // ── Toasts ────────────────────────────────────────────────
  toast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 200ms';
      setTimeout(() => toast.remove(), 200);
    }, 3500);
  },

  // ── Count-up animation ────────────────────────────────────
  countUp(el, target, duration = 600) {
    const start = performance.now();
    const from = 0;
    const update = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      el.textContent = Math.round(from + (target - from) * eased);
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  },

  // ── URL params ────────────────────────────────────────────
  getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
  },

  // ── Truncate text ─────────────────────────────────────────
  truncate(text, max = 120) {
    if (!text || text.length <= max) return text;
    return text.slice(0, max).trimEnd() + '…';
  },

  // ── Debounce ──────────────────────────────────────────────
  debounce(fn, delay = 300) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
  },

  // ── Session type label ────────────────────────────────────
  sessionTypeLabel(type) {
    return { behavioral: 'Behavioral', technical: 'Technical', mixed: 'Mixed' }[type] || type;
  },

  // ── Status badge class ────────────────────────────────────
  statusBadgeClass(status) {
    return {
      complete:   'badge-success',
      processing: 'badge-warning',
      failed:     'badge-danger',
      pending:    'badge-neutral',
      in_progress:'badge-brand',
    }[status] || 'badge-neutral';
  }
};
