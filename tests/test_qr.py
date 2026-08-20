"""QR redirect engine tests."""

from app.extensions import db
from app.models import QrCode, Scan


def test_redirect_records_scan(client, app, seeded):
    res = client.get(
        "/r/expo-card?utm_source=visiting_card&utm_campaign=dubai_2026",
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 WhatsApp/2.23.20.78",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com/expo"

    with app.app_context():
        scan = Scan.query.first()
        assert scan is not None
        assert scan.qr_code_id == seeded
        assert scan.device == "mobile"
        assert scan.app_source == "WhatsApp"
        assert scan.language == "en-US"
        assert scan.utm_source == "visiting_card"
        assert scan.utm_campaign == "dubai_2026"
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


def test_vcard_and_text_destinations(client, app, seeded):
    # 1. Test vCard payload rendering
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.destination_url = "vcard:BEGIN:VCARD\nFN:Mehboob Meghani\nTEL:+123456789\nEND:VCARD"
        db.session.commit()

    res = client.get("/r/expo-card")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Mehboob Meghani" in html
    assert "Save Contact (.vcf)" in html

    # 2. Test plain text note rendering
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.destination_url = "text:Welcome to Dubai Expo 2026!"
        db.session.commit()

    res_text = client.get("/r/expo-card")
    assert res_text.status_code == 200
    html_text = res_text.get_data(as_text=True)
    assert "Welcome to Dubai Expo 2026!" in html_text
