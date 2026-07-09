# Organismo

**Stop paying your LLM to recompute the same thing twice.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9+-black?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-compatible-black?style=flat-square)
![Status](https://img.shields.io/badge/status-early-orange?style=flat-square)

[English](README.md) · [Español](README.es.md)

## What this is

A semantic caching layer for multi-agent LLM systems. Before your system generates a response, it checks whether it already answered a near-identical question — and if so, serves that answer for free instead of paying for another generation.

Three outcomes on every query:

- **reflex** (similarity ≥ 0.90) — serve the cached answer directly. Zero tokens.
- **dejavu** (similarity ≥ 0.78) — inject the closest past answers as context, then generate.
- **miss** — generate normally, then write the result back to memory for next time.

Every generation makes the next one cheaper. More usage → more echoes → higher hit rate → lower marginal cost. That's the opposite of how most AI product costs scale.

## Quickstart

```bash
pip install psycopg2-binary
git clone https://github.com/turbillon50/organismo && cd organismo
```

```python
from organismo.cache import Organismo
from organismo.pg_store import PgVectorStore
from organismo.middleware import with_organismo

store = Organismo(
    PgVectorStore(dsn="postgres://...", embed_fn=your_embed_function, dims=768)
)
handler = with_organismo(store, your_generate_function)

response = handler({"messages": [{"role": "user", "content": "What is X?"}]})
```

Or skip the infrastructure entirely and connect as a hosted MCP server, live in 30 seconds:

```json
{
  "mcpServers": {
    "organismo": {
      "url": "https://mcp.mindcontextia.one/mcp/your-slug/sse",
      "headers": { "Authorization": "Bearer your-api-key" }
    }
  }
}
```

Get a free key at [mindcontextia.one](https://mindcontextia.one).

## Why this exists

I built this after burning $200/day in inference tokens building a product from scratch — mostly re-asking my own agents the same handful of questions about my own codebase, over and over, because LLMs have no memory between calls. The fix ended up being embarrassingly simple: embed the question, not the question-and-answer pair together. Embedding both dilutes similarity — an identical question will never score 1.0 against a blob that also contains the answer. Embed the key, store the value. Once that was fixed: identical queries hit **1.0** similarity, paraphrases land around **0.87**, unrelated queries stay near **0.52** — clean separation, measured in production, not a benchmark slide.

## How this compares

| | Organismo | Mem0 | Supermemory | MemClaw |
|---|---|---|---|---|
| Mechanism | Response-level semantic cache | Fact extraction + profile | Fact extraction + hybrid search | Governed shared memory + knowledge graph |
| MCP native | ✅ | Partial | ✅ | ✅ |
| Self-host | ✅ Apache 2.0 | ✅ Apache 2.0 | ❌ | ✅ Apache 2.0 |
| Contradiction detection | 🔧 roadmap | ❌ | ❌ | ✅ |
| Outcome-based learning | 🔧 roadmap | ❌ | ❌ | ✅ |
| Spanish-first docs | ✅ | ❌ | ❌ | ❌ |

Mem0 and Supermemory extract structured facts from conversations and build evolving profiles — a related but different mechanism. MemClaw is the closest architectural peer: governed shared memory for agent fleets, more mature on governance today. We're building toward that (see [CONTRIBUTING.md](CONTRIBUTING.md)), starting from the piece that was cheapest to get right first: don't regenerate what you already know.

## Reference implementation

- [`organismo/cache.py`](organismo/cache.py) — the core decision engine
- [`organismo/pg_store.py`](organismo/pg_store.py) — Postgres + pgvector backend
- [`organismo/middleware.py`](organismo/middleware.py) — wrap any OpenAI-compatible endpoint
- [`examples/quickstart.py`](examples/quickstart.py) — full working example

## License

Apache 2.0 — see [LICENSE](LICENSE). Use it, fork it, ship it commercially. Just keep the notice.

---

*Built by [V·Momentum](https://mindcontextia.one). Extracted from a production system running live traffic.*
