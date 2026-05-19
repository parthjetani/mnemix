# MNEMIX — UI Guide

The web UI is a static frontend served by FastAPI from the `frontend/` directory. It communicates with the FastAPI backend exclusively via the `/api/v1` REST API. Authentication is handled by Supabase magic links.

---

## Tech Stack

| Concern | Library |
|---------|---------|
| Reactivity | Alpine.js 3.x (CDN) |
| Auth | Supabase JS 2.x (CDN) |
| Charts | Chart.js (CDN, dashboard + history only) |
| Icons | Lucide (CDN) |
| Fonts | Fraunces (display/headings), Instrument Sans (body), JetBrains Mono (code/labels) |
| Styling | 3 custom CSS files (no framework) |
| JS modules | 4 app scripts (no bundler) |

All pages are plain HTML files — no build step required.

---

## File Structure

```
frontend/
├── index.html          ← Public landing page
├── login.html          ← Magic link sign-in
├── onboarding.html     ← First-run 5-step setup wizard
├── dashboard.html      ← Home after login
├── interview.html      ← Interview session flow
├── report.html         ← Post-interview feedback report
├── memory.html         ← Memory browser + gap analysis
├── documents.html      ← Upload resume / AI exports
├── chat.html           ← Conversational memory search
├── history.html        ← Past sessions list
├── settings.html       ← User profile settings
│
├── auth/
│   └── callback.html   ← Supabase magic link callback
│
├── css/
│   ├── design-system.css   ← CSS variables, base reset, typography
│   ├── components.css      ← Buttons, cards, inputs, badges, toasts
│   └── layout.css          ← Sidebar, topbar, page shell
│
└── js/
    ├── auth.js         ← Supabase auth wrapper (Auth object)
    ├── api.js          ← All fetch() calls to backend (API object)
    ├── utils.js        ← Shared helpers (formatDate, formatScore, etc.)
    └── components.js   ← Alpine.js component factories
```

---

## Shared JS Objects

### `Auth` (`js/auth.js`)

Wraps Supabase auth. Every page calls `Auth.requireAuth()` on load to redirect unauthenticated users to `/login.html`.

| Method | Description |
|--------|-------------|
| `Auth.requireAuth()` | Redirects to `/login.html` if no session. Returns session object. |
| `Auth.getToken()` | Returns the JWT access token for API calls. |
| `Auth.sendMagicLink(email)` | Triggers Supabase OTP email. |
| `Auth.handleCallback()` | Called by `auth/callback.html` to exchange the URL hash token. |
| `Auth.logout()` | Signs out and redirects to `/login.html`. |
| `Auth.devLogin()` | Sets `mnemix_dev_mode=1` in localStorage — bypasses Supabase for local dev. |

**Dev mode:** Navigate to `/login.html` and call `Auth.devLogin()` from the browser console to skip magic link auth during development.

### `API` (`js/api.js`)

Wraps all backend calls. Attaches the Bearer token from `Auth.getToken()` to every request. On 401 response, redirects to `/login.html`.

```js
// All methods are async
API.getProfile()                    // GET /memory/profile
API.getGaps()                       // GET /memory/gaps
API.searchMemories(query, topK)     // GET /memory/search
API.addMemory(data)                 // POST /memory/add
API.getUserProfile()                // GET /profile
API.updateUserProfile(data)         // PUT /profile
API.ingestResume(file)              // POST /ingest/resume (multipart)
API.ingestExport(file, sourceType)  // POST /ingest/ai-export (multipart)
API.listJobs()                      // GET /ingest/jobs
API.getJobStatus(jobId)             // GET /ingest/status/{jobId}
API.startSession(type)              // POST /interview/start
API.submitAnswer(data)              // POST /interview/answer
API.getEvaluation(sessionId)        // GET /interview/evaluate/{sessionId}
API.getSessions()                   // GET /interview/sessions
API.chat(message)                   // POST /chat
API.pollUntilDone(fn, interval)     // Polling helper — calls fn() every interval ms
```

---

## Pages

### `index.html` — Landing Page

Public (no auth required). Static marketing page with product description, feature list, and CTA button linking to `/login.html`.

No Alpine.js, no API calls.

---

### `login.html` — Sign In

Supabase magic link authentication.

**Flow:**
1. User enters email → `Auth.sendMagicLink(email)` called
2. "Check your inbox" confirmation shown
3. User clicks link in email → redirected to `/auth/callback.html`
4. Callback exchanges the URL hash token → session stored in Supabase
5. Redirected to `/dashboard.html` (first-time users) or `/onboarding.html`

**Dev bypass:**
```js
// In browser console on login.html:
Auth.devLogin()
```

---

### `auth/callback.html` — Auth Callback

Handles the redirect from Supabase magic links. Calls `Auth.handleCallback()`, then redirects to `/dashboard.html`. Shows a spinner while processing.

---

### `onboarding.html` — First-Run Wizard

5-step setup flow shown once after first login. Progress bar at the top tracks completion.

| Step | Title | What happens |
|------|-------|-------------|
| 1 | Welcome | Explains what MNEMIX does. No action required. |
| 2 | Your role | Collects `field` (software/product/data), `seniority` (junior/mid/senior), target roles. Calls `API.updateUserProfile()`. |
| 3 | Upload resume | File picker for PDF. Calls `API.ingestResume()`. Progress bar polls `API.getJobStatus()`. |
| 4 | Upload AI export | File picker for ZIP. Dropdown to select `chatgpt` or `claude`. Calls `API.ingestExport()`. Polls status. |
| 5 | Done | Shows memory count and category coverage stats. "Go to Dashboard" button. |

Steps 3 and 4 are skippable. The wizard can be re-entered from Documents page.

