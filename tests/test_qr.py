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


def test_whatsapp_telegram_and_toggles(client, app, seeded):
    # 1. Test WhatsApp destination validation & 302 redirect
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.destination_url = "https://wa.me/971501234567?text=Hello"
        code.show_lead_form = False
        code.show_call_button = False
        db.session.commit()

    res_wa = client.get("/r/expo-card")
    assert res_wa.status_code == 302
    assert res_wa.headers["Location"] == "https://wa.me/971501234567?text=Hello"

    # 2. Test landing page with Lead Capture Form toggle enabled
    with app.app_context():
        code = db.session.get(QrCode, seeded)
        code.show_lead_form = True
        code.show_call_button = True
        code.call_phone_number = "+971501234567"
        db.session.commit()

    res_landing = client.get("/r/expo-card")
    assert res_landing.status_code == 200
    html = res_landing.get_data(as_text=True)
    assert "Share Your Contact Info" in html
    assert "Call Me Direct (+971501234567)" in html
    assert "Continue to Destination" in html

    # 3. Test submitting lead form from QR landing page keeps user on QR landing page
    res_sub = client.post(
        "/contact",
        data={"name": "QR Guest", "phone": "971500001111", "qr_slug": "expo-card"},
        follow_redirects=True,
    )
    assert res_sub.status_code == 200
    html_sub = res_sub.get_data(as_text=True)
    assert "Thank you! Your contact information has been shared successfully." in html_sub
