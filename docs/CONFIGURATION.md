# MNEMIX — Configuration Reference

All configuration is loaded from the `.env` file by `config.py` using pydantic-settings. Copy `.env.example` to `.env` to get started.

## API Keys (Required)

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key. Primary provider for all LLM tasks. Free tier: 14,400 req/day, no credit card needed. Get one at [console.groq.com](https://console.groq.com). |
| `OPENROUTER_API_KEY` | OpenRouter API key. Used as fallback when Groq fails. Free tier gives access to `:free` models (50 req/day per model). Get one at [openrouter.ai](https://openrouter.ai). |

Both keys are **required** — the server will fail to start without them.

## Base URLs (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | Groq API endpoint |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |

These rarely need changing.

## Model Selection

All models default to values optimized for the free tier. Change only if you have paid access to higher-quality models.

| Variable | Default | Task | Provider |
|----------|---------|------|----------|
| `MODEL_CLASSIFY` | `llama-3.3-70b-versatile` | Classify ambiguous segments | Groq |
| `MODEL_EXTRACT` | `llama-3.3-70b-versatile` | Extract memories from segments | Groq |
| `MODEL_PROFILE` | `llama-3.3-70b-versatile` | Synthesize user profile | Groq |
| `MODEL_Q_BEHAVIORAL` | `openai/gpt-oss-20b` | Generate behavioral questions | Groq (via OpenAI compat) |
| `MODEL_Q_TECHNICAL` | `qwen/qwen3-32b` | Generate technical questions | Groq |
| `MODEL_EVAL` | `llama-3.3-70b-versatile` | Evaluate interview answers | Groq |
| `MODEL_EVAL_SYSDESIGN` | `qwen/qwen3-32b` | Evaluate system design answers | Groq |
| `MODEL_FEEDBACK` | `llama-3.3-70b-versatile` | Generate feedback report | Groq |
| `MODEL_GAP_ANALYSIS` | `qwen/qwen3-32b` | Analyze memory gaps | Groq |
| `MODEL_FALLBACK_REASONING` | `deepseek/deepseek-r1:free` | Fallback for reasoning tasks | OpenRouter |
| `MODEL_FALLBACK_GENERAL` | `meta-llama/llama-3.3-70b-instruct:free` | Fallback for general tasks | OpenRouter |

`qwen/qwen3-32b` is a thinking model. Its `<think>...</think>` blocks are automatically stripped by `parse_json_response` before JSON parsing.

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./mnemix.db` | SQLAlchemy async connection string. The path is relative to the working directory. |

To use an absolute path: `sqlite+aiosqlite:///D:/WorkSpace/mnemix/mnemix.db`

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
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxx

# Database (relative path — file created in working directory)
DATABASE_URL=sqlite+aiosqlite:///./mnemix.db

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
    OPENROUTER_API_KEY: str     # Required — no default
    DATABASE_URL: str = "sqlite+aiosqlite:///./mnemix.db"
    ...

settings = Settings()  # singleton, imported everywhere
```

Access settings anywhere with:
```python
from config import settings
print(settings.GROQ_API_KEY)
```
