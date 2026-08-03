from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Groq — primary provider, fastest tier for most tasks
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # NVIDIA NIM — quality tier (DeepSeek/Kimi/Qwen-coder) + Llama-8B backstop
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Gemini (OpenAI-compat endpoint) — mid tier
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # Models — Groq tier
    MODEL_CLASSIFY: str = "llama-3.1-8b-instant"          # rule-based first, LLM for ambiguous — 8B tier for 14.4K RPD
    MODEL_EXTRACT: str = "llama-3.3-70b-versatile"        # quality extraction
    MODEL_EVAL: str = "llama-3.3-70b-versatile"           # answer evaluation
    MODEL_EVAL_SYSDESIGN: str = "qwen/qwen3-32b"          # reasoning-heavy eval
    MODEL_FEEDBACK: str = "llama-3.3-70b-versatile"       # user-facing quality
    MODEL_GAP_ANALYSIS: str = "qwen/qwen3-32b"            # strategic reasoning

    # Models — NVIDIA NIM tier
    MODEL_NIM_CLASSIFY: str = "meta/llama-3.1-8b-instruct"
    MODEL_NIM_EXTRACT: str = "deepseek-ai/deepseek-v4-flash"
    MODEL_NIM_REASONING: str = "moonshotai/kimi-k2-thinking"

    # Models — Gemini tier
    MODEL_GEMINI_FLASH_LITE: str = "gemini-3.5-flash-lite"
    MODEL_GEMMA4: str = "gemma-4-31b-it"

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

    # Rate limiting — keeps extractor within Groq's free-tier token budget
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
