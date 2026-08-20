# mehboob-portfolio — Changelog

All notable changes, newest first. Format: `YYYY-MM-DD — summary (commit)`.

## 2026-08-20 — Dynamic destination type dropdown & interactive payload builder in admin QR form

- **Destination Type Selector & Guided Panels**: Added a destination type `<select>` dropdown to `app/templates/admin/qr_edit.html` supporting:
  - 🌐 **Web URL** (302 Redirect)
  - 🎴 **Digital Contact Card (vCard)** (Full form with Full Name, Organization, Job Title, Tel, Email, Website, Notes)
  - 📝 **Shared Note / Text** (Multi-line note content)
  - 📞 **Phone Call** (`tel:` destination)
  - ✉️ **Send Email** (`mailto:` with recipient, pre-filled subject, and body draft)
  - 💬 **Send SMS** (`sms:` with recipient and preset text message)
  - ⚙️ **Custom / Raw Payload** (Direct URI entry)
- **Live Payload Compiler & Field Auto-Parsing**: Added vanilla JavaScript to `qr_edit.html` that automatically parses existing payload strings into their respective form fields on edit, dynamically shows/hides supported field panels, compiles inputs into canonical RFC payload formats (e.g. `vcard:BEGIN:VCARD...`, `mailto:user@domain.com?subject=...`, `sms:+123...?body=...`), and provides a raw payload toggle.

---

## 2026-08-20 — Lock QR slug on edit & support URLs, vCards, text notes, tel/mailto/sms

- **Permanent Printed QR Protection**: In `app/templates/admin/qr_edit.html` and `app/admin.py`, locked the `slug` field (`readonly`) when editing existing QR codes. This prevents editing a QR code's redirect path (`/r/<slug>`), ensuring physical printed QR cards never become invalid when updating destination targets.
- **Flexible Destination Payload Support**: Expanded payload validation and routing in `app/admin.py` and `app/qr.py`:
  - **Web URLs**: `https://google.com`, `https://yahoo.com` (302 Redirect)
  - **Phone / Mail / SMS / Geo**: `tel:+1234567890`, `mailto:user@domain.com`, `sms:+1234...` (302 Redirect to device apps)
  - **Digital Contact Card (vCard)**: `vcard:BEGIN:VCARD...` or `BEGIN:VCARD...` (renders mobile contact card with `.vcf` download button)
  - **Shared Note / Text**: `text:Welcome to booth #402!` (renders clean text note card)
- **New Template (`app/templates/public/qr_content.html`)**: Added responsive public template for rendering dynamic vCard downloads and plain text notes.

---

## 2026-08-20 — Replace Flask `send_file(BytesIO)` with `Response(bytes)` in `qr_png`

- **Fix `qr_png` 500 error under WSGI/Passenger**: Replaced `flask.send_file(buf, ...)` in `app/admin.py` with direct `Response(buf.getvalue(), mimetype="image/png")`. Under LiteSpeed / Passenger WSGI environment, `send_file` calls `.fileno()` on the byte buffer which raises `io.UnsupportedOperation: fileno` and returns a 500 Internal Error. Direct `Response` streams the byte content reliably without invoking file descriptor operations.

---

## 2026-08-20 — Fix JavaScript quote syntax error in campaigns admin table

- **Fix JS Syntax Error in Campaigns Table**: Escaped quotes (`\'`) in inline `onsubmit="return confirm(...)"` strings inside `app/templates/admin/campaigns.html`. Unescaped single quotes inside JS single-quoted string literals were causing a JavaScript syntax error that prevented the Tabulator table from initializing and rendering.

---

## 2026-08-20 — Handle duplicate campaign names & slugs gracefully

- **Campaign Duplicate Validation**: Updated `app/admin.py` to check for existing campaign names and active slugs prior to creating a new campaign. Prevents database `IntegrityError` (1062 duplicate key) and returns a user-friendly error banner on `app/templates/admin/campaigns.html` instead of throwing an unhandled 500 Internal Server Error.

---

## 2026-08-20 — CloudLinux Python Selector UI registration & SQLAlchemy pool recovery

- **CloudLinux Python Selector Registration**: Resolved issue where `mehboob-portfolio` was missing from the cPanel **Setup Python App** web UI (`python-selector.html.tt`). Updated `/home/itqantra/.cl.selector/python-selector.json` with the exact application schema for `mehboob-portfolio` matching Python 3.11, domain `mehboob.itqantrades.com`, and startup file `passenger_wsgi.py`. Confirmed listing via `cloudlinux-selector get` CLI.
- **MySQL Idle Disconnect Recovery**: Added `pool_pre_ping=True` and `pool_recycle=280` to `SQLALCHEMY_ENGINE_OPTIONS` in `app/__init__.py` to handle dropped MySQL idle connections and eliminate `500 Internal Server Error` on `/admin/login`.
- **Deployment Script Sync**: Updated `.cpanel.yml` to include `git fetch origin master` and `git reset --hard origin/master` prior to touching `tmp/restart.txt` to ensure cPanel's "Deploy HEAD Commit" button pulls the latest code from GitHub.
