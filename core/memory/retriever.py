import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from llm.embeddings import embed
from core.memory import store
from models.schemas import Memory as MemorySchema


class MemoryRetriever:
    def __init__(self):
        self._embeddings: np.ndarray | None = None  # shape (N, 384)
        self._memory_ids: list[str] = []
        self._loaded: bool = False

    async def load(self, db: AsyncSession) -> None:
        all_memories = await store.get_all_memories(db)
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

        if self._embeddings is None or len(self._memory_ids) == 0:
            return []

        query_vec = embed(query_text).astype(np.float32)
        norms = np.linalg.norm(self._embeddings, axis=1)
        query_norm = np.linalg.norm(query_vec)
        similarities = (self._embeddings @ query_vec) / (norms * query_norm + 1e-10)

        k = min(top_k, len(self._memory_ids))
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            memory = await store.get_memory_by_id(self._memory_ids[idx], db)
            if memory:
                results.append((memory, float(similarities[idx])))
        return results

    async def add_to_index(self, memory_id: str, embedding: np.ndarray) -> None:
        embedding = embedding.astype(np.float32)
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
