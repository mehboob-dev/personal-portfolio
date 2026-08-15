# mehboob-portfolio — Deployment

cPanel/WSGI flow (same as the sibling site). Prod uses **MySQL** (`portfolio_db`), dev uses SQLite.

## Prod topology

```mermaid
flowchart LR
    U[Visitors] --> DNS[mehboob.itqantrades.com]
    DNS --> CDN[Cloudflare optional]
    CDN --> CP[cPanel Apache/Python App]
    CP --> WSGI[wsgi.py]
    WSGI --> APP[Flask app]
    APP --> MYSQL[(MySQL portfolio_db)]
    APP --> FS[(data/config.json<br/>content/*.json)]
    CAM[Camera scanners] -->|/r/slug| APP
```

## Prereqs on the server

- Python ≥ 3.11
- MySQL database `portfolio_db` (user + password)
- Git access to the public repo (or upload zip)

## Steps

### 1. Get the code

```bash
git clone <repo-url> mehboob-portfolio
cd mehboob-portfolio
uv sync --no-dev        # or pip install -e .
```

### 2. Configure secrets

```bash
cp data/secrets.example.json data/secrets.json
```

Set:

```json
{
  "DATABASE_URL": "mysql+pymysql://portfolio_user:STRONG_PASSWORD@localhost/portfolio_db",
  "SECRET_KEY": "long-random-string",
  "ADMIN_USERNAME": "admin",
  "ADMIN_PASSWORD": "strong-admin-password"
}
```

> `secrets.json` is gitignored — deploy it separately.

### 3. Database

```bash
uv run flask --app wsgi:app db upgrade    # apply Alembic migrations
# or dev-only convenience: uv run flask --app wsgi:app init-db
```

### 4. WSGI entrypoint

`wsgi.py` exposes `app`. In cPanel "Setup Python App":

- App root: `mehboob-portfolio/`
- Entry point: `wsgi.py`
- Application: `app`
- Python version: 3.11+

### 5. Verify

```bash
curl -I https://mehboob.itqantrades.com/
curl https://mehboob.itqantrades.com/admin          # expect 302 → /admin/login
curl -I https://mehboob.itqantrades.com/r/<slug>   # expect 302 → destination
```

## Updating

```bash
git pull
uv sync --no-dev
uv run flask db upgrade          # if schema changed
# restart the Python app in cPanel (or touch wsgi.py)
```

Content JSON changes apply on next request — no restart needed.

## Rollback

- Code: `git revert <sha>` then redeploy.
- DB: `uv run flask db downgrade -1` (dev) or MySQL backup restore (prod).
- Content: git history on `data/`.

## DNS / TLS

- Point `mehboob.itqantrades.com` A record at the host.
- cPanel AutoSSL or Cloudflare for TLS.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| 502/500 after deploy | missing `secrets.json`, wrong `DATABASE_URL` |
| Admin 500 | tables missing → `db upgrade` |
| QR 404 | slug soft-deleted or table missing |
| Geo fields empty | no proxy headers (Cloudflare off) |
| Static 404s | app root path wrong in cPanel |

## Related

- [instructions.md](instructions.md) — dev setup
- Sibling deploy: `../itqan-trades/docs/deployment.md`
