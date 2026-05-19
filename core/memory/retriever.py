import asyncio

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from llm.embeddings import embed
from core.memory import store
from models.schemas import Memory as MemorySchema


class MemoryRetriever:
    """In-process numpy similarity index.

    SAFE: single uvicorn worker (the default). The asyncio.Lock below
    serializes mutations within a worker.

    UNSAFE: multiple workers (``--workers N`` or gunicorn -w N). Each
    worker process holds its own ``MemoryRetriever`` instance, so a memory
    written by worker A is invisible to worker B's index until restart. This
    is a silent correctness failure, not a crash. Don't run multi-worker
    until the pgvector migration (P4.22) lands and the in-memory index is
    removed.
    """

    def __init__(self):
        self._embeddings: np.ndarray | None = None  # shape (N, 384)
        self._memory_ids: list[str] = []
        self._loaded: bool = False
        self._lock = asyncio.Lock()  # guards _embeddings / _memory_ids mutations

    async def load(self, db: AsyncSession) -> None:
        all_memories = await store.get_all_memories(db)
        async with self._lock:
            if not all_memories:
                self._embeddings = None
                self._memory_ids = []
                self._loaded = True
                return
            self._memory_ids = [m.id for m, _ in all_memories]
            self._embeddings = np.stack([emb for _, emb in all_memories])
            self._loaded = True

    async def search(
        self,
        query_text: str,
        db: AsyncSession,
        top_k: int = 5,
    ) -> list[tuple[MemorySchema, float]]:
        if not self._loaded:
            await self.load(db)

        # Snapshot index state under the lock so a concurrent add_to_index
        # cannot reshape the matrix mid-similarity computation.
        async with self._lock:
            if self._embeddings is None or len(self._memory_ids) == 0:
                return []
            embeddings_snapshot = self._embeddings
            ids_snapshot = list(self._memory_ids)

        query_vec = embed(query_text).astype(np.float32)
        norms = np.linalg.norm(embeddings_snapshot, axis=1)
        query_norm = np.linalg.norm(query_vec)
        similarities = (embeddings_snapshot @ query_vec) / (norms * query_norm + 1e-10)

        k = min(top_k, len(ids_snapshot))
        top_indices = np.argsort(similarities)[::-1][:k]

        # Batch fetch all top-k memories in one query instead of N selects.
        top_ids = [ids_snapshot[idx] for idx in top_indices]
        id_to_memory = await store.get_memories_by_ids(top_ids, db)
        results: list[tuple[MemorySchema, float]] = []
        for idx in top_indices:
            mid = ids_snapshot[idx]
            memory = id_to_memory.get(mid)
            if memory:
                results.append((memory, float(similarities[idx])))
        return results

    async def add_to_index(self, memory_id: str, embedding: np.ndarray) -> None:
        embedding = embedding.astype(np.float32)
        async with self._lock:
            self._memory_ids.append(memory_id)
            if self._embeddings is None:
                self._embeddings = embedding.reshape(1, -1)
            else:
                self._embeddings = np.vstack([self._embeddings, embedding.reshape(1, -1)])
            self._loaded = True

    def invalidate(self) -> None:
        self._embeddings = None
        self._memory_ids = []
        self._loaded = False


memory_retriever = MemoryRetriever()
