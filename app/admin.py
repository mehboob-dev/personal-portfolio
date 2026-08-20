"""Admin blueprint: QR manager + scan analytics + leads (portfolio).

Protected by flask-login. Routes:
  /admin                        dashboard (totals, unique, device/city, recent scans)
  /admin/login                  POST login
  /admin/logout
  /admin/campaigns              list + create (supports show=active|deleted|all)
  /admin/campaigns/<id>/delete  soft delete (move to trash)
  /admin/campaigns/<id>/restore recover from trash
  /admin/campaigns/<id>/purge   permanent delete
  /admin/qr                     list (supports show=active|deleted|all)
  /admin/qr/new                 create
  /admin/qr/<id>                edit (label, destination, active, campaign)
  /admin/qr/<id>/delete         soft delete (move to trash)
  /admin/qr/<id>/restore        recover from trash
  /admin/qr/<id>/purge          permanent delete
  /admin/qr/<id>/png            download QR image / inline preview
  /admin/leads                  list + CSV export (supports show=active|deleted|all)
  /admin/leads/<id>             detail view
  /admin/leads/<id>/delete      soft delete (move to trash)
  /admin/leads/<id>/restore     recover from trash
  /admin/leads/<id>/purge       permanent delete
"""

import io
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import qrcode
from flask import (
    Blueprint,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .helpers import slugify
from .models import AdminUser, Campaign, Lead, QrCode, Scan

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _valid_destination_url(url: str) -> bool:
    """Validate destination payload.

    Allows absolute web URLs (http/https), custom URIs (tel:, mailto:, sms:, geo:, whatsapp:, wa.me, tg:, t.me),
    vCard contact structures (BEGIN:VCARD or vcard:), or plain text notes (text:).
    Rejects malformed javascript: links or bare paths to prevent open-redirect vectors.
    """
    if not url:
        return False
    u = url.strip()
    if u.startswith((
        "vcard:", "vcard-direct:", "vcard_direct:", "direct-vcard:", "BEGIN:VCARD",
        "text:", "tel:", "mailto:", "sms:", "geo:", "whatsapp:", "wa.me:", "tg:", "t.me:"
    )):
        return True
    try:
        parts = urlparse(u)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.netloc)


# --- auth ------------------------------------------------------------------

@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        else:
            error = "Invalid username or password. Please verify your credentials."

    return render_template("admin/login.html", error=error, username=username)


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


# --- dashboard -------------------------------------------------------------

@bp.get("/")
@login_required
def dashboard():
    scans_q = Scan.query.filter_by(is_deleted=False)
    total_scans = scans_q.count()
    unique_visitors = scans_q.with_entities(Scan.ip_hash).distinct().count()

    device_breakdown = _column_counts(Scan.device)
    os_breakdown = _column_counts(Scan.os)
    recent_scans = scans_q.order_by(Scan.created_at.desc()).limit(15).all()

    top_cities = (
        db.session.query(Scan.city, db.func.count(Scan.id))
        .filter(Scan.city.isnot(None), Scan.is_deleted == False)
        .group_by(Scan.city)
        .order_by(db.func.count(Scan.id).desc())
        .limit(8)
        .all()
    )

    # last 14 days, per-day scan counts
    since = datetime.now(timezone.utc) - timedelta(days=14)
    daily = (
        db.session.query(db.func.date(Scan.created_at), db.func.count(Scan.id))
        .filter(Scan.created_at >= since, Scan.is_deleted == False)
        .group_by(db.func.date(Scan.created_at))
        .order_by(db.func.date(Scan.created_at))
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_scans=total_scans,
        unique_visitors=unique_visitors,
        device_breakdown=device_breakdown,
        os_breakdown=os_breakdown,
        recent_scans=recent_scans,
        top_cities=top_cities,
        daily=daily,
        leads_count=Lead.query.filter_by(is_deleted=False).count(),
        qr_count=QrCode.query.filter_by(is_deleted=False).count(),
        campaigns_count=Campaign.query.filter_by(is_deleted=False).count(),
    )


def _column_counts(column):
    rows = (
        db.session.query(column, db.func.count(column))
        .filter(Scan.is_deleted == False)
        .group_by(column)
        .order_by(db.func.count(column).desc())
        .all()
    )
    return [(label or "Unknown", count) for label, count in rows]


# --- campaigns -------------------------------------------------------------

