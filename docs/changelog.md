# mehboob-portfolio — Changelog

All notable changes, newest first. Format: `YYYY-MM-DD — summary (commit)`.

## 2026-08-20 — CloudLinux Python Selector UI registration & SQLAlchemy pool recovery

- **CloudLinux Python Selector Registration**: Resolved issue where `mehboob-portfolio` was missing from the cPanel **Setup Python App** web UI (`python-selector.html.tt`). Updated `/home/itqantra/.cl.selector/python-selector.json` with the exact application schema for `mehboob-portfolio` matching Python 3.11, domain `mehboob.itqantrades.com`, and startup file `passenger_wsgi.py`. Confirmed listing via `cloudlinux-selector get` CLI.
- **MySQL Idle Disconnect Recovery**: Added `pool_pre_ping=True` and `pool_recycle=280` to `SQLALCHEMY_ENGINE_OPTIONS` in `app/__init__.py` to handle dropped MySQL idle connections and eliminate `500 Internal Server Error` on `/admin/login`.
- **Deployment Script Sync**: Updated `.cpanel.yml` to include `git fetch origin master` and `git reset --hard origin/master` prior to touching `tmp/restart.txt` to ensure cPanel's "Deploy HEAD Commit" button pulls the latest code from GitHub.

---

## 2026-08-20 — Make all section copy JSON-configurable; delete unused content files and keys

- **Section headings/labels/intros fully JSON-driven**: replaced every hardcoded string in `app/templates/public/home.html` with template variables. Each section now reads its label, heading, and intro from the appropriate content JSON — no literals remain in the template.
  - Benchmarks panel header/subtitle → `site.benchmarks_panel.label` / `site.benchmarks_panel.subtitle` (new keys in `data/config.json`)
  - Section [01] Flagship Systems → `content.projects.flagship_label`, `content.projects.flagship_heading`, `content.projects.flagship_intro`
  - Section [02] Systems Architecture → `content.about.section_label`, `content.about.heading`, `content.about.intro`
  - Section [03] Chronology & Foundations → `content.experience.section_label`, `content.experience.heading`, `content.experience.intro`
  - Foundation panel → `content.education.heading`, `content.education.intro`
  - Section [04] Secondary Artifacts → `content.projects.artifacts_label`, `content.projects.artifacts_heading`, `content.projects.artifacts_intro`
  - Section [05] Direct Contact → `content.contact.section_label`, `content.contact.heading`
- **Deleted unused JSON keys**: removed `skills[]` from `data/content/about.json`; removed the stale `projects[]` array and the generic `heading`/`intro` from `data/content/projects.json` (replaced by section-specific keys); all remaining keys in every content file are now rendered.
- **Deleted unused content files**: removed `data/content/home.json` and `data/content/trading_systems.json` — none of their keys were loaded or rendered in any template.
- **`data/content/projects.json` restructured**: split the single `heading`/`intro` pair into two sets — `flagship_label`/`flagship_heading`/`flagship_intro` for section 01 and `artifacts_label`/`artifacts_heading`/`artifacts_intro` for section 04, since `projects.json` drives two distinct sections.
- **`data/content/contact.json`**, **`about.json`**, **`experience.json`**: each gained a `section_label` key containing the numbered label (e.g. `[02] Systems Architecture`) that was previously hardcoded in the template.

---



- **Template Fallback Literal Cleanup**: removed inline default string literals and conditional existence guards (`if site and site.identity else ...`, `else '...'`, etc.) in `app/templates/base.html` and `app/templates/public/home.html`. Template variables for `site` and `content` are now accessed directly, aligning with the "config over code" principle so that missing or misconfigured keys fail loudly.
- **Independent Page Title Configuration**: corrected the typo `"Mehboob Meghaniaaaaaaaaaaa"` to `"Mehboob Meghani"` in `data/config.json`. Removed the redundant `{% block title %}` override from `app/templates/public/home.html` so that the homepage title uses the `site.site.title` configuration value dynamically, separating browser tab title configuration from the displayed hero name (`site.identity.name`).
- **Codebase and Configuration Simplification**: purged all unused properties from `data/config.json` (such as `tagline`, `domain`, `canonical_url`, `expo_url`, `identity.summary`, `masthead`, `benchmark`, `nav`, and `themes`). Moved `role` to `identity.role` in `data/config.json` and updated references. Deleted dead script files `app/static/js/theme.js` and `app/static/js/hero.js` and removed their inclusions in templates.
- **Dynamic Copyright Year**: migrated the website's copyright year from a hardcoded config key (`site.site.year` in `data/config.json`) to a dynamically resolved datetime object (`now.year`) using Python's `datetime.now(timezone.utc)` injected globally via Flask's context processor.
- **Calibrated Benchmarks Layout**: refactored the calibrated benchmarks panel (.benchmarks-spec-grid) in app/static/css/home.css from a fixed 4-column CSS grid to a flexible, horizontally scrollable flexbox container. Utilizes responsive percentage-based flex sizes (`calc((100% - 24px) / 3)` on desktop, `calc((100% - 12px) / 2)` on tablet, and `100%` on mobile) to guarantee that benchmark cards retain a stable, constant width and overflow scroll instead of shrinking/squeezing when more items are added.

---

## 2026-08-20 — Implement GSAP scroll-triggered and numeric count-up animations with immediate hero loading

