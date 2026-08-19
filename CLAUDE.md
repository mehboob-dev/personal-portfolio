# CLAUDE.md — mehboob-portfolio

Guidance for Claude Code (and other AI agents) working in this repository.

## Project overview

Personal portfolio for **Mehboob Meghani** — Quant Developer (C#, .NET, C++ interop). Single scrolling CV-driven page + **dynamic QR manager** with scan analytics.

- **Stack**: Flask 3 (WSGI) · Jinja2 · SQLAlchemy 2 · Flask-Migrate · flask-login · flask-wtf (CSRF) · SQLite (dev) / MySQL (prod) · vanilla JS · `uv`
- **Entry point**: `wsgi.py` → `create_app()` in `app/__init__.py`
- **Repo**: public, on `master`

## Commands

```bash
uv sync                              # install deps
uv run flask --app wsgi:app init-db # create tables + sync admin user
uv run flask seed                   # sync admin user from secrets.json
uv run flask --app wsgi:app run     # dev server → http://localhost:5000
uv run pytest                       # run tests
uv run flask db migrate -m "msg"    # schema change → migration
uv run flask db upgrade             # apply migrations
```

## Architecture (30-second version)

- `app/public.py` — single-page home + legacy anchor redirects (`/about` → `#about`, etc.)
- `app/qr.py` — `GET /r/<slug>`: record scan → 302 to the QR's **mutable** destination
- `app/admin.py` — login-gated admin: campaigns, QR CRUD, scan analytics, leads + CSV export
- `app/models.py` — `Campaign`, `QrCode`, `Scan`, `Lead`, `AdminUser` (one file, plain tables)
- `app/helpers.py` — JSON loading, slugify, UA parsing, IP anonymization (sha256, never raw IP)
- `data/config.json` — site identity, hero, benchmarks, nav, themes; injected as `site`
- `data/content/*.json` — about, experience, projects, contact, trading-systems, home
- `data/secrets.json` — **gitignored**: `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- `app/static/resume/MehboobMeghaniResume.md` — downloadable CV (source: root `MehboobMeghaniResume.md`)

## Rules & conventions

1. **KISS** — one-file models, no business logic in models, no Docker, no build step.
2. **Config over code** — all personal copy in JSON. Templates render `site.*` / `content.*`; keep JSON complete.
3. **Never commit** `data/secrets.json`, `data/*.db`, `__pycache__/`, `.venv/`.
4. **Schema changes** via Alembic. On startup `_sync_admin_from_secrets()` syncs admin credentials from `secrets.json` — the app **will overwrite** an existing admin's password if `secrets.json` differs (intended; see `app/__init__.py`).
5. **Privacy by design** (QR scans): store only `ip_hash` (sha256) — never the raw IP; device/browser/OS parsed from UA; geolocation from headers when present.
6. **Soft-delete pattern**: `is_deleted` flag + admin restore/purge on campaigns, QRs, scans, leads.
7. **CSRF global** — every form POST needs `{{ csrf_token() }}`.
8. **QR destination URLs are validated** (`_valid_destination_url` in `app/admin.py`) before save.
9. **Frontend**: vanilla JS, no build. `app/static/js/hero.js` (ticker/hero), `theme.js` (themes: systems-light, monochrome, quant-dark, warm-monograph). Use design tokens (`var(--...)` from `app/static/css/app.css` + `home.css`), never hardcoded colors.
10. **Legacy anchor routes** must stay — tests assert `LEGACY_ANCHORS` redirects (302 to `#section`).
11. **Shared table system** — every grid (admin campaigns/leads/qr_list/qr_stats, dashboard + QR-stats summary grids) uses `window.TableKit.create()` from `app/static/js/table.js`; helpers/editors are `TableKit.*`, never redefined in templates. Keep the file **byte-identical** with `itqan-trades/app/static/js/table.js` — edit both copies together.
12. **Git constraints**: Never create git worktrees, make commits, or push changes unless explicitly instructed by the user.
13. **Changelog updates**: Update `docs/changelog.md` on every user-visible change or fix.

## Testing

- `tests/test_public.py` — home renders, legacy redirects, sections present.
- `tests/test_admin.py` — login, QR CRUD, validation.
- `tests/test_qr.py` — redirect flow, scan recording.
- `tests/conftest.py` — in-memory SQLite fixtures.
- Run `uv run pytest` after any route/model/template change.

## Docs

Full documentation in [`docs/`](docs/index.md): index, instructions, architecture, database, content-model, admin, qr-manager, deployment, frontend, changelog. **Update the changelog on user-visible changes.**

## Related projects

- **`itqan-trades/`** (sibling, private repo) — business site; the portfolio links to its `/expo` demo via `config.json → site.expo_url`.
- Both share the stack/design; docs index lives at workspace root `../docs/index.md`.

## Gotchas

- `_sync_admin_from_secrets()` runs on every startup — if you change `secrets.json` credentials, the DB user is updated automatically.
- Relative SQLite paths resolved against `data/` (`_resolve_db_url`).
- UA parsing uses `user-agents` lib; `parse_user_agent` is safe on garbage input.
- Scan geo depends on proxy headers (CF/Vercel/Nginx) — absent headers mean `country=None` (marked "Local Dev" for localhost).
