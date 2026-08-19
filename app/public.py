"""Public pages for the portfolio (KISS). Single scrolling page driven by
config.json + content/*.json. Legacy /about, /experience, etc. redirect to
the matching section anchors."""

from flask import Blueprint, redirect, render_template, request, url_for

from .extensions import db
from .helpers import get_content
from .models import Lead

bp = Blueprint("public", __name__)

# Legacy paths → section anchors on the single page.
_ANCHORS = {
    "about": "#about",
    "experience": "#experience",
    "projects": "#projects",
    "trading-systems": "#engine",
    "contact": "#contact",
}


@bp.get("/")
def home():
    return render_template(
        "public/home.html",
        content={
            "about": get_content("about") or {},
            "experience": get_content("experience") or {},
            "education": get_content("education") or {},
            "projects": get_content("projects") or {},
            "contact": get_content("contact") or {},
        },
        sent=request.args.get("sent"),
    )


@bp.get("/about")
def about():
    return redirect(url_for("public.home", _anchor="about"))


@bp.get("/experience")
def experience():
    return redirect(url_for("public.home", _anchor="experience"))


@bp.get("/projects")
def projects():
    return redirect(url_for("public.home", _anchor="projects"))


@bp.get("/trading-systems")
def trading_systems():
    return redirect(url_for("public.home", _anchor="engine"))


@bp.get("/contact")
def contact():
    return redirect(url_for("public.home", _anchor="contact"))


@bp.post("/contact")
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    interest = request.form.get("interest", "").strip()
    message = request.form.get("message", "").strip()
    if name and email:
        db.session.add(Lead(name=name, email=email, interest=interest or None, message=message or None))
        db.session.commit()
        return redirect(url_for("public.home", sent=1, _anchor="contact"))
    return redirect(url_for("public.home", _anchor="contact"))
