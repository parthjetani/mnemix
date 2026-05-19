"""pgvector-backed retriever — replacement for the in-memory numpy retriever.

WIRED. main.py imports memory_retriever from this module. To remove the
legacy numpy retriever entirely:
  1. Verify search quality matches expectations on real data.
  2. Drop core/memory/retriever.py.
  3. Stop dual-writing in core/memory/store.save_memory (remove the
     BYTEA `embedding` write).
  4. Drop the `embedding` BYTEA column from the schema.

Multi-worker note: unlike the numpy retriever, this implementation is
process-stateless — multiple uvicorn workers behave correctly.
"""
from __future__ import annotations

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from llm.embeddings import embed
from models.schemas import Memory as MemorySchema


class PgvectorRetriever:
    async def load(self, db: AsyncSession) -> None:  # noqa: ARG002 — signature parity
        """No-op. pgvector has no warm-up index to populate."""

    def invalidate(self) -> None:
        """No-op. State lives in Postgres."""

    async def add_to_index(
        self,
        memory_id: str,  # noqa: ARG002 — store.save_memory writes embedding_vec inline
        embedding: np.ndarray,  # noqa: ARG002
    ) -> None:
        """No-op. core.memory.store.save_memory persists embedding_vec directly."""

    async def search(
        self,
        query_text: str,
        db: AsyncSession,
        top_k: int = 5,
        user_id: str | None = None,
    ) -> list[tuple[MemorySchema, float]]:
        from core.memory.store import get_memories_by_ids  # local import to avoid cycle

        query_vec = embed(query_text).astype(np.float32)
        vec_literal = "[" + ",".join(f"{x:.6f}" for x in query_vec.tolist()) + "]"
        k = min(top_k, 20)

        uid_filter = "AND user_id = :uid" if user_id is not None else ""
        sql = text(
            f"""
            SELECT id, 1 - (embedding_vec <=> CAST(:q AS vector)) AS similarity
              FROM memories
             WHERE embedding_vec IS NOT NULL {uid_filter}
          ORDER BY embedding_vec <=> CAST(:q AS vector) ASC
             LIMIT :k
            """
        )
        params: dict = {"q": vec_literal, "k": k}
        if user_id is not None:
            params["uid"] = user_id
        result = await db.execute(sql, params)
        rows = result.all()
        if not rows:
            return []

        ids = [row[0] for row in rows]
        sims = {row[0]: float(row[1]) for row in rows}
        id_to_memory = await get_memories_by_ids(ids, db)

        out: list[tuple[MemorySchema, float]] = []
        for mid in ids:
            memory = id_to_memory.get(mid)
            if memory:
                out.append((memory, sims[mid]))
        return out


memory_retriever = PgvectorRetriever()
