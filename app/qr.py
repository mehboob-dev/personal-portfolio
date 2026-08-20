"""Dynamic QR redirect engine.

GET /r/<slug>  →  record a scan  →  302 to the QR code's current destination.

The destination is mutable in the admin, so a printed QR never goes stale.
"""

from flask import Blueprint, Response, abort, redirect, render_template, request

from .extensions import db
from .helpers import anonymize_ip, parse_user_agent
from .models import QrCode, Scan

bp = Blueprint("qr", __name__)


@bp.get("/r/<slug>")
def redirect_slug(slug: str):
    code = QrCode.query.filter_by(slug=slug, is_deleted=False).first()
    if code is None:
        abort(404)

    if code.is_active:
        _record_scan(code)

    dest = (code.destination_url or "").strip()

    # If landing page features (lead capture form or direct call button) are enabled AND dest is not direct vcard, render interactive landing page
    if (code.show_lead_form or code.show_call_button) and not dest.startswith(("vcard-direct:", "vcard_direct:", "direct-vcard:")):
        vcard_text = None
        text_body = None
        content_type = "landing"

        if dest.startswith("vcard:") or dest.startswith("BEGIN:VCARD"):
            vcard_text = dest[6:].strip() if dest.startswith("vcard:") else dest
            content_type = "vcard"
        elif dest.startswith("text:"):
            text_body = dest[5:].strip()
            content_type = "text"

        return render_template(
            "public/qr_content.html",
            content_type=content_type,
            label=code.label,
            text_content=vcard_text or text_body,
            dest_url=dest,
            qr_code=code,
            title=code.label or "QR Destination",
            sent=request.args.get("sent"),
            error=request.args.get("error"),
        )

    # Direct 1-Tap vCard Download / Import (e.g. vcard-direct: or vcard_direct:)
    if dest.startswith(("vcard-direct:", "vcard_direct:", "direct-vcard:")):
        vcard_text = dest.split(":", 1)[1].strip()
        filename = f"{slugify_filename(code.label or code.slug)}.vcf"
        return Response(
            vcard_text,
            mimetype="text/vcard",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Type": "text/vcard; charset=utf-8",
            },
        )

    # vCard payload rendering (Web Page with Web Share API + Download)
    if dest.startswith("vcard:") or dest.startswith("BEGIN:VCARD"):
        vcard_text = dest[6:].strip() if dest.startswith("vcard:") else dest
        return render_template(
            "public/qr_content.html",
            content_type="vcard",
            label=code.label,
            text_content=vcard_text,
            dest_url=dest,
            qr_code=code,
            title=code.label or "Contact Card",
        )
    elif dest.startswith("text:"):
        text_body = dest[5:].strip()
        return render_template(
            "public/qr_content.html",
            content_type="text",
            label=code.label,
            text_content=text_body,
            dest_url=dest,
            qr_code=code,
            title=code.label or "Shared Note",
        )

    # 302 (temporary) so search engines don't cache the redirect target.
    return redirect(dest, code=302)


def slugify_filename(name: str) -> str:
    """Helper to convert string into safe filename."""
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.strip())
    return safe.strip("_") or "contact"


def _record_scan(code: QrCode) -> None:
    """Best-effort scan capture. Never raises — a broken scan shouldn't 500."""
    try:
        raw_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if request.headers.get("X-Forwarded-For")
            else (request.headers.get("CF-Connecting-IP") or request.remote_addr or "")
        )
        ua = parse_user_agent(request.headers.get("User-Agent", ""))

        # Geolocation headers (Cloudflare, Vercel, AWS CloudFront, Nginx)
        country = (
            request.headers.get("CF-IPCountry")
            or request.headers.get("X-Vercel-IP-Country")
            or request.headers.get("X-Country-Code")
            or None
        )
        city = (
            request.headers.get("CF-IPCity")
            or request.headers.get("X-Vercel-IP-City")
            or request.headers.get("X-City-Name")
            or None
        )

        # Mark local test IP explicitly
        if not country and raw_ip in ("127.0.0.1", "::1", "localhost"):
            country = "Local Dev"
            city = "Localhost"

        lang = request.headers.get("Accept-Language", "").split(",")[0].strip()[:30] or None

        # UTM parameters (fallback to assigned campaign name if not in URL)
        utm_source = (request.args.get("utm_source") or "")[:80] or None
        utm_medium = (request.args.get("utm_medium") or "")[:80] or None
        utm_campaign = (
            (request.args.get("utm_campaign") or "")[:80]
            or (code.campaign.name if code.campaign else None)
        )

        scan = Scan(
            qr_code_id=code.id,
            ip_hash=anonymize_ip(raw_ip),
            device=ua["device"],
            device_model=ua.get("device_model"),
            browser=ua["browser"],
            os=ua["os"],
            app_source=ua.get("app_source", "Direct / Browser"),
            language=lang,
            country=country,
            city=city,
            referrer=(request.referrer or "")[:500] or None,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
        db.session.add(scan)
        db.session.commit()
    except Exception:
        db.session.rollback()