@bp.route("/campaigns", methods=["GET", "POST"])
@login_required
def campaigns():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip() or slugify(name)
        if name and slug:
            existing = Campaign.query.filter_by(slug=slug).first()
            if existing and existing.is_deleted:
                existing.name = name
                existing.is_deleted = False
                db.session.commit()
            elif existing and not existing.is_deleted:
                error = f"A campaign with the slug '{slug}' already exists."
            else:
                existing_name = Campaign.query.filter_by(name=name).first()
                if existing_name:
                    error = f"A campaign with the name '{name}' already exists."
                else:
                    db.session.add(Campaign(name=name, slug=slug))
                    db.session.commit()

    show = request.args.get("show", "active")  # 'active', 'deleted', 'all'
    q = Campaign.query
    if show == "deleted":
        q = q.filter_by(is_deleted=True)
    elif show == "all":
        pass
    else:  # default active
        q = q.filter_by(is_deleted=False)

    all_campaigns = q.order_by(Campaign.created_at.desc()).all()
    active_count = Campaign.query.filter_by(is_deleted=False).count()
    deleted_count = Campaign.query.filter_by(is_deleted=True).count()
    all_count = Campaign.query.count()

    return render_template(
        "admin/campaigns.html",
        campaigns=all_campaigns,
        show=show,
        active_count=active_count,
        deleted_count=deleted_count,
        all_count=all_count,
        error=error,
    )


@bp.post("/campaigns/<int:cid>/delete")
@login_required
def delete_campaign(cid: int):
    camp = db.session.get(Campaign, cid)
    if camp:
        camp.is_deleted = True
        db.session.commit()
    return redirect(request.referrer or url_for("admin.campaigns"))


@bp.post("/campaigns/<int:cid>/restore")
@login_required
def restore_campaign(cid: int):
    camp = db.session.get(Campaign, cid)
    if camp:
        camp.is_deleted = False
        db.session.commit()
    return redirect(request.referrer or url_for("admin.campaigns"))


@bp.post("/campaigns/<int:cid>/purge")
@login_required
def purge_campaign(cid: int):
    camp = db.session.get(Campaign, cid)
    if camp:
        for q in camp.qr_codes:
            q.campaign_id = None
        db.session.delete(camp)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.campaigns"))


@bp.post("/campaigns/bulk")
@login_required
def campaigns_bulk():
    action = request.form.get("action")  # 'trash', 'restore', 'purge'
    raw_ids = request.form.getlist("ids")
    ids = [int(i) for i in raw_ids if str(i).isdigit()]
    if ids:
        camps = Campaign.query.filter(Campaign.id.in_(ids)).all()
        for c in camps:
            if action == "trash":
                c.is_deleted = True
            elif action == "restore":
                c.is_deleted = False
            elif action == "purge":
                for q in c.qr_codes:
                    q.campaign_id = None
                db.session.delete(c)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.campaigns"))


# --- QR codes --------------------------------------------------------------

@bp.route("/qr", methods=["GET"])
@login_required
def qr_list():
    show = request.args.get("show", "active")  # 'active', 'deleted', 'all'
    q = QrCode.query
    if show == "deleted":
        q = q.filter_by(is_deleted=True)
    elif show == "all":
        pass
    else:  # default active
        q = q.filter_by(is_deleted=False)

    codes = q.order_by(QrCode.created_at.desc()).all()
    active_count = QrCode.query.filter_by(is_deleted=False).count()
    deleted_count = QrCode.query.filter_by(is_deleted=True).count()
    all_count = QrCode.query.count()
    campaigns = Campaign.query.filter_by(is_deleted=False).order_by(Campaign.name).all()

    return render_template(
        "admin/qr_list.html",
        codes=codes,
        campaigns=campaigns,
        show=show,
        active_count=active_count,
        deleted_count=deleted_count,
        all_count=all_count,
    )


