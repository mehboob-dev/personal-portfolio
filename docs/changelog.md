# mehboob-portfolio — Changelog

All notable changes, newest first. Format: `YYYY-MM-DD — summary (commit)`.

## 2026-08-19 — Container width matching, breakpoint unification, mobile header fix, and unified typography

- **Container Width Matching**: updated `.container` styling in `app/static/css/app.css` to match `itqan-trades` exactly (`width: 90%`, `max-width: 1600px`).
- **Breakpoint Unification**: changed mobile nav toggle and site nav media query breakpoints from `768px` to `900px` in `app/static/css/app.css`, and did the same for contact layout and responsive paddings/grids in `app/static/css/home.css`. This prevents menu wrapping on medium screens and unifies layout responsiveness breakpoints with the Tabulator table wrapper.
- **Mobile Header Fix**: removed the redundant and empty `.header-controls` container element from `app/templates/base.html` and `app/templates/admin/base.html` and cleaned up its CSS rules in `app.css`. This allows the mobile hamburger menu toggle to correctly align to the right side of the screen using the flexbox `space-between` rule, matching the clean structure of the `itqan-trades` site.
- **Unified Typography**: aligned the font loading and font variables structure in `app/static/css/app.css` to match `itqan-trades` exactly. The site now loads and uses Google Fonts `Fauna One` (for body/mono/display elements) and `Cinzel` (for headings/serif text), replacing `Plus Jakarta Sans` and `JetBrains Mono`.

---

## 2026-08-19 — Reusable JSON defaults and FontAwesome icon support

- **Generic Defaults System**: implemented generic `"defaults"` block merging dynamically for all content JSON files loaded via `get_content()` in `app/helpers.py`.
- **`data/content/education.json`**: created new content file to make education data independent of experience data.
- **`data/content/about.json`**: removed duplicate/redundant `"education"` block to adhere to DRY principles.
- **`data/content/experience.json`**: removed the `"education"` block, keeping professional experience decoupled from education.
- **`app/helpers.py`**: replaced `preprocess_projects` with a generic recursive `merge_defaults` function combined with a name-specific `preprocess_content` mapper, making fallback resolution completely deterministic at Python load-time.
- **`app/public.py`**: registered and loaded `"education"` as an independent content file in the homepage routing context.
- **`app/templates/public/home.html`**: cleaned up flagship systems, secondary artifacts, and education rendering templates by removing all Jinja2 fallback/guessing inline logic in favor of directly rendering backend-resolved values (using bracket notation `['items']` for education).
- **`tests/test_public.py`**: added unit tests to verify deterministic merging of defaults in projects JSON content loading, and to assert that education is loaded independently.

---

## 2026-08-19 — Fix table header select-all to target filtered rows

- **`app/static/js/table.js`**: modified `TableKit` table selection logic to only select/deselect active (filtered) rows when the header checkbox is clicked. The header checkbox's state (checked, unchecked, indeterminate) is automatically kept in sync with the selection status of active rows by listening to `rowSelectionChanged` and `dataFiltered` events.

---

## 2026-08-18 — Step-by-step cPanel deployment guide (`a976827`)

- **`docs/cpanel-deploy-stepbystep.md`** (new): deploy **both** Flask apps
  (mehboob-portfolio + itqan-trades) onto one cPanel shared-hosting account — repo
  transfer (GitHub push or zip), MySQL DBs + users per site, per-site venv +
  `pip install -e .`, `data/secrets.json` per site, two "Setup Python App" entries
  (`wsgi.py` + entry point `app`), `flask db upgrade` (Alembic migrations), admin
  user auto-sync on startup, restart + per-site verification (incl. QR scan flow),
  Let's Encrypt TLS, updates, rollback, troubleshooting.
- Identical copy in `itqan-trades/docs/` (shared-file convention, same as `table.js`).
- No code changes.

---

## 2026-08-16 — Unified table system (TableKit)

### Shared table module
- **`app/static/js/table.js`** (new): `window.TableKit.create(container, opts)` factory plus all filter helpers/editors, exported as `TableKit.*`. One copy per repo, kept byte-identical with `itqan-trades` (convention documented in CLAUDE.md).
- All admin grids (campaigns, leads, qr_list, qr_stats, dashboard recent scans) migrated to `TableKit.create`; per-page helper definitions and reset handlers removed.

