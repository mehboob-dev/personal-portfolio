# mehboob-portfolio

Personal portfolio for **Mehboob Meghani** — Quant Developer (C#, .NET, C++ interop).
Purely personal: CV-driven content, plus the **dynamic QR manager + scan analytics** admin.

Public repo. Everything about me is JSON-configurable — see `app/config.json` and `app/content/*.json`.

## Stack
Flask (WSGI) · Jinja2 · SQLAlchemy · SQLite (dev) / MySQL (prod) · Vanilla JS · `uv`

## Quick start

```bash
uv sync
uv run flask --app wsgi:app init-db   # creates tables + admin user
uv run flask --app wsgi:app run
```

Then:
- Public site: http://localhost:5000/ (single scrolling page)
- Admin: http://localhost:5000/admin (user/pass from `secrets.json`)

## Config

Everything is JSON-configurable — no hard-coded personal copy:
- `app/config.json` — site identity, hero (typed roles, ticker symbols, CTAs), benchmark stats, engine pipeline, anchor nav, `site.expo_url`.
- `app/content/*.json` — page copy (about incl. skills matrix + education, experience, projects with links, contact). Source: `MehboobMeghaniResume.md`.
- `app/static/resume/MehboobMeghaniResume.md` — the downloadable CV.
- `secrets.json` — **gitignored**; copy `secrets.example.json` → `secrets.json`. Holds `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`. All secrets live here, not in code or env files.

> The interactive expo demo lives on the Itqan Trades site (`https://itqantrades.com/expo`) — the portfolio links out to it via `config.json → site.expo_url`.

## QR manager

- `/r/<slug>` → records a scan, 302-redirects to the QR code's current destination.
- Destinations are **mutable** in the admin — edit any time, the printed QR keeps working.
- Admin: campaigns, QR CRUD, scan analytics (device/browser/OS, anonymized), leads + CSV export.

See `DOCS/qr-manager.md` for the full spec.

## Deploy (Cloudmate Bronze / cPanel, WSGI)

See `DOCS/deployment.md`. Short version: point the Python App at this repo, `uv`/pip install, set `DATABASE_URL` to MySQL in `secrets.json`, run Alembic, map the subdomain.

> **KISS**: no Docker, no Node build, no frontend framework. One Flask app, one repo, one DB.
