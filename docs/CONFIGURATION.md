# MNEMIX — Configuration Reference

All configuration is loaded from the `.env` file by `config.py` using pydantic-settings. Copy `.env.example` to `.env` to get started.

## API Keys

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key. **Required** — the server will fail to start without it. Free tier: 14,400 req/day for 8B-class models (much lower for `llama-3.3-70b-versatile`, ~1,000 req/day), no credit card needed. Get one at [console.groq.com](https://console.groq.com). |
| `NVIDIA_API_KEY` | NVIDIA NIM API key. Optional but recommended — primary provider for `extract`/`eval`/`feedback` chains. If unset, those chains skip straight to their Groq fallback with no wasted network call. Get one at [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys). |
| `GEMINI_API_KEY` | Gemini API key (OpenAI-compat endpoint). Optional — mid-tier fallback in several chains. Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). |

Only `GROQ_API_KEY` is required; `NVIDIA_API_KEY` and `GEMINI_API_KEY` are optional but each configured key adds resilience (an extra fallback tier) to the task chains.

## Base URLs (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | Groq API endpoint |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM API endpoint |
| `GEMINI_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai` | Gemini OpenAI-compat endpoint |

These rarely need changing.

## Model Selection

All models default to values optimized for the free tier. Each task routes through an ordered chain of providers (see `docs/LLM_SYSTEM.md` for the full per-task chain) — the variables below name the individual model IDs used within those chains.

| Variable | Default | Provider tier |
|----------|---------|----------------|
| `MODEL_CLASSIFY` | `llama-3.1-8b-instant` | Groq |
| `MODEL_EXTRACT` | `llama-3.3-70b-versatile` | Groq |
| `MODEL_EVAL` | `llama-3.3-70b-versatile` | Groq |
| `MODEL_EVAL_SYSDESIGN` | `qwen/qwen3-32b` | Groq |
| `MODEL_FEEDBACK` | `llama-3.3-70b-versatile` | Groq |
| `MODEL_GAP_ANALYSIS` | `qwen/qwen3-32b` | Groq |
| `MODEL_NIM_CLASSIFY` | `meta/llama-3.1-8b-instruct` | NVIDIA NIM |
| `MODEL_NIM_EXTRACT` | `deepseek-ai/deepseek-v4-flash` | NVIDIA NIM |
| `MODEL_NIM_REASONING` | `moonshotai/kimi-k2-thinking` | NVIDIA NIM |
| `MODEL_GEMINI_FLASH_LITE` | `gemini-3.5-flash-lite` | Gemini |
| `MODEL_GEMMA4` | `gemma-4-31b-it` | Gemini |

`qwen/qwen3-32b` and `moonshotai/kimi-k2-thinking` are thinking models. Their `<think>...</think>` blocks are automatically stripped by `parse_json_response` before JSON parsing.

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | SQLAlchemy async connection string for Supabase PostgreSQL. **Required.** |

## Supabase Auth (Required for web UI)

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | `""` | Your Supabase project URL, e.g. `https://abcdefgh.supabase.co`. Required for the web UI; the server returns 503 on auth endpoints if unset. |
| `SUPABASE_ANON_KEY` | `""` | Supabase anon (public) key. Served to the frontend via `GET /config.js`. |

Both values are found at: Supabase Dashboard → Project Settings → API.

Format: `postgresql+asyncpg://postgres:YOUR-PASSWORD@db.YOUR-PROJECT.supabase.co:5432/postgres`

Special characters in the password must be URL-encoded (`#` → `%23`, `/` → `%2F`, `,` → `%2C`, `$` → `%24`).

Get the connection string from: Supabase Dashboard → Project Settings → Database → Connection string → Python (asyncpg).

## Embeddings

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace model name. Downloaded on first use (~90MB). |
| `EMBEDDING_DIM` | `384` | Output dimension. Must match the model. `all-MiniLM-L6-v2` produces 384-dim vectors. |

## Memory Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_MEMORIES_PER_USER` | `500` | Upper bound on stored memories. Enforced at save time. |
| `MIN_CONFIDENCE_THRESHOLD` | `0.65` | Minimum confidence score for a memory to be saved. Memories below this threshold are discarded during extraction. |

## Interview Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `INTERVIEW_QUESTIONS_COUNT` | `8` | Number of questions per session. The `count` parameter in `select_questions()` defaults to this value. |

## Rate Limiting

These control how the ingestion pipeline batches LLM calls to stay within Groq's free-tier token limits.

| Variable | Default | Description |
|----------|---------|-------------|
| `EXTRACTION_BATCH_SIZE` | `5` | Number of segments processed per LLM batch call. Groq free tier is 6,000 tokens/minute. With 5 segments of ~200 tokens each = ~1,000 tokens/batch. |
| `EXTRACTION_BATCH_DELAY` | `2.0` | Seconds to wait between batches. Set to 2.0s to stay comfortably under the 6K TPM limit. |

Increase `EXTRACTION_BATCH_SIZE` or decrease `EXTRACTION_BATCH_DELAY` if you have a paid Groq plan with higher limits.

## Debug Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Set to `true` to enable SQLAlchemy query logging and verbose LLM error output. |
| `LOG_LEVEL` | `INFO` | Python logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Example `.env`

```env
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Optional — add resilience/quality to task chains
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxx

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Embeddings (local, no cost)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# Thresholds
MIN_CONFIDENCE_THRESHOLD=0.65
INTERVIEW_QUESTIONS_COUNT=8

# Rate limiting
EXTRACTION_BATCH_SIZE=5
EXTRACTION_BATCH_DELAY=2.0

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

## How Settings Are Loaded

`config.py` defines a `Settings` class using pydantic-settings:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    GROQ_API_KEY: str           # Required — no default
    NVIDIA_API_KEY: str = ""    # Optional — chains skip this provider if unset
    GEMINI_API_KEY: str = ""    # Optional — chains skip this provider if unset
    DATABASE_URL: str  # Required — Supabase PostgreSQL connection string
    ...

settings = Settings()  # singleton, imported everywhere
```

Access settings anywhere with:
```python
from config import settings
print(settings.GROQ_API_KEY)
```

**Gotcha:** pydantic-settings prioritizes real OS environment variables over `.env` file values. If you've ever `export`ed or `source`d `.env` into a shell session, those exported values will silently shadow later edits to the `.env` file in that same session. Run `env | grep MODEL_` (or open a fresh terminal) if a config change doesn't seem to take effect.
