# Step-by-Step Guide — Deploy Both Flask Apps to cPanel Shared Hosting

This guide takes **two Flask apps** — `mehboob-portfolio` (personal portfolio + QR manager)
and `itqan-trades` (business site) — from a Windows dev machine to a single **cPanel shared
hosting** account, side by side on two domains/subdomains, each with its own MySQL database.

| Site | Domain (example) | Repo | MySQL DB (example) | Purpose |
|---|---|---|---|---|
| 1 · Portfolio | `mehboob.itqantrades.com` | `mehboob-portfolio` (public) | `portfolio_db` | CV site + QR manager |
| 2 · Itqan Trades | `itqantrades.com` | `itqan-trades` (private) | `itqan_db` | Trading services + signals |

> The two apps never import each other. Everything below is **identical per site** — only
> the folder name, domain, DB name, and values in `secrets.json` differ.

---

## What you need before starting

- cPanel hosting with **"Setup Python App"** (most shared hosts offer it; if yours uses
  `passenger_wsgi.py` instead, the WSGI file is the same `wsgi.py`, just renamed). This guide
  assumes **Setup Python App**.
- **SSH access** to the account (or use cPanel **File Manager** + **Terminal** — every step
  below can be done through either).
- **Two domain names / subdomains** (e.g. `itqantrades.com` and `mehboob.itqantrades.com`)
  already pointed at the host (A record / nameservers), or you will map them later.
- Python **3.11+** chosen in the Python App settings.
- The code from both repos (they are **local-only right now** — see Step 1).
- Your hosting plan must allow **2 Python Apps** (some plans limit them).

---

## Step 1 — Get the code onto the server

The repos are currently **local-only** (no GitHub remote yet). You have two options:

**Option A — push to GitHub first (recommended for future updates):**

```bash
# on your Windows machine, once per repo
cd D:\Work\MyPortfolio\mehboob-portfolio
git init                          # if not already
git add .
git commit -m "ready for deploy"
gh repo create mehboob-portfolio --private --source . --push
# repeat for itqan-trades
```

Then on the server (SSH):

```bash
cd ~
git clone https://github.com/<you>/mehboob-portfolio.git
git clone https://github.com/<you>/itqan-trades.git
```

**Option B — upload a zip (no git):**

1. On Windows, zip each project folder (`mehboob-portfolio/`, `itqan-trades/`).
   **Important:** delete `.venv/`, `data/*.db`, `__pycache__/`, and `data/secrets.json`
   first — they must NOT be uploaded (they are gitignored for a reason).
2. cPanel → **File Manager** → upload each zip into your home directory.
3. Right-click each zip → **Extract**. You get `~/mehboob-portfolio/` and `~/itqan-trades/`.

Either way, you end up with two folders in your home directory:

```
~/
├── mehboob-portfolio/     ← app 1
└── itqan-trades/          ← app 2
```

---

## Step 2 — Create the two MySQL databases

cPanel → **MySQL Databases** → do this **twice** (once per site):

| Part | Site 1 (portfolio) | Site 2 (itqan) |
|---|---|---|
| Database name | `portfolio_db` | `itqan_db` |
| Database user | `portfolio_user` | `itqan_user` |
| Password | strong random one | strong random one |
| Privileges | **ALL** on that DB only | **ALL** on that DB only |

> cPanel often prefixes names with your account, e.g. `cand_portfolio_db`. **Write down the
> full names and the hostname shown (usually `localhost`)** — you need them for Step 4.

---

## Step 3 — Install the dependencies per site

SSH into the account, then **for each site** (run this twice — once in each folder):

> ⚠️ If your host has no SSH: use cPanel → **Setup Python App → "Create Application"**,
> then the app's **"Run Python Script"** console to run the same commands. The `flask` and
> `pip` commands below are what matter.

```bash
cd ~/mehboob-portfolio            # then repeat in ~/itqan-trades

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e .                  # installs everything from pyproject.toml
```

What this does:

- Creates a virtualenv **inside the app folder** (`.venv`).
- Installs the app itself in editable mode (`pip install -e .` uses `pyproject.toml` +
  hatchling — no `requirements.txt` needed).
- Installs **all** declared dependencies, including `pymysql`, `flask-sqlalchemy`,
  `flask-migrate`, `flask-login`, `flask-wtf` — and for the portfolio additionally
  `user-agents`, `qrcode`, `pillow`.

> If `uv` is available on the host, `uv sync` achieves the same thing — plain pip is fine.

**Verify per site:**

