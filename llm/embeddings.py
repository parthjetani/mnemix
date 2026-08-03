import asyncio
import numpy as np
from config import settings

_model = None
_cache: dict[str, np.ndarray] = {}  # per-process; each uvicorn worker holds its own


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed(text: str) -> np.ndarray:
    if text in _cache:
        return _cache[text]
    model = _get_model()
    vector = model.encode([text], convert_to_numpy=True)[0].astype(np.float32)
    _cache[text] = vector
    return vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


async def aembed(text: str) -> np.ndarray:
    """Async wrapper: offloads CPU-bound embed() to a thread so it doesn't block the event loop."""
    if text in _cache:
        return _cache[text]
    return await asyncio.get_running_loop().run_in_executor(None, embed, text)
