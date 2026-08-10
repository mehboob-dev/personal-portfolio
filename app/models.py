"""SQLAlchemy models for the portfolio + QR manager.

One file on purpose (KISS). Every model is a plain table with no business logic.
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    qr_codes = db.relationship("QrCode", back_populates="campaign", lazy="dynamic")


class QrCode(db.Model):
    __tablename__ = "qr_codes"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    label = db.Column(db.String(200), nullable=False, default="")
    # The mutable destination — this is what makes the printed card reusable.
    destination_url = db.Column(db.String(2000), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    campaign = db.relationship("Campaign", back_populates="qr_codes")
    scans = db.relationship("Scan", back_populates="qr_code", lazy="dynamic")


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    qr_code_id = db.Column(db.Integer, db.ForeignKey("qr_codes.id"), nullable=False)
    # Anonymized: store a hash of the IP, never the raw IP.
    ip_hash = db.Column(db.String(64), nullable=True)
    device = db.Column(db.String(40), nullable=True)
    browser = db.Column(db.String(60), nullable=True)
    os = db.Column(db.String(60), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    qr_code = db.relationship("QrCode", back_populates="scans")


class Lead(db.Model):
    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    interest = db.Column(db.String(40), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
