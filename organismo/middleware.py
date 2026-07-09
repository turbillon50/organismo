"""
Drop this in front of any OpenAI-compatible chat completions endpoint
to give it the organism's memory. Framework-agnostic: works with
Flask, FastAPI, a raw http.server handler, or your own router.

This mirrors the logic running in production at MindContextIA's mesh
router -- extracted, generalized, and stripped of anything tenant-specific.
"""
from __future__ import annotations
import time
from typing import Callable, Optional

from .cache import Organismo


def extract_last_user_query(body: dict, max_messages: int = 4) -> Optional[str]:
    """
    Only cache short, simple exchanges. Long conversations, streaming
    requests, and anything explicitly opted out (`no_echo: true`) skip
    the organism entirely and fall through to normal generation.
    """
    if body.get("no_echo") or body.get("stream"):
        return None
    messages = body.get("messages", [])
    if len(messages) > max_messages:
        return None
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return None
    query = user_messages[-1].get("content", "")
    return query.strip() if isinstance(query, str) else None


def with_organismo(organismo: Organismo, generate_fn: Callable[[dict], dict]):
    """
    Wrap a generate_fn(body) -> OpenAI-style response dict with the
    organism's reflex / dejavu / miss decision.
    """

    def handler(body: dict) -> dict:
        query = extract_last_user_query(body)

        if not query:
            return generate_fn(body)

        mode, echoes = organismo.recall(query)

        if mode == "reflex":
            answer = organismo.reflex_answer(echoes[0])
            return {
                "id": f"echo-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "model": body.get("model", "organismo"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": answer},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "_organismo": {"mode": "reflex", "score": echoes[0].score},
            }

        if mode == "dejavu":
            context = organismo.dejavu_context(echoes)
            messages = body.get("messages", [])
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = messages[0]["content"] + "\n\n" + context
            else:
                body["messages"] = [{"role": "system", "content": context}] + messages

        response = generate_fn(body)

        try:
            answer = response["choices"][0]["message"]["content"]
            organismo.remember(query, answer)
        except (KeyError, IndexError, TypeError):
            pass

        return response

    return handler
