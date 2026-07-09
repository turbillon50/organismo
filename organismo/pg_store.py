"""
Postgres + pgvector backend for Organismo.

Schema (created automatically on first use):
    chunks(id, source, title, content, embedding vector(N), created_at)

The embedding column stores the QUESTION vector. The content column
stores "Q: <question>\\nR: <answer>" so the value carries both, but
similarity is always computed against the key alone.
"""
from __future__ import annotations
from typing import Callable, List
import psycopg2

from .cache import Echo


class PgVectorStore:
    def __init__(
        self,
        dsn: str,
        embed_fn: Callable[[str], List[float]],
        table: str = "chunks",
        dims: int = 768,
    ):
        """
        dsn      : Postgres connection string (the `vector` extension must be available)
        embed_fn : any function str -> list[float], bring your own embedding model
        dims     : must match the output dimension of embed_fn
        """
        self.dsn = dsn
        self.embed_fn = embed_fn
        self.table = table
        self.dims = dims
        self._ensure_schema()

    def _conn(self):
        return psycopg2.connect(self.dsn)

    def _ensure_schema(self):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id bigserial PRIMARY KEY,
                    source text DEFAULT 'echo',
                    title text,
                    content text,
                    embedding vector({self.dims}),
                    created_at timestamptz DEFAULT now()
                );
                """
            )
            conn.commit()

    def search(self, query: str, k: int = 5) -> List[Echo]:
        vec = self.embed_fn(query)
        if not vec:
            return []
        vlit = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT title, content, 1 - (embedding <=> %s::vector) AS score
                FROM {self.table}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (vlit, vlit, k),
            )
            rows = cur.fetchall()
        return [Echo(title=r[0] or "", text=r[1] or "", score=float(r[2])) for r in rows]

    def write(self, query: str, answer: str) -> None:
        vec = self.embed_fn(query)
        if not vec:
            return
        vlit = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        content = f"Q: {query[:1500]}\nR: {answer[:6000]}"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self.table} (source, title, content, embedding)
                VALUES ('echo', %s, %s, %s::vector);
                """,
                (query[:180], content, vlit),
            )
            conn.commit()
