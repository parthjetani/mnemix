from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Groq — primary provider for all LLM tasks
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # OpenRouter — backup for reasoning tasks (50 req/day free)
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Models — all on Groq unless noted
    MODEL_CLASSIFY: str = "llama-3.3-70b-versatile"       # rule-based first, LLM for ambiguous
    MODEL_EXTRACT: str = "llama-3.3-70b-versatile"        # quality extraction
    MODEL_PROFILE: str = "llama-3.3-70b-versatile"        # one-time profile synthesis
    MODEL_Q_BEHAVIORAL: str = "openai/gpt-oss-20b"        # 886 tok/s, fastest
    MODEL_Q_TECHNICAL: str = "qwen/qwen3-32b"             # domain knowledge
    MODEL_EVAL: str = "llama-3.3-70b-versatile"           # answer evaluation
    MODEL_EVAL_SYSDESIGN: str = "qwen/qwen3-32b"          # reasoning-heavy eval
    MODEL_FEEDBACK: str = "llama-3.3-70b-versatile"       # user-facing quality
    MODEL_GAP_ANALYSIS: str = "qwen/qwen3-32b"            # strategic reasoning

    # OpenRouter fallback model IDs (used when Groq fails)
    MODEL_FALLBACK_REASONING: str = "deepseek/deepseek-r1:free"
    MODEL_FALLBACK_GENERAL: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Database (Supabase PostgreSQL) — must be set in .env, no fallback
    DATABASE_URL: str

    # Embeddings (local, no API cost)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # App
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_MEMORIES_PER_USER: int = 500
    MIN_CONFIDENCE_THRESHOLD: float = 0.65
    INTERVIEW_QUESTIONS_COUNT: int = 8

    # Supabase — required for UI auth (optional for CLI-only use)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Rate limiting — Groq free tier is 6K tokens/min
    # Extractor will sleep between batches to stay within limits
    EXTRACTION_BATCH_SIZE: int = 5        # segments per batch
    EXTRACTION_BATCH_DELAY: float = 2.0   # seconds between batches


settings = Settings()


if __name__ == "__main__":
    import json
    data = settings.model_dump()
    for key in data:
        if "API_KEY" in key and data[key]:
            data[key] = data[key][:8] + "..." + data[key][-4:]
    print(json.dumps(data, indent=2))
