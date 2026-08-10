# mehboob-portfolio

Personal portfolio + trading-engine showcase + **dynamic QR manager** for Mehboob Meghani.

Public repo. Everything non-secret is configurable via JSON — see `app/config.json` and `app/content/*.json`.

## Stack
Flask (WSGI) · Jinja2 · SQLAlchemy · SQLite (dev) / MySQL (prod) · HTMX-free vanilla JS · Lightweight Charts · `uv`

## Quick start

```bash
uv sync
uv run flask --app wsgi:app init-db   # creates tables + admin user
uv run flask --app wsgi:app run
```

Then:
- Public site: http://localhost:5000/
- Expo demo: http://localhost:5000/expo
- Admin: http://localhost:5000/admin (user/pass from `secrets.json`)

## Config

- `app/config.json` — site identity, benchmark stats, nav, engine pipeline, expo strategies.
- `app/content/*.json` — page copy (home, about, experience, projects, trading_systems).
- `data/*.json` — expo replay datasets.
- `secrets.json` — **gitignored**; copy `secrets.example.json` → `secrets.json`. Holds `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`. All secrets live here, not in code or env files.

## QR manager

- `/r/<slug>` → records a scan, 302-redirects to the QR code's current destination.
- Destinations are **mutable** in the admin — edit any time, the printed QR keeps working.
- Admin: campaigns, QR CRUD, scan analytics (device/browser/OS, anonymized), leads + CSV export.

See `DOCS/qr-manager.md` for the full spec.

## Deploy (Cloudmate Bronze / cPanel, WSGI)

See `DOCS/deployment.md`. Short version: point the Python App at this repo, `uv`/pip install, set `DATABASE_URL` to MySQL in `secrets.json`, run Alembic, map the subdomain.

> **KISS**: no Docker, no Node build, no frontend framework. One Flask app, one repo, one DB.
