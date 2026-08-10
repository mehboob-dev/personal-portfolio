"""Admin + lead tests."""

from app.extensions import db
from app.models import Lead


def test_admin_requires_login(client):
    res = client.get("/admin/", follow_redirects=False)
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]


def test_admin_login_and_dashboard(admin_client):
    res = admin_client.get("/admin/")
    assert res.status_code == 200
    assert "Dashboard" in res.get_data(as_text=True)


def test_admin_qr_crud(admin_client, app, seeded):
    # edit destination via admin form
    res = admin_client.post(
        f"/admin/qr/{seeded}",
        data={
            "slug": "expo-card",
            "label": "Visiting card (updated)",
            "destination_url": "https://example.com/new-target",
            "is_active": "on",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    with app.app_context():
        from app.models import QrCode
        assert db.session.get(QrCode, seeded).destination_url == "https://example.com/new-target"


def test_admin_png_download(admin_client, seeded):
    res = admin_client.get(f"/admin/qr/{seeded}/png")
    assert res.status_code == 200
    assert res.mimetype == "image/png"


def test_contact_submit_creates_lead(client, app):
    res = client.post(
        "/contact",
        data={"name": "Jane", "email": "jane@example.com", "interest": "hiring"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    with app.app_context():
        lead = Lead.query.first()
        assert lead is not None
        assert lead.name == "Jane"
        assert lead.interest == "hiring"


def test_leads_csv(admin_client, app):
    with app.app_context():
        db.session.add(Lead(name="Jane", email="jane@example.com", interest="hiring"))
        db.session.commit()
    res = admin_client.get("/admin/leads/export.csv")
    assert res.status_code == 200
    assert "jane@example.com" in res.get_data(as_text=True)
