// API — all fetch() calls to FastAPI backend
// Auth.getToken() is async (Supabase), so every method is async

const API = {
  base: '/api/v1',

  async _headers(json = true) {
    const token = await Auth.getToken();
    const h = { 'Authorization': `Bearer ${token}` };
    if (json) h['Content-Type'] = 'application/json';
    return h;
  },

  async get(path) {
    const res = await fetch(`${this.base}${path}`, {
      headers: await this._headers(false)
    });
    if (res.status === 401) { window.location.href = '/login.html'; return; }
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async post(path, body) {
    const res = await fetch(`${this.base}${path}`, {
      method: 'POST',
      headers: await this._headers(true),
      body: JSON.stringify(body)
    });
    if (res.status === 401) { window.location.href = '/login.html'; return; }
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async put(path, body) {
    const res = await fetch(`${this.base}${path}`, {
      method: 'PUT',
      headers: await this._headers(true),
      body: JSON.stringify(body)
    });
    if (res.status === 401) { window.location.href = '/login.html'; return; }
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async upload(path, formData) {
    // No Content-Type header — browser sets multipart boundary automatically
    const token = await Auth.getToken();
    const res = await fetch(`${this.base}${path}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    if (res.status === 401) { window.location.href = '/login.html'; return; }
    if (!res.ok) throw await res.json();
    return res.json();
  },

  // ── Memory ────────────────────────────────────────────────
  async getProfile()         { return this.get('/memory/profile'); },
  async getGaps()            { return this.get('/memory/gaps'); },
  async searchMemories(q, k) { return this.get(`/memory/search?q=${encodeURIComponent(q)}&top_k=${k || 5}`); },
  async addMemory(data)      { return this.post('/memory/add', data); },

  // ── Profile ───────────────────────────────────────────────
  async getUserProfile()     { return this.get('/profile'); },
  async updateUserProfile(d) { return this.put('/profile', d); },

  // ── Ingestion ─────────────────────────────────────────────
  async ingestResume(file) {
    const fd = new FormData();
    fd.append('file', file);
    return this.upload('/ingest/resume', fd);
  },
  async ingestExport(file, sourceType) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('source_type', sourceType);
    return this.upload('/ingest/ai-export', fd);
  },
  async listJobs()            { return this.get('/ingest/jobs'); },
  async getJobStatus(jobId)  { return this.get(`/ingest/status/${jobId}`); },

  // ── Interview ─────────────────────────────────────────────
  async startSession(type)   { return this.post('/interview/start', { session_type: type }); },
  async submitAnswer(data)   { return this.post('/interview/answer', data); },
  async getEvaluation(id)    { return this.get(`/interview/evaluate/${id}`); },
  async getSessions()        { return this.get('/interview/sessions'); },

  // ── Chat ──────────────────────────────────────────────────
  async chat(message)        { return this.post('/chat', { message }); },

  // ── Polling helper ────────────────────────────────────────
  async pollUntilDone(fn, interval = 2000, maxAttempts = 150) {
    for (let i = 0; i < maxAttempts; i++) {
      const result = await fn();
      if (result.status === 'complete' || result.status === 'failed') return result;
      if (result.status !== 'evaluating' && result.status !== 'processing') return result;
      await new Promise(r => setTimeout(r, interval));
    }
    throw new Error('Timeout waiting for job completion');
  }
};
