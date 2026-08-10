"""Public pages for the portfolio (KISS). All copy comes from content/*.json."""

from flask import Blueprint, redirect, render_template, request, url_for

from .extensions import db
from .helpers import get_content
from .models import Lead

bp = Blueprint("public", __name__)


@bp.get("/")
def home():
    return render_template(
        "public/home.html", content=get_content("home") or {}
    )


@bp.get("/about")
def about():
    return render_template(
        "public/about.html", content=get_content("about") or {}
    )


@bp.get("/experience")
def experience():
    return render_template(
        "public/experience.html", content=get_content("experience") or {}
    )


@bp.get("/projects")
def projects():
    return render_template(
        "public/projects.html", content=get_content("projects") or {}
    )


@bp.get("/trading-systems")
def trading_systems():
    return render_template(
        "public/trading_systems.html",
        content=get_content("trading_systems") or {},
    )


@bp.get("/contact")
def contact():
    return render_template("public/contact.html", sent=request.args.get("sent"))


@bp.post("/contact")
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    interest = request.form.get("interest", "").strip()
    message = request.form.get("message", "").strip()
    if name and email:
        db.session.add(Lead(name=name, email=email, interest=interest or None, message=message or None))
        db.session.commit()
        return redirect(url_for("public.contact", sent=1))
    return redirect(url_for("public.contact"))