```bash
cd ~/mehboob-portfolio && .venv/bin/python -c "import flask, flask_sqlalchemy, pymysql; print('deps ok')"
cd ~/itqan-trades      && .venv/bin/python -c "import flask, flask_sqlalchemy, pymysql; print('deps ok')"
```

---

## Step 4 — Create `secrets.json` on the server (per site)

`secrets.json` is **gitignored** — it never ships in the zip/repo, so you create it fresh
on the server. Both apps read `data/secrets.json` at startup
(see `app/__init__.py → _load_secrets()`); if it is missing they fall back to
`secrets.example.json` **dev defaults — never run prod on those**.

**Site 1 — portfolio** (`~/mehboob-portfolio/data/secrets.json`):

```json
{
  "DATABASE_URL": "mysql+pymysql://<FULL_DB_USER>:<DB_PASSWORD>@localhost/<FULL_DB_NAME>",
  "SECRET_KEY": "<long random hex, e.g. python -c 'import secrets; print(secrets.token_hex(32))'>",
  "ADMIN_USERNAME": "mehboob",
  "ADMIN_PASSWORD": "<strong admin password>"
}
```

**Site 2 — itqan** (`~/itqan-trades/data/secrets.json`) — same shape, plus the `API_KEY`
used by external bots hitting `/api/v1` with `X-API-Key`:

```json
{
  "DATABASE_URL": "mysql+pymysql://<FULL_DB_USER>:<DB_PASSWORD>@localhost/<FULL_DB_NAME>",
  "SECRET_KEY": "<long random hex>",
  "ADMIN_USERNAME": "admin",
  "ADMIN_PASSWORD": "<strong admin password>",
  "API_KEY": "<random api key for bots>"
}
```

Replace `<FULL_DB_USER>`, `<DB_PASSWORD>`, `<FULL_DB_NAME>` with what cPanel showed you in
Step 2 (including the account prefix if any). Change the `ADMIN_USERNAME`/`ADMIN_PASSWORD`.

> Never commit this file. It is gitignored in both repos.

---

## Step 5 — Create the Python Apps in cPanel

cPanel → **Setup Python App** → **Create Application**, **twice** (once per site):

| Setting | Site 1 (portfolio) | Site 2 (itqan) |
|---|---|---|
| Python version | 3.11 (or newest available ≥3.11) | same |
| Application root | `mehboob-portfolio` | `itqan-trades` |
| Application URL | `mehboob.itqantrades.com` | `itqantrades.com` |
| Application startup file | **`wsgi.py`** | **`wsgi.py`** |
| Application entry point | **`app`** | **`app`** |

> Both apps expose the WSGI callable as `app = create_app()` at module level in `wsgi.py` —
> that is exactly what cPanel's "entry point" field expects. `app.run()` only executes under
> `if __name__ == "__main__"`, so it never runs under the WSGI server.

If you set the URL before the domains exist you may get an error — you can map the
domain/subdomain to the app later (Step 7). The common flow: **create the subdomain first
in cPanel → Domains**, then reference it here.

---

## Step 6 — Initialize the databases (schema + admin user)

For **each site**, from its folder on the server:

```bash
# Site 1:
cd ~/mehboob-portfolio && .venv/bin/flask --app wsgi:app db upgrade

# Site 2:
cd ~/itqan-trades && .venv/bin/flask --app wsgi:app db upgrade
```

What this does:

- Reads `data/secrets.json` → connects to MySQL with the credentials you set.
- Applies the **committed Alembic migrations** (both repos carry the initial schema
  migration in `migrations/versions/`; itqan has 3, portfolio has 1).
- Creates all tables. **No admin user is created yet** (see below).

> `flask db upgrade` is the canonical prod path. `flask --app wsgi:app init-db` also exists
> as a dev convenience but is **not** the deployed path.

**Create/sync the admin user:**

```bash
# Site 1 (portfolio): the app auto-syncs the admin from secrets.json on every startup,
# so no extra command is needed — start the app and the admin user exists.
# To force it now:
cd ~/mehboob-portfolio && .venv/bin/flask --app wsgi:app seed

# Site 2 (itqan): the admin user comes from secrets.json at init-db time.
# Run init-db (idempotent — it only creates the user if missing, and seeds
# services + blog posts the first time):
cd ~/itqan-trades && .venv/bin/flask --app wsgi:app init-db
```

---

## Step 7 — Restart both apps

cPanel → **Setup Python App** → for each app click **Restart**, then open the app's
**"Open Application"** link. The app takes its first request, Flask starts, and the
portfolio's `_sync_admin_from_secrets()` runs on startup.

---

## Step 8 — Verify each site

**Site 1 — portfolio** (`https://mehboob.itqantrades.com`):

