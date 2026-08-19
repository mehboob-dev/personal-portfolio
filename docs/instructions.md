# mehboob-portfolio — Developer Instructions

Everything you need to get the app running, understand the workflow, and not break things.

## Prerequisites

- Python **≥ 3.11**
- [`uv`](https://docs.astral.sh/uv/) (package manager — `uv.lock` is checked in)
- Git

## First-time setup

```bash
# 1. Install dependencies from the lockfile
uv sync

# 2. Create secrets from the example (REQUIRED before first run)
cp data/secrets.example.json data/secrets.json
#    edit values: DATABASE_URL, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

# 3. Create the database and sync the admin user
uv run flask --app wsgi:app init-db

# 4. Run the dev server
uv run flask --app wsgi:app run
```

- Public site → http://localhost:5000/ (single scrolling page)
- Admin → http://localhost:5000/admin (credentials from `secrets.json`)

> On every startup `_sync_admin_from_secrets()` in `app/__init__.py` syncs the admin user to `secrets.json` — change credentials there and the DB user follows automatically.

## Daily workflow

| Task | Command |
|---|---|
| Run tests | `uv run pytest` |
| Run one test | `uv run pytest tests/test_qr.py::test_name -v` |
| Apply migrations | `uv run flask db upgrade` |
| Generate migration | `uv run flask db migrate -m "msg"` |
| Sync admin user | `uv run flask seed` |

## Project structure

```
mehboob-portfolio/
├── app/
│   ├── __init__.py     # create_app factory, _sync_admin_from_secrets, CLI
│   ├── public.py       # single-page site + legacy anchor redirects
│   ├── qr.py           # QR redirect engine (/r/<slug>)
│   ├── admin.py        # admin blueprint (campaigns, QRs, scans, leads)
│   ├── models.py       # all SQLAlchemy models (one file)
│   ├── helpers.py      # JSON loading, slugify, UA parse, IP anonymization
│   ├── extensions.py   # shared Flask extensions
│   ├── static/         # css/, img/, js/, resume/
│   └── templates/
│       ├── base.html            # public layout
│       ├── admin/base.html      # admin layout
│       └── public/home.html     # the whole single page
├── data/
│   ├── config.json              # site config (identity, hero, benchmarks, nav, themes)
│   ├── content/*.json           # page copy (about, experience, projects, ...)
│   ├── secrets.json             # gitignored — real secrets
│   ├── secrets.example.json     # template
│   └── app.db                   # dev SQLite
├── migrations/                  # Alembic
├── tests/                       # pytest suite
├── wsgi.py                      # entrypoint (cPanel + flask run)
└── pyproject.toml
```

See [architecture.md](architecture.md) for the full picture and [content-model.md](content-model.md) for what each JSON file controls.

## Secrets (do not commit)

`data/secrets.json` is **gitignored**. Keys:

| Key | Used for |
|---|---|
| `DATABASE_URL` | SQLAlchemy URI (`sqlite:///data/app.db` dev, `mysql+pymysql://...` prod) |
| `SECRET_KEY` | Flask session signing |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Admin login (synced at startup) |

Fallback: missing `secrets.json` → `secrets.example.json` → dev defaults. Never deploy with defaults.

## Editing personal copy

Everything personal is JSON:

- `data/config.json` — site identity (`identity.name`, `identity.links.*`, `identity.contact.*`, `identity.resume`), masthead, benchmarks, nav, themes, `site.expo_url`.
- `data/content/*.json` — about (intro, systems_architecture, skills, education), experience (roles, education), projects (flagship_systems, secondary_artifacts), contact (labels, interests), home (hero text), trading_systems.
- `app/static/resume/MehboobMeghaniResume.md` — the downloadable CV (source: repo-root `MehboobMeghaniResume.md`).

Edit JSON → save → refresh. No restart needed in dev (read per request).

## Testing

```bash
uv run pytest           # full suite
uv run pytest -v        # verbose
```

Covers: public render + legacy redirects, admin login/CRUD/validation, QR redirect + scan recording. Run after any route/model/template change.

## Git conventions

- Conventional-ish subjects: `fix:`, `feat:`, `docs:`, `chore:`.
- Explain the *why* in the body.
- Never commit `secrets.json`, `data/*.db`, `__pycache__/`, `.venv/`.
- This is the **PUBLIC** repo — no personal data beyond what's intentional.
- **Workflow restrictions**: Do not create git worktrees, make commits, or push changes unless explicitly instructed by the user.

## Deployment

cPanel/WSGI flow with MySQL (`portfolio_db`). Full walkthrough: [deployment.md](deployment.md).

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `flask` not found | not inside venv — use `uv run flask ...` |
| 500 on pages | missing key in `config.json` / `content/*.json` |
| Admin login rejected | update `secrets.json` → re-run `init-db` or restart (auto-sync) |
| QR 404 | slug doesn't exist or is soft-deleted |
| `user_agents` import errors | dependency not installed — `uv sync` |
