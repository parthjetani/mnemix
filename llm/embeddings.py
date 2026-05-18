import numpy as np
from config import settings

_model = None
_cache: dict[str, np.ndarray] = {}


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


def embed_batch(texts: list[str]) -> list[np.ndarray]:
    results: list[np.ndarray | None] = [None] * len(texts)
    uncached_indices = []
    uncached_texts = []

    for i, text in enumerate(texts):
        if text in _cache:
            results[i] = _cache[text]
        else:
            uncached_indices.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        model = _get_model()
        vectors = model.encode(uncached_texts, convert_to_numpy=True).astype(np.float32)
        for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
            _cache[text] = vectors[i]
            results[idx] = vectors[i]

    return results  # type: ignore[return-value]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
