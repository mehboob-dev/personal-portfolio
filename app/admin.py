"""Admin blueprint: QR manager + scan analytics + leads (portfolio).

Protected by flask-login. Routes:
  /admin              dashboard (totals, unique, device/city, recent scans)
  /admin/login        POST login
  /admin/logout
  /admin/campaigns    list + create
  /admin/campaigns/<id>/delete
  /admin/qr           list
  /admin/qr/new       create
  /admin/qr/<id>      edit (label, destination, active, campaign)
  /admin/qr/<id>/delete
  /admin/qr/<id>/png  download QR image
  /admin/leads        list + CSV export
"""

import io
from datetime import datetime, timedelta, timezone

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


# --- auth ------------------------------------------------------------------

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
    return render_template("admin/login.html")


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


# --- dashboard -------------------------------------------------------------

@bp.get("/")
@login_required
def dashboard():
    scans_q = Scan.query
    total_scans = scans_q.count()
    unique_visitors = scans_q.with_entities(Scan.ip_hash).distinct().count()

    device_breakdown = _column_counts(Scan.device)
    os_breakdown = _column_counts(Scan.os)
    recent_scans = scans_q.order_by(Scan.created_at.desc()).limit(15).all()

    top_cities = (
        db.session.query(Scan.city, db.func.count(Scan.id))
        .filter(Scan.city.isnot(None))
        .group_by(Scan.city)
        .order_by(db.func.count(Scan.id).desc())
        .limit(8)
        .all()
    )

    # last 14 days, per-day scan counts
    since = datetime.now(timezone.utc) - timedelta(days=14)
    daily = (
        db.session.query(db.func.date(Scan.created_at), db.func.count(Scan.id))
        .filter(Scan.created_at >= since)
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
        leads_count=Lead.query.count(),
        qr_count=QrCode.query.count(),
        campaigns_count=Campaign.query.count(),
    )


def _column_counts(column):
    rows = (
        db.session.query(column, db.func.count(column))
        .group_by(column)
        .order_by(db.func.count(column).desc())
        .all()
    )
    return [(label or "Unknown", count) for label, count in rows]


# --- campaigns -------------------------------------------------------------

@bp.route("/campaigns", methods=["GET", "POST"])
@login_required
def campaigns():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip() or slugify(name)
        if name and slug and not Campaign.query.filter_by(slug=slug).first():
            db.session.add(Campaign(name=name, slug=slug))
            db.session.commit()
    all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("admin/campaigns.html", campaigns=all_campaigns)


@bp.post("/campaigns/<int:cid>/delete")
@login_required
def delete_campaign(cid: int):
    camp = db.session.get(Campaign, cid)
    if camp:
        db.session.delete(camp)
        db.session.commit()
    return redirect(url_for("admin.campaigns"))


# --- QR codes --------------------------------------------------------------

@bp.route("/qr", methods=["GET"])
@login_required
def qr_list():
    codes = QrCode.query.order_by(QrCode.created_at.desc()).all()
    campaigns = Campaign.query.order_by(Campaign.name).all()
    return render_template("admin/qr_list.html", codes=codes, campaigns=campaigns)


@bp.route("/qr/new", methods=["GET", "POST"])
@login_required
def qr_new():
    campaigns = Campaign.query.order_by(Campaign.name).all()
    if request.method == "POST":
        slug = slugify(request.form.get("slug", ""))
        label = request.form.get("label", "").strip()
        destination = request.form.get("destination_url", "").strip()
        campaign_id = request.form.get("campaign_id") or None
        if slug and destination and not QrCode.query.filter_by(slug=slug).first():
            code = QrCode(
                slug=slug,
                label=label,
                destination_url=destination,
                campaign_id=int(campaign_id) if campaign_id else None,
                is_active=request.form.get("is_active") == "on",
            )
            db.session.add(code)
            db.session.commit()
            return redirect(url_for("admin.qr_list"))
    return render_template("admin/qr_edit.html", code=None, campaigns=campaigns)


@bp.route("/qr/<int:qid>", methods=["GET", "POST"])
@login_required
def qr_edit(qid: int):
    code = db.session.get(QrCode, qid) or abort(404)
    campaigns = Campaign.query.order_by(Campaign.name).all()
    if request.method == "POST":
        new_slug = slugify(request.form.get("slug", code.slug))
        clash = QrCode.query.filter(QrCode.slug == new_slug, QrCode.id != code.id).first()
        if not clash:
            code.slug = new_slug
            code.label = request.form.get("label", "").strip()
            code.destination_url = request.form.get("destination_url", "").strip()
            campaign_id = request.form.get("campaign_id") or None
            code.campaign_id = int(campaign_id) if campaign_id else None
            code.is_active = request.form.get("is_active") == "on"
            db.session.commit()
            return redirect(url_for("admin.qr_list"))
    return render_template("admin/qr_edit.html", code=code, campaigns=campaigns)


@bp.post("/qr/<int:qid>/delete")
@login_required
def qr_delete(qid: int):
    code = db.session.get(QrCode, qid)
    if code:
        db.session.delete(code)
        db.session.commit()
    return redirect(url_for("admin.qr_list"))


@bp.get("/qr/<int:qid>/png")
@login_required
def qr_png(qid: int):
    """Render a PNG of the QR for the code's redirect URL."""
    code = db.session.get(QrCode, qid) or abort(404)
    img = qrcode.make(code.destination_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"qr-{code.slug}.png",
    )


# --- leads -----------------------------------------------------------------

@bp.get("/leads")
@login_required
def leads():
    all_leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("admin/leads.html", leads=all_leads)


@bp.get("/leads/export.csv")
@login_required
def leads_csv():
    import csv

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "email", "interest", "message", "created_at"])
    for lead in Lead.query.order_by(Lead.created_at.desc()).all():
        writer.writerow(
            [
                lead.name,
                lead.email,
                lead.interest or "",
                lead.message or "",
                lead.created_at.isoformat() if lead.created_at else "",
            ]
        )
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
