"""Structured JSON logging + optional Sentry wiring.

Call `configure_logging()` once during app startup. JSON output goes to
stdout; if SENTRY_DSN is set in the environment, Sentry is initialized
with the FastAPI + logging integrations. If SENTRY_DSN is empty, Sentry
is skipped silently.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Allow callers to attach structured fields via `logger.info("x", extra={"key": "v"})`.
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in ("args", "msg", "levelname", "levelno", "pathname", "filename",
                       "module", "exc_info", "exc_text", "stack_info", "lineno",
                       "funcName", "created", "msecs", "relativeCreated", "thread",
                       "threadName", "processName", "process", "name", "taskName"):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Replace the root handler with a JSON formatter on stdout. Idempotent."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    # Drop existing handlers so we don't double-emit.
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    # Quiet down noisy third parties; keep our own loggers at the configured level.
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    # Remove SQLAlchemy's own echo=True handler to avoid double-logging.
    sqlalchemy_engine_logger = logging.getLogger("sqlalchemy.engine.Engine")
    for handler in list(sqlalchemy_engine_logger.handlers):
        sqlalchemy_engine_logger.removeHandler(handler)


def configure_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Returns True if wired."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN is set but sentry-sdk is not installed; skipping Sentry init."
        )
        return False
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )
    return True
