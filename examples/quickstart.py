"""
Minimal working example: wire the organism in front of an LLM call.
Swap `ollama_embed` and `fake_llm_call` for your real providers.

Run:
    export ORGANISMO_DSN="postgres://user:pass@host/db"
    python examples/quickstart.py
"""
import os
import json
import urllib.request

from organismo.cache import Organismo
from organismo.pg_store import PgVectorStore
from organismo.middleware import with_organismo


def ollama_embed(text: str):
    body = json.dumps({"model": "nomic-embed-text", "prompt": text[:6000]}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=40).read()).get("embedding", [])


def fake_llm_call(body: dict) -> dict:
    # Replace with your real OpenAI-compatible call
    query = body["messages"][-1]["content"]
    return {
        "choices": [
            {"message": {"role": "assistant", "content": f"(generated answer for: {query})"}}
        ]
    }


def main():
    dsn = os.environ["ORGANISMO_DSN"]  # postgres connection string, pgvector enabled
    store = PgVectorStore(dsn=dsn, embed_fn=ollama_embed, dims=768)
    organismo = Organismo(store, log_fn=lambda e: print("[organismo]", e))

    handler = with_organismo(organismo, fake_llm_call)

    body = {"messages": [{"role": "user", "content": "What is MindContextIA?"}]}
    print(handler(body))
    print(handler(body))  # second call should hit reflex -- zero generation


if __name__ == "__main__":
    main()
