"""
Organismo — semantic caching layer for multi-agent LLM systems.

Core idea: before generating, look for an echo. If a near-identical
question was answered before, serve that answer instead of paying for
a new generation. Three outcomes:

  REFLEX  (score >= reflex_threshold)  -> serve the cached answer, zero tokens
  DEJAVU  (score >= dejavu_threshold)  -> inject cached answers as context, then generate
  MISS    (score below dejavu_threshold) -> generate normally, then write back

The key insight that makes this work: embed the QUESTION only.
Storing "question + answer" together and comparing against a new
question dilutes similarity -- an identical question will never score
1.0 against a blob that also contains the answer. Embed the key,
store the value. Validated in production: identical query -> 1.0,
paraphrase -> ~0.87, unrelated -> ~0.52.
"""
from __future__ import annotations
import time
import threading
import dataclasses
from typing import Callable, Optional


@dataclasses.dataclass
class Echo:
    title: str
    text: str
    score: float


class Organismo:
    """
    Wrap any (store, generate) pair with a semantic cache.

    `store` must implement:
        search(query: str, k: int = 5) -> list[Echo]
        write(query: str, answer: str) -> None

    Bring your own store backend (see organismo.pg_store for a
    ready-made Postgres + pgvector implementation) -- this class has
    zero database dependencies of its own.
    """

    def __init__(
        self,
        store,
        reflex_threshold: float = 0.90,
        dejavu_threshold: float = 0.78,
        dedup_threshold: float = 0.93,
        min_query_len: int = 12,
        max_query_len: int = 2000,
        min_answer_len: int = 40,
        max_answer_len: int = 8000,
        log_fn: Optional[Callable[[dict], None]] = None,
    ):
        self.store = store
        self.reflex_threshold = reflex_threshold
        self.dejavu_threshold = dejavu_threshold
        self.dedup_threshold = dedup_threshold
        self.min_query_len = min_query_len
        self.max_query_len = max_query_len
        self.min_answer_len = min_answer_len
        self.max_answer_len = max_answer_len
        self._log = log_fn or (lambda event: None)

    def is_cacheable(self, query: str) -> bool:
        q = (query or "").strip()
        return self.min_query_len <= len(q) <= self.max_query_len

    def recall(self, query: str):
        """
        Look up a query against the organism's memory.
        Returns (mode, echoes) where mode is 'reflex', 'dejavu', 'miss', or 'skip'.
        """
        t0 = time.time()
        if not self.is_cacheable(query):
            return "skip", []

        echoes = self.store.search(query, k=5)
        top = echoes[0].score if echoes else 0.0
        ms = int((time.time() - t0) * 1000)

        if echoes and top >= self.reflex_threshold:
            self._log({"kind": "reflex", "q": query[:120], "score": round(top, 3), "ms": ms})
            return "reflex", echoes
        if echoes and top >= self.dejavu_threshold:
            self._log({"kind": "dejavu", "q": query[:120], "score": round(top, 3), "ms": ms})
            return "dejavu", echoes[:3]

        self._log({"kind": "miss", "q": query[:120], "score": round(top, 3), "ms": ms})
        return "miss", []

    def reflex_answer(self, echo: Echo) -> str:
        """Extract the answer half of a stored (question, answer) echo."""
        text = echo.text
        marker = "\nR: "
        if marker in text:
            return text.split(marker, 1)[1]
        return text

    def dejavu_context(self, echoes) -> str:
        """Build a system-prompt fragment from the top echoes."""
        lines = [f"- {e.title}: {e.text[:350]}" for e in echoes]
        return "Ecos de memoria del organismo (usa si son relevantes):\n" + "\n".join(lines)

    def remember(self, query: str, answer: str) -> None:
        """
        Write-back a fresh generation as a new echo, async, fire-and-forget.
        Deduplicates against near-identical existing echoes so the memory
        doesn't grow fat restating the same fact.
        """
        answer = (answer or "").strip()
        if not (self.min_answer_len < len(answer) < self.max_answer_len):
            return

        def _write():
            try:
                existing = self.store.search(query, k=1)
                if existing and existing[0].score >= self.dedup_threshold:
                    self._log({"kind": "dedup_skip", "q": query[:120]})
                    return
                self.store.write(query, answer)
                self._log({"kind": "stored", "q": query[:120]})
            except Exception as e:  # pragma: no cover - fire and forget
                self._log({"kind": "store_fail", "q": query[:120], "error": str(e)[:200]})

        threading.Thread(target=_write, daemon=True).start()
