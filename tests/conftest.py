import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db
from app.models import AdminUser, Campaign, QrCode


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "poolclass": StaticPool,  # one shared in-memory DB across connections
                "connect_args": {"check_same_thread": False},
            },
            "SQLALCHEMY_SESSION_OPTIONS": {"expire_on_commit": False},
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded(app):
    """A campaign + active QR code pointing at a known destination.

    Returns the QrCode id (a plain int) so tests avoid lazy-loading a
    detached instance outside the app context.
    """
    with app.app_context():
        camp = Campaign(name="Money Expo 2026", slug="money-expo-2026")
        code = QrCode(
            slug="expo-card",
            label="Visiting card",
            destination_url="https://example.com/expo",
            campaign=camp,
            is_active=True,
        )
        db.session.add_all([camp, code])
        db.session.commit()
        return code.id


def make_admin(app):
    with app.app_context():
        user = AdminUser(username="admin")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture()
def admin_client(app, client):
    make_admin(app)
    client.post(
        "/admin/login", data={"username": "admin", "password": "secret"}, follow_redirects=True
    )
    return client
