# Contributing to Organismo

This is young software, extracted from a production system on July 9, 2026. Contributions welcome, especially:

- **Alternative store backends** — Redis + vector search, SQLite + sqlite-vec, Qdrant, or anything else with cosine similarity
- **Outcome-based learning** — report whether a served echo was actually useful, and let the reflex/dejavu thresholds adapt from that signal (inspired by MemClaw's approach to the same problem)
- **Basic contradiction detection** — flag when a new answer conflicts with a recent echo on the same topic, before writing it back
- **Tests** — there are none yet, be gentle

## How to contribute

1. Fork the repo
2. Open an issue describing what you want to change before writing code, for anything non-trivial
3. Keep PRs small and focused
4. Match the existing style: plain functions, minimal dependencies, no framework lock-in

## Code of conduct

Be direct, be kind. A bug report with a reproducible example is worth more than a paragraph of praise.
