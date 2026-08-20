"""Application factory for the portfolio + QR manager (KISS)."""

import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template
from flask_login import current_user

from .extensions import csrf, db, login_manager, migrate

APP_DIR = Path(__file__).resolve().parent


def _load_secrets() -> dict:
    """Secrets live in a gitignored JSON file (user: no .env, only JSON)."""
    secrets_path = APP_DIR.parent / "data" / "secrets.json"
    if secrets_path.exists():
        return json.loads(secrets_path.read_text(encoding="utf-8"))
    # Fall back to a checked-in example so the app runs on a fresh clone.
    example = APP_DIR.parent / "data" / "secrets.example.json"
    if example.exists():
        return json.loads(example.read_text(encoding="utf-8"))
    return {}


def _resolve_db_url(url: str) -> str:
    """Make relative sqlite paths absolute (Flask-SQLAlchemy resolves them
    against instance_path, which trips people up)."""
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel = url[len("sqlite:///"):]
        if not Path(rel).is_absolute():
            abs_path = APP_DIR.parent / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)  # ensure data/ exists
            return f"sqlite:///{abs_path.as_posix()}"
    return url


def _sync_admin_from_secrets() -> None:
    """Ensure the AdminUser in DB matches current secrets.json credentials."""
    try:
        from .models import AdminUser

        secrets = _load_secrets()
        username = secrets.get("ADMIN_USERNAME", "admin")
        password = secrets.get("ADMIN_PASSWORD", "change-me-strong")

        user = AdminUser.query.filter_by(username=username).first()
        if user:
            if not user.check_password(password):
                user.set_password(password)
                db.session.commit()
        else:
            first_user = AdminUser.query.first()
            if first_user:
                first_user.username = username
                first_user.set_password(password)
                db.session.commit()
            else:
                new_user = AdminUser(username=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
    except Exception:
        db.session.rollback()


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    secrets = _load_secrets()
    app.config["SECRET_KEY"] = secrets.get("SECRET_KEY", "dev-insecure-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = _resolve_db_url(
        secrets.get("DATABASE_URL", "sqlite:///data/app.db")
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SEED_ADMIN"] = secrets

    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401  (register models with SQLAlchemy)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.AdminUser, int(user_id))

    # Admin credentials are synced from secrets.json on startup. Schema is
    # managed by Alembic (`flask db upgrade`), not create_all, so the two
    # cannot drift. create_all remains available via the `init-db` CLI command.
    with app.app_context():
        try:
            _sync_admin_from_secrets()
        except Exception:
            pass

    # Blueprints (flat, KISS)
    from .admin import bp as admin_bp
    from .public import bp as public_bp
    from .qr import bp as qr_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(admin_bp)

    # CLI: `flask init-db` creates tables + admin user (dev convenience)
    @app.cli.command("init-db")
    def init_db():
        import click

        db.create_all()
        _sync_admin_from_secrets()
        secrets = _load_secrets()
        username = secrets.get("ADMIN_USERNAME", "admin")
        click.echo(f"Database ready. Admin user '{username}' synced with secrets.json.")

    # CLI: `flask seed` (alias) creates the admin user from secrets.json
    @app.cli.command("seed")
    def seed_admin():
        import click

        _sync_admin_from_secrets()
        secrets = _load_secrets()
        username = secrets.get("ADMIN_USERNAME", "admin")
        click.echo(f"Admin user '{username}' synced with secrets.json.")

    # Inject site config + nav into every template
    @app.context_processor
    def inject_config():
        cfg = {}
        cfg_path = APP_DIR.parent / "data" / "config.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        return {"site": cfg, "current_user": current_user, "now": datetime.now(timezone.utc)}

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("public/404.html"), 404

    return app
