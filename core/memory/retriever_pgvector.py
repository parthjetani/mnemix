"""pgvector-backed retriever — replacement for the in-memory numpy retriever.

NOT WIRED YET. To activate:
  1. Apply migrations/001_pgvector.sql against your Supabase project (the
     `vector` extension must be enabled on the project first).
  2. In main.py, change
         from core.memory.retriever import memory_retriever
     to
         from core.memory.retriever_pgvector import memory_retriever
  3. Drop the `memory_retriever.load(db)` call from the lifespan handler —
     pgvector does the work in SQL, there is no in-memory index to warm.
  4. Once verified in staging, delete core/memory/retriever.py and the BYTEA
     `embedding` column from the schema.

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
        memory_id: str,
        embedding: np.ndarray,  # noqa: ARG002 — store.save_memory writes the vector
    ) -> None:
        """No-op. core.memory.store.save_memory persists embedding_vec directly."""

    async def search(
        self,
        query_text: str,
        db: AsyncSession,
        top_k: int = 5,
    ) -> list[tuple[MemorySchema, float]]:
        from core.memory.store import _orm_to_schema  # local import to avoid cycle

        query_vec = embed(query_text).astype(np.float32)
        # pgvector literal: "[v1,v2,...]"
        vec_literal = "[" + ",".join(f"{x:.6f}" for x in query_vec.tolist()) + "]"
        sql = text(
            """
            SELECT *, 1 - (embedding_vec <=> CAST(:q AS vector)) AS similarity
              FROM memories
             WHERE embedding_vec IS NOT NULL
          ORDER BY embedding_vec <=> CAST(:q AS vector) ASC
             LIMIT :k
            """
        )
        result = await db.execute(sql, {"q": vec_literal, "k": min(top_k, 20)})
        rows = result.mappings().all()

        from database import MemoryORM
        out: list[tuple[MemorySchema, float]] = []
        for row in rows:
            # Reconstruct an ORM-shaped object for _orm_to_schema.
            orm_like = MemoryORM(**{k: v for k, v in row.items() if k != "similarity"})
            out.append((_orm_to_schema(orm_like), float(row["similarity"])))
        return out


memory_retriever = PgvectorRetriever()
