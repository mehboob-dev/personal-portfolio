# mehboob-portfolio — Changelog

All notable changes, newest first. Format: `YYYY-MM-DD — summary (commit)`.

## 2026-08-20 — WhatsApp, Telegram Destination Support & Dynamic QR Landing Page Feature Overlays

- **WhatsApp & Telegram Destinations**: Added dedicated `whatsapp` (`https://wa.me/...`) and `telegram` (`https://t.me/...`) options to the admin QR destination builder dropdown (`app/templates/admin/qr_edit.html`) and payload validator (`_valid_destination_url` in `app/admin.py`).
- **Optional QR Landing Page Overlays**:
  - **Lead Capture / Contact Exchange Form (Approach 1)**: Added `show_lead_form` database toggle on `QrCode` model allowing visitors scanning any QR code destination (URL, WhatsApp, Telegram, etc.) to optionally leave their contact details.
  - **Direct Call / Call Me Button (Approach 2)**: Added `show_call_button` & `call_phone_number` database toggles on `QrCode` model allowing admins to display an instant green "Call Me Direct" button on the QR destination landing page (`app/templates/public/qr_content.html`).
- **Database Schema Migration**: Added Alembic migration script (`b33147b1af14_add_qr_landing_toggles.py`) adding `show_lead_form`, `show_call_button`, and `call_phone_number` columns to `qr_codes`.

---

## 2026-08-20 — 1-Tap Direct vCard Download & Native Web Share Contact Import

- **Native Web Share API Contact Import**: Updated `app/templates/public/qr_content.html` to add a primary **"📲 Add to Contacts (Native Import)"** button using `navigator.share({ files: [vcardFile] })`. On modern mobile devices (iOS / Android), clicking this opens the native phone contacts sheet directly.
- **Direct 1-Tap vCard Download Mode**: Added `vcard-direct:` destination type option in `app/templates/admin/qr_edit.html` and routing in `app/qr.py`. When configured with `vcard-direct:`, scanning the QR code bypasses the webpage and directly returns a `text/vcard` HTTP stream, triggering instant contact import dialogs on Android/iOS.
- **Table JSON Escape Fix**: Updated `app/templates/admin/qr_list.html` to serialize string parameters using Jinja2 `tojson` to prevent multi-line JS syntax errors when displaying vCard payloads.

---

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
