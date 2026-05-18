// Auth — Supabase magic link, JWT from session
// Keys injected via <meta name="supabase-url"> and <meta name="supabase-anon-key">

const _DEV_TOKEN = 'dev-local';
const _DEV_SESSION = { access_token: _DEV_TOKEN, user: { id: 'dev-user', email: 'dev@localhost' } };

let _supabase = null;

function _getSupabase() {
  if (_supabase) return _supabase;
  const urlMeta = document.querySelector('meta[name="supabase-url"]');
  const keyMeta = document.querySelector('meta[name="supabase-anon-key"]');
  if (!urlMeta || !keyMeta || !window.supabase) {
    console.error('Supabase meta tags or CDN missing');
    return null;
  }
  _supabase = window.supabase.createClient(urlMeta.content, keyMeta.content);
  return _supabase;
}

const Auth = {
  async getSession() {
    // Dev bypass: localStorage flag set by devLogin()
    if (localStorage.getItem('mnemix_dev_mode') === '1') return _DEV_SESSION;
    const sb = _getSupabase();
    if (!sb) return null;
    const { data } = await sb.auth.getSession();
    return data.session;
  },

  async getToken() {
    const session = await this.getSession();
    return session?.access_token || '';
  },

  async requireAuth() {
    const session = await this.getSession();
    if (!session) {
      window.location.href = '/login.html';
      return null;
    }
    return session;
  },

  devLogin() {
    localStorage.setItem('mnemix_dev_mode', '1');
    window.location.href = '/dashboard.html';
  },

  async sendMagicLink(email) {
    const sb = _getSupabase();
    if (!sb) throw new Error('Supabase not initialized');
    const { error } = await sb.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin + '/auth/callback.html' }
    });
    if (error) throw error;
  },

  async handleCallback() {
    const sb = _getSupabase();
    if (!sb) return null;
    // Supabase handles token exchange from URL hash automatically
    const { data, error } = await sb.auth.getSession();
    if (error) throw error;
    return data.session;
  },

  async logout() {
    localStorage.removeItem('mnemix_dev_mode');
    const sb = _getSupabase();
    if (sb) await sb.auth.signOut();
    window.location.href = '/login.html';
  },

  getUserInitials(email) {
    return email ? email[0].toUpperCase() : 'U';
  },

  getUserDisplayName(email) {
    if (!email) return 'User';
    return email.split('@')[0];
  }
};
