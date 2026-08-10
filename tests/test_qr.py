"""QR redirect engine tests."""

from app.extensions import db
from app.models import QrCode, Scan


def test_redirect_records_scan(client, app, seeded):
    res = client.get("/r/expo-card", headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"})
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com/expo"

    with app.app_context():
        scan = Scan.query.first()
        assert scan is not None
        assert scan.qr_code_id == seeded
        assert scan.device == "mobile"
        assert scan.ip_hash is not None  # anonymized, never the raw IP


def test_unknown_slug_404(client):
    res = client.get("/r/does-not-exist")
    assert res.status_code == 404


def test_inactive_code_still_redirects_but_no_scan(client, app, seeded):
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.is_active = False
        db.session.commit()

    res = client.get("/r/expo-card")
    assert res.status_code == 302

    with app.app_context():
        assert Scan.query.count() == 0


def test_destination_is_mutable(client, app, seeded):
    # Simulate an admin edit: repoint the same slug.
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.destination_url = "https://example.com/portfolio"
        db.session.commit()

    res = client.get("/r/expo-card")
    assert res.headers["Location"] == "https://example.com/portfolio"