@bp.route("/qr/new", methods=["GET", "POST"])
@login_required
def qr_new():
    campaigns = Campaign.query.filter_by(is_deleted=False).order_by(Campaign.name).all()
    if request.method == "POST":
        slug = slugify(request.form.get("slug", ""))
        label = request.form.get("label", "").strip()
        destination = request.form.get("destination_url", "").strip()
        campaign_id = request.form.get("campaign_id") or None
        show_lead_form = request.form.get("show_lead_form") == "on"
        show_call_button = request.form.get("show_call_button") == "on"
        call_phone_number = request.form.get("call_phone_number", "").strip() or None

        if slug and destination:
            if not _valid_destination_url(destination):
                return render_template(
                    "admin/qr_edit.html",
                    code=None,
                    campaigns=campaigns,
                    error="Invalid destination format. Destination URL must be an absolute http(s) link (e.g. https://example.com) or custom payload (tel:, mailto:, sms:, vcard:, text:, whatsapp:, telegram:).",
                    form=request.form,
                )
            existing = QrCode.query.filter_by(slug=slug).first()
            if existing and existing.is_deleted:
                # restore and update
                existing.label = label
                existing.destination_url = destination
                existing.campaign_id = int(campaign_id) if campaign_id else None
                existing.show_lead_form = show_lead_form
                existing.show_call_button = show_call_button
                existing.call_phone_number = call_phone_number
                existing.is_active = request.form.get("is_active") == "on"
                existing.is_deleted = False
                db.session.commit()
                return redirect(url_for("admin.qr_list"))
            elif existing and not existing.is_deleted:
                return render_template(
                    "admin/qr_edit.html",
                    code=None,
                    campaigns=campaigns,
                    error=f"A QR code with slug '{slug}' already exists.",
                    form=request.form,
                )
            elif not existing:
                code = QrCode(
                    slug=slug,
                    label=label,
                    destination_url=destination,
                    campaign_id=int(campaign_id) if campaign_id else None,
                    show_lead_form=show_lead_form,
                    show_call_button=show_call_button,
                    call_phone_number=call_phone_number,
                    is_active=request.form.get("is_active") == "on",
                    is_deleted=False,
                )
                db.session.add(code)
                db.session.commit()
                return redirect(url_for("admin.qr_list"))
    return render_template("admin/qr_edit.html", code=None, campaigns=campaigns)


@bp.route("/qr/<int:qid>", methods=["GET", "POST"])
@login_required
def qr_edit(qid: int):
    code = db.session.get(QrCode, qid) or abort(404)
    campaigns = Campaign.query.filter_by(is_deleted=False).order_by(Campaign.name).all()
    if request.method == "POST":
        # Keep original slug for existing QRs to prevent breaking printed physical QR codes
        destination = request.form.get("destination_url", "").strip()
        if not _valid_destination_url(destination):
            return render_template(
                "admin/qr_edit.html",
                code=code,
                campaigns=campaigns,
                error="Invalid destination format. Destination URL must be an absolute http(s) link (e.g. https://example.com) or custom payload (tel:, mailto:, sms:, vcard:, text:, whatsapp:, telegram:).",
                form=request.form,
            )
        code.label = request.form.get("label", "").strip()
        code.destination_url = destination
        campaign_id = request.form.get("campaign_id") or None
        code.campaign_id = int(campaign_id) if campaign_id else None
        code.show_lead_form = request.form.get("show_lead_form") == "on"
        code.show_call_button = request.form.get("show_call_button") == "on"
        code.call_phone_number = request.form.get("call_phone_number", "").strip() or None
        code.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        return redirect(url_for("admin.qr_list"))
    return render_template("admin/qr_edit.html", code=code, campaigns=campaigns)


@bp.get("/qr/<int:qid>/stats")
@login_required
def qr_stats(qid: int):
    code = db.session.get(QrCode, qid) or abort(404)
    show = request.args.get("show", "active")  # 'active', 'deleted', 'all'

    active_scans_q = Scan.query.filter_by(qr_code_id=code.id, is_deleted=False)
    deleted_scans_q = Scan.query.filter_by(qr_code_id=code.id, is_deleted=True)
    all_scans_q = Scan.query.filter_by(qr_code_id=code.id)

    total_scans = active_scans_q.count()
    unique_visitors = active_scans_q.with_entities(Scan.ip_hash).distinct().count()
    active_count = total_scans
    deleted_count = deleted_scans_q.count()
    all_count = all_scans_q.count()

    device_rows = (
        db.session.query(Scan.device, db.func.count(Scan.id))
        .filter(Scan.qr_code_id == code.id, Scan.is_deleted == False)
        .group_by(Scan.device)
        .order_by(db.func.count(Scan.id).desc())
        .all()
    )
    device_breakdown = [(label or "Unknown", count) for label, count in device_rows]

    os_rows = (
        db.session.query(Scan.os, db.func.count(Scan.id))
        .filter(Scan.qr_code_id == code.id, Scan.is_deleted == False)
        .group_by(Scan.os)
        .order_by(db.func.count(Scan.id).desc())
        .all()
    )
    os_breakdown = [(label or "Unknown", count) for label, count in os_rows]

    browser_rows = (
        db.session.query(Scan.browser, db.func.count(Scan.id))
        .filter(Scan.qr_code_id == code.id, Scan.is_deleted == False)
        .group_by(Scan.browser)
        .order_by(db.func.count(Scan.id).desc())
        .all()
    )
    browser_breakdown = [(label or "Unknown", count) for label, count in browser_rows]

    app_rows = (
        db.session.query(Scan.app_source, db.func.count(Scan.id))
        .filter(Scan.qr_code_id == code.id, Scan.is_deleted == False)
        .group_by(Scan.app_source)
        .order_by(db.func.count(Scan.id).desc())
        .all()
    )
    app_breakdown = [(label or "Direct / Browser", count) for label, count in app_rows]

    since = datetime.now(timezone.utc) - timedelta(days=14)
    daily = (
        db.session.query(db.func.date(Scan.created_at), db.func.count(Scan.id))
        .filter(Scan.qr_code_id == code.id, Scan.is_deleted == False, Scan.created_at >= since)
        .group_by(db.func.date(Scan.created_at))
        .order_by(db.func.date(Scan.created_at).desc())
        .all()
    )

    if show == "deleted":
        scans_to_show = deleted_scans_q.order_by(Scan.created_at.desc()).all()
    elif show == "all":
        scans_to_show = all_scans_q.order_by(Scan.created_at.desc()).all()
    else:
        scans_to_show = active_scans_q.order_by(Scan.created_at.desc()).all()

    return render_template(
        "admin/qr_stats.html",
        code=code,
        show=show,
        total_scans=total_scans,
        unique_visitors=unique_visitors,
        active_count=active_count,
        deleted_count=deleted_count,
        all_count=all_count,
        device_breakdown=device_breakdown,
        os_breakdown=os_breakdown,
        browser_breakdown=browser_breakdown,
        app_breakdown=app_breakdown,
        daily=daily,
        scans=scans_to_show,
    )


