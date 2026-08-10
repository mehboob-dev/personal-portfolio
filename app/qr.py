"""Dynamic QR redirect engine.

GET /r/<slug>  →  record a scan  →  302 to the QR code's current destination.

The destination is mutable in the admin, so a printed QR never goes stale.
"""

from flask import Blueprint, abort, redirect, request

from .extensions import db
from .helpers import anonymize_ip, parse_user_agent
from .models import QrCode, Scan

bp = Blueprint("qr", __name__)


@bp.get("/r/<slug>")
def redirect_slug(slug: str):
    code = db.session.get(QrCode, slug) or QrCode.query.filter_by(slug=slug).first()
    if code is None:
        abort(404)

    if code.is_active:
        _record_scan(code)

    # 302 (temporary) so search engines don't cache the redirect target.
    return redirect(code.destination_url, code=302)


def _record_scan(code: QrCode) -> None:
    """Best-effort scan capture. Never raises — a broken scan shouldn't 500."""
    try:
        ua = parse_user_agent(request.headers.get("User-Agent", ""))
        scan = Scan(
            qr_code_id=code.id,
            ip_hash=anonymize_ip(request.headers.get("X-Forwarded-For", "").split(",")[0].strip() if request.headers.get("X-Forwarded-For") else request.remote_addr),
            device=ua["device"],
            browser=ua["browser"],
            os=ua["os"],
            referrer=(request.referrer or "")[:500] or None,
            # country/city intentionally empty: geo lookup is optional/off by default.
            # Wire a geo service here later if needed (see DOCS/qr-manager.md).
        )
        db.session.add(scan)
        db.session.commit()
    except Exception:
        db.session.rollback()