---

### `dashboard.html` — Home

The main screen after login. Three-column layout (sidebar + main + right panel).

**Left panel:** Quick action buttons — Start Interview, Browse Memories, Upload Document, Chat.

**Main area:**
- Memory coverage — score bar showing how many of the 13 required categories are filled
- Recent sessions — last 5 interview sessions with scores and dates

**Right panel:**
- Top memory categories — bar chart (Chart.js)
- Upcoming gaps — top 3 categories needing more stories

All data loaded on page init via `API.getProfile()`, `API.getSessions()`, `API.getGaps()`.

---

### `interview.html` — Interview Session

Full-screen interview flow with three modes:

**Setup mode** (before starting):
- Three session type cards: Behavioral, Technical, Mixed
- "Start Interview" button → calls `API.startSession(type)`
- Loads all 8 questions from the response, caches in Alpine state

**Active mode** (during interview):
- Full-screen layout, progress bar at top
- Large question number (monospace, faded)
- Question text below
- Textarea for answer input
- "Submit Answer" button → calls `API.submitAnswer()`
- Next question shown immediately from cached array (no network wait)
- After last answer: transitions to evaluating mode

**Evaluating mode** (after last answer):
- "Evaluating your responses…" screen with 3-step progress indicator
- Polls `API.getEvaluation(sessionId)` every 3 seconds
- On `status=complete`: redirects to `/report.html?id={sessionId}`
- On `status=failed`: shows error with retry option

---

### `report.html` — Feedback Report

Loaded with `?id={sessionId}` query parameter. Calls `API.getEvaluation(sessionId)`.

**Layout:**
- **Score hero** — large animated number (0–100) with color coding: red < 50, yellow 50–75, green > 75
- **Overall narrative** — LLM-generated report text rendered as formatted paragraphs
- **Per-answer breakdown** — one card per question showing:
  - Question text
  - User's answer
  - Score bar (memory match, specificity, outcome, coherence)
  - Specific feedback sentence

"Run another session" button links back to `/interview.html`.

---

### `memory.html` — Memory Browser

Two-panel layout:

**Left: Category grid** — 19 categories in a 3-column grid. Each card shows:
- Category name
- Memory count / minimum required
- Fill level bar (green if met, amber if partial, red if empty)
- Click to filter memories on the right

**Right: Memory list** — Filtered by selected category. Each memory card shows:
- Content text
- Source badge (resume / chatgpt / claude)
- Confidence score
- `has_outcome` and `outcome_quantified` indicators

**Gap analysis section** (below grid) — calls `API.getGaps()`. Shows categories below their minimum with suggested follow-up questions to fill the gap.

**Add memory** — Manual entry form (content + category). Calls `API.addMemory()`.

---

### `documents.html` — Documents

Upload history and new upload forms.

- Resume upload: PDF only. Shows last ingestion job status.
- AI export upload: ZIP file + source type selector (`chatgpt` / `claude`).
- Job list: table of all ingestion jobs with status, memories found, timestamp.
- Polls active jobs every 2 seconds until `complete` or `failed`.

---

### `chat.html` — Memory Chat

Conversational interface backed by `POST /api/v1/chat`. User types a message; the backend retrieves relevant memories and returns an LLM-composed answer grounded in those memories.

Useful for: "What stories do I have about dealing with a difficult stakeholder?" or "What's my best example of system design?"

Message history stored in Alpine state only — not persisted across page reloads.

---

### `history.html` — Session History

Table of all past interview sessions. Columns: date, session type, status, overall score.

- Chart.js line chart showing score trend over time (sessions with `status=complete` only)
- Clicking a row navigates to `/report.html?id={sessionId}`
- Sessions with `status=evaluating` show a spinner and poll until complete

---

### `settings.html` — Settings

Form to update the user profile stored in `user_profile` table.

Fields: field, seniority, primary stack (comma-separated), target roles (comma-separated), communication style, career narrative.

Calls `API.updateUserProfile()` on save. Changes affect question selection and evaluation context in future sessions.

---

## Auth Flow Summary

```
/index.html (public)
    → CTA → /login.html
        → magic link email
        → /auth/callback.html  (Supabase exchanges token)
            → /onboarding.html  (first time)
            → /dashboard.html   (returning user)
                → /interview.html
                → /report.html?id=...
                → /memory.html
                → /documents.html
                → /chat.html
                → /history.html
                → /settings.html
```

All pages except `index.html`, `login.html`, and `auth/callback.html` call `Auth.requireAuth()` on load and redirect to `/login.html` if no session exists.

---

## FastAPI Static File Serving

The frontend is served by FastAPI's `StaticFiles` mount:

```python
# main.py
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

This means:
- All `.html`, `.css`, `.js` files in `frontend/` are served directly
- The API routes (`/api/v1/...`) take precedence over static files (FastAPI routes are matched first)
- Browser caching can serve stale JS after code changes — append `?v=N` to script/link tags during development to bust the cache

---

## Supabase Configuration

Supabase credentials are served to the frontend by the backend via a single endpoint:

```
GET /config.js
```

This returns a JavaScript snippet that sets `window.MNEMIX_CONFIG`:

```js
window.MNEMIX_CONFIG = {
  "supabase": {
    "url": "https://your-project.supabase.co",
    "anonKey": "eyJ..."
  }
};
```

Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`. All HTML pages load `/config.js` via a `<script>` tag and fall back to legacy `<meta>` tags if `MNEMIX_CONFIG` is not present.

**Supabase project setup required:**
- Authentication → Providers → Email → enable **Magic Links**
- Authentication → URL Configuration → add `{origin}/auth/callback.html` to Redirect URLs
