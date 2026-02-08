# Memo — lightning-fast backend for personal memos ⚡📝

A small, focused backend that stores and serves memos with minimal fuss. Built for speed, clarity, and easy deployment.

## Why this repo
- Minimal surface area: clear models, one router, simple DB wiring.
- Ready for containerized deployment via Docker / docker-compose.
- Ideal as a starter for note-taking apps, journaling services, or lightweight sync backends.

## Highlights
- Clean API routing in [router/memo.py](router/memo.py)
- Data model definitions in [models.py](models.py)
- DB wiring and migrations in [database.py](database.py)
- Validation and form handling in [forms.py](forms.py)
- Utility helpers in [utils.py](utils.py)
- Entrypoint: [main.py](main.py)

