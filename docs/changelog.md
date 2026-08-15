# mehboob-portfolio — Changelog

All notable changes, newest first. Format: `YYYY-MM-DD — summary (commit)`.

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