- **Immediate Hero Animation Loading**: updated the GSAP animation runner script in both `app/templates/base.html` and `app/templates/admin/base.html` to check if animated elements reside inside the hero masthead container (`#about`). If they do, their animations (fade/slide reveals, word-masks, and numeric count-ups) trigger immediately upon script execution/page load instead of waiting for scroll trigger entry, ensuring a complete and animated initial viewport above the fold.
- **GSAP Scroll Animations Setup**: integrated GSAP and ScrollTrigger libraries via CDN links in `app/templates/base.html` and `app/templates/admin/base.html`. Added scroll-reveal styles with progressive enhancement wrapping (`html.js-gsap [data-gsap-reveal] { opacity: 0; }`) to ensure contents only start hidden when JavaScript and GSAP are loaded and actively driving the page.
- **Scroll-Reveal Animations**: decorated section headers, card lists, timelines, and form panels in `app/templates/public/home.html` and `app/templates/admin/dashboard.html` with `data-gsap-reveal` triggers and `data-anim-text` word-masks for smooth transition reveals on scroll.
- **Numeric Count-up Engine**: integrated numeric count-up animations for key metrics using `data-count-to` parameters. Updated `data/config.json` with dedicated animation configurations for the system benchmarks (throughput, memory reduction, socket latency, cloud cost optimization) so that benchmark values dynamically count up when scrolled into view.

---

## 2026-08-20 — Convert direct channels toolbar to two-line layout and refine mobile navigation menu

- **Two-Line Masthead Toolbar**: split the direct contact/links toolbar inside `.masthead-channels` (under `app/templates/public/home.html`) into two distinct lines: Email and Phone contact info on Line 1, and GitHub, LinkedIn, and Download CV on Line 2. Modified CSS in `app/static/css/home.css` to preserve this two-line layout, keep it left-aligned on mobile devices, and optimize sizing. To prevent wrapping/overflow on mobile viewports, the long email address text is swapped to display "Email" on screens under 480px.
- **Navigation Menu Layout & Numbering Removal**: updated mobile navigation toggle button `.mobile-nav-toggle`, navigation menu dropdown `.site-nav.open`, and nav link elements `.site-nav a` to copy the styles exactly from the `itqan-trades` project. This includes inheriting the same elevated background, gold border highlights, flex space-between item alignments, card-based floating dropdown box with blur backdrop-filter, and responsive padding behavior. Completely removed the navigation links numbering (`.nav-num`) from both desktop and mobile modes to match the clean, unnumbered navigation menu of the `itqan-trades` site.

---

## 2026-08-20 — Remove color swatches from admin login page

- **Remove Color Swatches**: removed the color/theme swatches from the admin login page (`app/templates/admin/login.html`), including their CSS styles in `app/static/css/app.css` and their theme-handling JavaScript event listeners and UI update logic in `app/static/js/theme.js`.

---

## 2026-08-19 — Scroll-to-Top FAB, layout matching, typography unification, mobile header, and anchor redirect fixes

- **Scroll-to-Top FAB**: added a "jump to top" floating action button (FAB) with a scroll progress ring to `base.html` and styled it in `app.css`. It features a smooth-scrolling click handler, a circular SVG ring showing scroll percentage, and mobile responsiveness matching the `itqan-trades` implementation.
- **Container Width Matching**: updated `.container` styling in `app/static/css/app.css` to match `itqan-trades` exactly (`width: 90%`, `max-width: 1600px`).
- **Breakpoint Unification**: changed mobile nav toggle and site nav media query breakpoints from `768px` to `900px` in `app/static/css/app.css`, and did the same for contact layout and responsive paddings/grids in `app/static/css/home.css`. This prevents menu wrapping on medium screens and unifies layout responsiveness breakpoints with the Tabulator table wrapper.
- **Mobile Header Fix**: removed the redundant and empty `.header-controls` container element from `app/templates/base.html` and `app/templates/admin/base.html` and cleaned up its CSS rules in `app.css`. This allows the mobile hamburger menu toggle to correctly align to the right side of the screen using the flexbox `space-between` rule, matching the clean structure of the `itqan-trades` site.
- **Unified Typography**: aligned the font loading and font variables structure in `app/static/css/app.css` to match `itqan-trades` exactly. The site now loads and uses Google Fonts `Fauna One` (for body/mono/display elements) and `Cinzel` (for headings/serif text), replacing `Plus Jakarta Sans` and `JetBrains Mono`.
- **Anchor Redirect Fixes**: changed the navigation links in the header of `app/templates/base.html` from relative hashes (e.g. `#systems`) to absolute home paths (e.g. `{{ url_for('public.home') }}#systems`) so that they work correctly when clicked from other pages (such as the 404 page).
- **Scroll Padding Offset**: added `scroll-padding-top: 80px;` to the `html` element in `app/static/css/app.css` to prevent the sticky header from overlapping and obscuring the headings of targeted sections when scrolling to page anchors.
- **Mobile Grid Layout Overflow Fixes**: updated `.decisions-grid`, `.arch-dossier-grid`, `.foundation-grid`, and `.artifacts-grid` in `app/static/css/home.css` to use `minmax(min(100%, X), 1fr)` patterns. This prevents horizontal scrolling and layout overflow on mobile screens where the container width is smaller than the grid columns' minimum width. Also decreased padding of `.arch-dossier-card` under the 900px breakpoint to allow more breathing room for text-rich sections.
- **Justify Align Content Globally**: added `text-align: justify;` to the global `p` rule in `app/static/css/app.css` to make all body/description text elements on the site justify-aligned. Removed the card-specific alignment from `home.css` to rely on the global style.

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