```bash
curl -I https://mehboob.itqantrades.com/                   # 200
curl -I https://mehboob.itqantrades.com/admin              # 302 → /admin/login
curl -I https://mehboob.itqantrades.com/r/<your-qr-slug>   # 302 → destination
```

Browser checks:

- Home renders the single scrolling CV page, resume download works.
- `/admin` shows the login; log in with `ADMIN_USERNAME`/`ADMIN_PASSWORD` from Step 4.
- Create a campaign + QR → scan it with your phone → scan is recorded in admin analytics.

**Site 2 — itqan** (`https://itqantrades.com`):

```bash
curl -I https://itqantrades.com/                  # 200
curl -I https://itqantrades.com/admin             # 302 → /admin/login
curl https://itqantrades.com/api/v1/signals       # JSON (needs X-API-Key header to POST)
```

Browser checks:

- Home + `/services`, `/pms`, `/signals`, `/records`, `/blog`, `/contact` render.
- `/admin` logs in with the itqan credentials from Step 4.
- `/contact` form → entry appears in `/admin/leads`.

Cross-site check: the portfolio's "Watch the live demo" button links to
`https://itqantrades.com/expo` via `mehboob-portfolio/data/config.json → site.expo_url` —
confirm the URL matches whatever the itqan site actually serves.

---

## Step 9 — Enable TLS (Let's Encrypt)

- cPanel → **SSL/TLS Status** or **Domains → SSL** → issue a free **Let's Encrypt** cert
  for both domains/subdomains.
- Skip `AutoSSL` if your host uses it — it covers them automatically.
- Test: `https://` loads with a valid padlock for both sites; no mixed-content warnings.

---

## Step 10 — Restart persistence & health check

- Python Apps on cPanel are usually started by the host's process manager (they restart
  automatically on reboot / after the app is killed). If the host requires a manual
  restart, note it in an ops note.
- **Health check after a host reboot:** hit both domains; if either returns 502/503,
  open cPanel → Setup Python App → Restart that app.

---

## Updating a site later

```bash
# on the server, per site:
cd ~/mehboob-portfolio          # or ~/itqan-trades
git pull                        # or re-upload the zip
.venv/bin/pip install -e .      # if dependencies changed
.venv/bin/flask --app wsgi:app db upgrade   # only if schema changed
```

Then **Restart** the Python App in cPanel.

> Content edits (JSON files under `data/`) take effect on the **next request** — no
> restart needed; both apps read them per request.

---

## Rollback

| Layer | How |
|---|---|
| Code | Revert the commit, redeploy, restart. |
| Database | MySQL backup (cPanel → Backup / phpMyAdmin), or `flask db downgrade -1` for the last migration. |
| Content | `git` history on `data/*.json`. |

---

## Troubleshooting

| Symptom | Likely cause & fix |
|---|---|
| 502/500 after first deploy | `data/secrets.json` missing or wrong `DATABASE_URL` → fix Step 4. Check the Python App error log (Setup Python App → "Open error log"). |
| "Access denied for user" | DB user/name has an account prefix in cPanel (`cand_db`) — use the **full** name in `DATABASE_URL`. |
| Admin login 500 / tables missing | Run `flask db upgrade` (Step 6) — or `init-db` for itqan. |
| Itqan API returns 401 | `API_KEY` in `secrets.json` ≠ the key the bot sends. |
| Static files 404 (CSS/JS/images) | Application root path wrong in Setup Python App settings — must be the folder containing `wsgi.py`. |
| `pip install -e .` fails with build error | Python < 3.11, or hatchling missing — install `pip install --upgrade pip setuptools wheel` then retry. |
| QR scan works but geo fields empty | No proxy headers (Cloudflare off) — expected; city/country stay empty. |
| Both sites down after reboot | cPanel didn't auto-restart the apps — restart each in Setup Python App. |
| Windows zip includes junk | Re-zip WITHOUT `.venv/`, `data/*.db`, `__pycache__/`, `data/secrets.json` (Step 1, Option B). |

---

## Resource reality check

| Item | App 1 (portfolio) | App 2 (itqan) |
|---|---|---|
| Python process | ~1 × small | ~1 × small |
| RAM | ~100–200 MB | ~100–200 MB |
| MySQL DBs | 1 | 1 |
| Static files | Flask-served from `app/static/` (fine at this scale) | same |

Two Flask apps on one Bronze-style shared plan is comfortable — the heavy trading engine
must **never** live in these web apps.

---

_Companion docs: `data/config.json → site.expo_url` cross-link check (Step 8). This guide is
identical in both repos — keep the copies in sync._