@bp.post("/scans/<int:sid>/delete")
@login_required
def scan_delete(sid: int):
    scan = db.session.get(Scan, sid)
    if scan:
        scan.is_deleted = True
        db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.post("/scans/<int:sid>/restore")
@login_required
def scan_restore(sid: int):
    scan = db.session.get(Scan, sid)
    if scan:
        scan.is_deleted = False
        db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.post("/scans/<int:sid>/purge")
@login_required
def scan_purge(sid: int):
    scan = db.session.get(Scan, sid)
    if scan:
        db.session.delete(scan)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.post("/scans/bulk")
@login_required
def scans_bulk():
    action = request.form.get("action")  # 'trash', 'restore', 'purge'
    raw_ids = request.form.getlist("ids")
    ids = [int(i) for i in raw_ids if str(i).isdigit()]
    if ids:
        scans_items = Scan.query.filter(Scan.id.in_(ids)).all()
        for s in scans_items:
            if action == "trash":
                s.is_deleted = True
            elif action == "restore":
                s.is_deleted = False
            elif action == "purge":
                db.session.delete(s)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.get("/qr/<int:qid>/export-scans.csv")
@login_required
def qr_scans_csv(qid: int):
    import csv

    code = db.session.get(QrCode, qid) or abort(404)
    show = request.args.get("show", "active")
    q = Scan.query.filter_by(qr_code_id=code.id)
    if show == "deleted":
        q = q.filter_by(is_deleted=True)
    elif show == "all":
        pass
    else:
        q = q.filter_by(is_deleted=False)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "scan_id", "date_utc", "time_utc", "qr_slug", "device", "device_model",
        "browser", "os", "app_source", "language", "country", "city",
        "referrer", "utm_source", "utm_medium", "utm_campaign", "is_deleted", "ip_hash"
    ])
    for s in q.order_by(Scan.created_at.desc()).all():
        writer.writerow([
            s.id,
            s.created_at.strftime('%Y-%m-%d') if s.created_at else "",
            s.created_at.strftime('%H:%M:%S') if s.created_at else "",
            code.slug,
            s.device or "",
            s.device_model or "",
            s.browser or "",
            s.os or "",
            s.app_source or "Direct / Browser",
            s.language or "",
            s.country or "",
            s.city or "",
            s.referrer or "",
            s.utm_source or "",
            s.utm_medium or "",
            s.utm_campaign or "",
            "deleted" if s.is_deleted else "active",
            s.ip_hash or "",
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scans-{code.slug}.csv"},
    )


@bp.post("/qr/<int:qid>/delete")
@login_required
def qr_delete(qid: int):
    code = db.session.get(QrCode, qid)
    if code:
        code.is_deleted = True
        db.session.commit()
    return redirect(request.referrer or url_for("admin.qr_list"))


@bp.post("/qr/<int:qid>/restore")
@login_required
def qr_restore(qid: int):
    code = db.session.get(QrCode, qid)
    if code:
        code.is_deleted = False
        db.session.commit()
    return redirect(request.referrer or url_for("admin.qr_list"))


@bp.post("/qr/<int:qid>/purge")
@login_required
def qr_purge(qid: int):
    code = db.session.get(QrCode, qid)
    if code:
        # Delete associated scans first
        Scan.query.filter_by(qr_code_id=code.id).delete()
        db.session.delete(code)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.qr_list"))


@bp.post("/qr/bulk")
@login_required
def qr_bulk():
    action = request.form.get("action")  # 'trash', 'restore', 'purge'
    raw_ids = request.form.getlist("ids")
    ids = [int(i) for i in raw_ids if str(i).isdigit()]
    if ids:
        codes = QrCode.query.filter(QrCode.id.in_(ids)).all()
        for q in codes:
            if action == "trash":
                q.is_deleted = True
            elif action == "restore":
                q.is_deleted = False
            elif action == "purge":
                Scan.query.filter_by(qr_code_id=q.id).delete()
                db.session.delete(q)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.qr_list"))


@bp.get("/qr/<int:qid>/png")
@login_required
def qr_png(qid: int):
    """Render a PNG of the QR for the code's redirect URL."""
    code = db.session.get(QrCode, qid) or abort(404)
    # The QR encodes the redirect URL on our domain (/r/<slug>)
    redirect_url = url_for("qr.redirect_slug", slug=code.slug, _external=True)
    img = qrcode.make(redirect_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_data = buf.getvalue()
    as_attachment = request.args.get("download") == "1"
    response = Response(png_data, mimetype="image/png")
    if as_attachment:
        response.headers["Content-Disposition"] = f'attachment; filename="qr-{code.slug}.png"'
    return response


# --- leads -----------------------------------------------------------------

@bp.get("/leads")
@login_required
def leads():
    show = request.args.get("show", "active")  # 'active', 'deleted', 'all'
    q = Lead.query
    if show == "deleted":
        q = q.filter_by(is_deleted=True)
    elif show == "all":
        pass
    else:  # default 'active'
        q = q.filter_by(is_deleted=False)

    all_leads = q.order_by(Lead.created_at.desc()).all()
    active_count = Lead.query.filter_by(is_deleted=False).count()
    deleted_count = Lead.query.filter_by(is_deleted=True).count()
    all_count = Lead.query.count()

    return render_template(
        "admin/leads.html",
        leads=all_leads,
        show=show,
        active_count=active_count,
        deleted_count=deleted_count,
        all_count=all_count,
    )


@bp.get("/leads/<int:lid>")
@login_required
def lead_detail(lid: int):
    lead = db.session.get(Lead, lid) or abort(404)
    return render_template("admin/lead_detail.html", lead=lead)


@bp.post("/leads/<int:lid>/delete")
@login_required
def lead_delete(lid: int):
    lead = db.session.get(Lead, lid) or abort(404)
    lead.is_deleted = True
    db.session.commit()
    return redirect(request.referrer or url_for("admin.leads"))


@bp.post("/leads/<int:lid>/restore")
@login_required
def lead_restore(lid: int):
    lead = db.session.get(Lead, lid) or abort(404)
    lead.is_deleted = False
    db.session.commit()
    return redirect(request.referrer or url_for("admin.leads"))


@bp.post("/leads/<int:lid>/purge")
@login_required
def lead_purge(lid: int):
    lead = db.session.get(Lead, lid) or abort(404)
    db.session.delete(lead)
    db.session.commit()
    return redirect(url_for("admin.leads", show="deleted"))


@bp.post("/leads/bulk")
@login_required
def leads_bulk():
    action = request.form.get("action")  # 'trash', 'restore', 'purge'
    raw_ids = request.form.getlist("ids")
    ids = [int(i) for i in raw_ids if str(i).isdigit()]
    if ids:
        leads_items = Lead.query.filter(Lead.id.in_(ids)).all()
        for lead in leads_items:
            if action == "trash":
                lead.is_deleted = True
            elif action == "restore":
                lead.is_deleted = False
            elif action == "purge":
                db.session.delete(lead)
        db.session.commit()
    return redirect(request.referrer or url_for("admin.leads"))


@bp.get("/leads/export.csv")
@login_required
def leads_csv():
    import csv

    show = request.args.get("show", "active")
    q = Lead.query
    if show == "deleted":
        q = q.filter_by(is_deleted=True)
    elif show == "all":
        pass
    else:
        q = q.filter_by(is_deleted=False)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "email", "interest", "message", "is_deleted", "created_at"])
    for lead in q.order_by(Lead.created_at.desc()).all():
        writer.writerow(
            [
                lead.id,
                lead.name,
                lead.email,
                lead.interest or "",
                lead.message or "",
                "deleted" if lead.is_deleted else "active",
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