### Static summary tables → Tabulator grids
- Dashboard + QR stats: the 6 static HTML `<table class="table">` summaries now render as Tabulator grids (`#dashboard-daily-table`, `#dashboard-device-table`, `#dashboard-os-table`, `#stats-daily-table`, `#stats-app-table`, `#stats-os-table`). Headerless layouts preserved where the old markup had no `<thead>` (device/OS/app breakdowns); daily grids keep their header row.
- All grids read `--accent-*`/`--border-*` tokens — all 4 themes style them consistently.

### Behavior
- Table header font → mono uppercase (was sans). Filters, reset, bulk select, row-click nav, counts unchanged.
- **Date filter fix** (shared `table.js`): `advancedDateFilterFunc` now parses both the filter value and the row value (ISO or DMY) and compares normalized dates — typed DMY dates against ISO row values match, and `after`/`before` work. Previously DMY input never matched ISO rows. Verified by unit cases + headless-browser E2E.

---

## 2026-08-15 — Documentation system established

### Added: `docs/` + `CLAUDE.md`

- **`docs/`** — index, instructions, architecture, database, content-model, qr-manager, admin, deployment, frontend, changelog — all Markdown with Mermaid diagrams.
- **`CLAUDE.md`** at repo root — AI-agent guidance (commands, conventions, gotchas).
- No code changes.

---

## 2026-08-14 — CSRF enabled, QR destination validated, Alembic migration (`4c2584e`)

- **CSRF global** via flask-wtf — every admin form POST now requires `{{ csrf_token() }}`.
- **QR destination URLs validated** (`_valid_destination_url` in `app/admin.py`) before save — malformed destinations rejected at edit time instead of failing redirects.
- Initial Alembic migration (`migrations/`, revision `ac309500b1c7`) — schema changes now go through `flask db migrate` / `db upgrade`.
- Admin forms updated with CSRF tokens; tests extended (88 new lines).

## 2026-08-14 — Unified design system, logo + favicon (`150bbb9`)

- `app.css` consolidated (~275 lines removed) into a single token-driven design system shared with the Itqan Trades site (White Golden palette).
- Added brand logo `WhiteGoldTransparent.png` and `favicon.png`; referenced in public + admin base templates.

## 2026-08-14 — Responsive styles + admin mobile nav (`bc3efad`)

- Responsive breakpoints for `app.css` and `home.css`.
- Hamburger mobile nav for the admin base template.

## 2026-08-14 — Only-light theme, table filters, data moved to `data/` (`d682e13`)

- **Theme system**: `theme.js` supports multiple themes via `data-theme`; added only-light default theme; `data/color_palette.json` added.
- **Table filters**: admin list pages (campaigns, leads, qr_list, qr_stats) gain client-side filters.
- **Restructure**: `app/config.json` → `data/config.json`, `app/content/*.json` → `data/content/*.json`, `secrets.example.json` → `data/secrets.example.json` (renames only, 21 files).

## 2026-08-12 — Single-page portfolio + admin trash/restore (`252f1d7`)

- **Single-page conversion**: multi-page templates removed (about, contact, experience, projects, trading_systems, expo); everything renders in `public/home.html` sections driven by `content/*.json` + `home.css` (675 lines new).
- Legacy routes `/about`, `/experience`, `/projects`, `/trading-systems`, `/contact` → 302 to `#section` anchors.
- **Admin trash/restore**: campaigns, QRs, leads get `is_deleted` soft-delete with restore; `lead_detail.html` and `qr_stats.html` added (456 lines of scan analytics UI).
- QR manager expanded: campaigns CRUD, lead details, stats pages, CSV exports.
- `hero.js` (ticker animation) replaces `expo.js`; resume added at `app/static/resume/MehboobMeghaniResume.md`.
- 43 files, 5439 insertions.

## 2026-08-11 — Initial: trading-engine showcase, expo demo, dynamic QR manager (`5502dc0`)

- Initial commit — single-page portfolio scaffold + QR manager.
- **QR manager**: dynamic redirect engine (`/r/<slug>`) with mutable destinations, scan recording (anonymized IP hash, UA parse, geo headers, UTM), admin CRUD for campaigns, QR codes, leads, stats, CSV exports.
- **Trading-engine showcase**: content-driven pages for about, experience, projects, trading systems; `/expo` interactive demo (`expo.py` + `expo.js`).
- Flask app factory + blueprints (public/admin/qr/expo), models (`Campaign`, `QrCode`, `Scan`, `Lead`, `AdminUser`), tests, `uv` packaging, `secrets.example.json`.
- 44 files, 3010 insertions.

---

## Format

```markdown
## YYYY-MM-DD — Short summary (`<commit-sha>`)

### Category
- bullet
```

Keep this file updated on every user-visible change. Reference the commit sha when possible.
