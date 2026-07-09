# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/), versioning follows [SemVer](https://semver.org/).

## [0.1.0] - 2026-07-09

### Added
- Core `Organismo` class: reflex / dejavu / miss decision engine
- `PgVectorStore`: Postgres + pgvector backend implementation
- `with_organismo` middleware for wrapping any OpenAI-compatible endpoint
- Quickstart example
- Bilingual README (EN/ES)

Thresholds and dedup logic validated in production at [MindContextIA](https://mindcontextia.one):
identical query → 1.0 similarity, paraphrase → ~0.87, unrelated → ~0.52.
