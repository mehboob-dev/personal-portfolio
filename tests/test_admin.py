"""Admin + lead + QR + campaign tests."""

from app.extensions import db
from app.models import Campaign, Lead, QrCode


def test_admin_requires_login(client):
    res = client.get("/admin/", follow_redirects=False)
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]


def test_csrf_token_present_on_public_contact_form(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'name="csrf_token"' in html


def test_csrf_rejects_post_without_token(app):
    # CSRF is globally ON in the real app config; this app forces it OFF for
    # the rest of the suite. Test the protection is actually wired by turning
    # it back on here.
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    res = client.post("/admin/login", data={"username": "admin", "password": "secret"})
    assert res.status_code == 400


def test_csrf_rejects_post_with_invalid_token(app):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    res = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret", "csrf_token": "invalid-token"},
    )
    assert res.status_code == 400


def test_admin_login_and_dashboard(admin_client):
    res = admin_client.get("/admin/")
    assert res.status_code == 200
    assert "Dashboard" in res.get_data(as_text=True)


def test_admin_login_failure(client):
    res = client.post(
        "/admin/login",
        data={"username": "wrong_user", "password": "wrong_password"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Invalid username or password" in html
    assert 'value="wrong_user"' in html


def test_admin_qr_crud_and_trash_recover_purge(admin_client, app, seeded):
    # 1. Edit destination via admin form
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
        assert db.session.get(QrCode, seeded).destination_url == "https://example.com/new-target"

    # 2. Move QR to trash (soft delete)
    res_trash = admin_client.post(f"/admin/qr/{seeded}/delete", follow_redirects=True)
    assert res_trash.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, seeded).is_deleted is True

    # 3. Public redirect should now 404
    res_redirect = admin_client.get("/r/expo-card")
    assert res_redirect.status_code == 404

    # 4. Recover from trash
    res_restore = admin_client.post(f"/admin/qr/{seeded}/restore", follow_redirects=True)
    assert res_restore.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, seeded).is_deleted is False

    # 5. Permanent delete (purge)
    res_purge = admin_client.post(f"/admin/qr/{seeded}/purge", follow_redirects=True)
    assert res_purge.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, seeded) is None


def test_qr_stats_view(admin_client, seeded):
    res = admin_client.get(f"/admin/qr/{seeded}/stats")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Analytics:" in html
    assert "expo-card" in html
    assert "Daily Scans" in html


def test_qr_scans_csv_export(admin_client, seeded):
    res = admin_client.get(f"/admin/qr/{seeded}/export-scans.csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "scan_id,date_utc,time_utc,qr_slug" in res.get_data(as_text=True)


def test_admin_campaign_trash_recover_purge(admin_client, app):
    # 1. Create campaign
    res_create = admin_client.post(
        "/admin/campaigns",
        data={"name": "Tech Summit 2026", "slug": "tech-summit-2026"},
        follow_redirects=True,
    )
    assert res_create.status_code == 200
    with app.app_context():
        camp = Campaign.query.filter_by(slug="tech-summit-2026").first()
        assert camp is not None
        cid = camp.id

    # 2. Move campaign to trash
    res_trash = admin_client.post(f"/admin/campaigns/{cid}/delete", follow_redirects=True)
    assert res_trash.status_code == 200
    with app.app_context():
        assert db.session.get(Campaign, cid).is_deleted is True

    # 3. Recover campaign
    res_restore = admin_client.post(f"/admin/campaigns/{cid}/restore", follow_redirects=True)
    assert res_restore.status_code == 200
    with app.app_context():
        assert db.session.get(Campaign, cid).is_deleted is False

    # 4. Permanent purge
    res_purge = admin_client.post(f"/admin/campaigns/{cid}/purge", follow_redirects=True)
    assert res_purge.status_code == 200
    with app.app_context():
        assert db.session.get(Campaign, cid) is None


def test_admin_png_download(admin_client, seeded):
    res = admin_client.get(f"/admin/qr/{seeded}/png")
    assert res.status_code == 200
    assert res.mimetype == "image/png"


def test_contact_submit_creates_lead(client, app):
    res = client.post(
        "/contact",
        data={"name": "Jane", "email": "jane@example.com", "interest": "hiring", "message": "Long inquiry message here..."},
        follow_redirects=True,
    )
    assert res.status_code == 200
    with app.app_context():
        lead = Lead.query.first()
        assert lead is not None
        assert lead.name == "Jane"
        assert lead.interest == "hiring"
        assert lead.is_deleted is False


def test_leads_csv(admin_client, app):
    with app.app_context():
        db.session.add(Lead(name="Jane", email="jane@example.com", interest="hiring"))
        db.session.commit()
    res = admin_client.get("/admin/leads/export.csv")
    assert res.status_code == 200
    assert "jane@example.com" in res.get_data(as_text=True)


def test_lead_detail_view(admin_client, app):
    with app.app_context():
        lead = Lead(name="John Doe", email="john@example.com", interest="quant-infra", message="Detailed long message content")
        db.session.add(lead)
        db.session.commit()
        lid = lead.id

    res = admin_client.get(f"/admin/leads/{lid}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "John Doe" in html
    assert "Detailed long message content" in html


def test_lead_trash_recover_purge(admin_client, app):
    with app.app_context():
        lead = Lead(name="Alice", email="alice@example.com", interest="trading-engine", message="Testing soft delete")
        db.session.add(lead)
        db.session.commit()
        lid = lead.id

    # 1. Soft delete (move to trash)
    res_del = admin_client.post(f"/admin/leads/{lid}/delete", follow_redirects=True)
    assert res_del.status_code == 200
    with app.app_context():
        assert db.session.get(Lead, lid).is_deleted is True

    # 2. Active view should not show it by default
    res_active = admin_client.get("/admin/leads")
    assert "Alice" not in res_active.get_data(as_text=True)

    # 3. Deleted view shows it
    res_trash = admin_client.get("/admin/leads?show=deleted")
    assert "Alice" in res_trash.get_data(as_text=True)

    # 4. Restore
    res_restore = admin_client.post(f"/admin/leads/{lid}/restore", follow_redirects=True)
    assert res_restore.status_code == 200
    with app.app_context():
        assert db.session.get(Lead, lid).is_deleted is False

    # 5. Permanent purge
    res_purge = admin_client.post(f"/admin/leads/{lid}/purge", follow_redirects=True)
    assert res_purge.status_code == 200
    with app.app_context():
        assert db.session.get(Lead, lid) is None


def test_scan_trash_recover_purge(admin_client, app, seeded):
    with app.app_context():
        from app.models import Scan
        scan = Scan(qr_code_id=seeded, device="mobile", browser="Safari", os="iOS", ip_hash="test-hash-123")
        db.session.add(scan)
        db.session.commit()
        sid = scan.id

    # 1. Soft delete scan (move to trash)
    res_del = admin_client.post(f"/admin/scans/{sid}/delete", follow_redirects=True)
    assert res_del.status_code == 200
    with app.app_context():
        from app.models import Scan
        assert db.session.get(Scan, sid).is_deleted is True

    # 2. Restore scan
    res_restore = admin_client.post(f"/admin/scans/{sid}/restore", follow_redirects=True)
    assert res_restore.status_code == 200
    with app.app_context():
        from app.models import Scan
        assert db.session.get(Scan, sid).is_deleted is False

    # 3. Permanent purge
    res_purge = admin_client.post(f"/admin/scans/{sid}/purge", follow_redirects=True)
    assert res_purge.status_code == 200
    with app.app_context():
        from app.models import Scan
        assert db.session.get(Scan, sid) is None


def test_qr_destination_validation_rejects_non_http(admin_client, app):
    # javascript: / ftp: / bare paths are open-redirect / broken-card vectors
    bad_values = [
        "javascript:alert(1)",
        "ftp://example.com/file",
        "example.com",  # no scheme
        "/r/relative-path",
    ]
    for bad in bad_values:
        res = admin_client.post(
            "/admin/qr/new",
            data={
                "slug": "bad-" + str(len(bad)),
                "label": "Bad target",
                "destination_url": bad,
            },
            follow_redirects=True,
        )
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "Invalid destination format" in html
        with app.app_context():
            assert QrCode.query.filter_by(destination_url=bad).first() is None


def test_qr_destination_validation_accepts_https(admin_client, app):
    res = admin_client.post(
        "/admin/qr/new",
        data={
            "slug": "good-card",
            "label": "Good target",
            "destination_url": "https://example.com/portfolio",
            "is_active": "on",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    with app.app_context():
        code = QrCode.query.filter_by(slug="good-card").first()
        assert code is not None
        assert code.destination_url == "https://example.com/portfolio"


def test_qr_edit_rejects_invalid_destination(admin_client, app, seeded):
    res = admin_client.post(
        f"/admin/qr/{seeded}",
        data={
            "slug": "expo-card",
            "label": "Still visiting card",
            "destination_url": "javascript:alert(1)",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Destination URL must be an absolute http(s) link" in html
    with app.app_context():
        # unchanged
        assert db.session.get(QrCode, seeded).destination_url == "https://example.com/expo"


def test_bulk_actions_across_models(admin_client, app, seeded):
    with app.app_context():
        # Create multiple test QR codes
        q1 = QrCode(slug="bulk-1", destination_url="https://example.com/1")
        q2 = QrCode(slug="bulk-2", destination_url="https://example.com/2")
        db.session.add_all([q1, q2])
        db.session.commit()
        q1_id, q2_id = q1.id, q2.id

    # 1. Bulk trash QR codes
    res_trash = admin_client.post("/admin/qr/bulk", data={"action": "trash", "ids": [q1_id, q2_id]}, follow_redirects=True)
    assert res_trash.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, q1_id).is_deleted is True
        assert db.session.get(QrCode, q2_id).is_deleted is True

    # 2. Bulk restore QR codes
    res_restore = admin_client.post("/admin/qr/bulk", data={"action": "restore", "ids": [q1_id, q2_id]}, follow_redirects=True)
    assert res_restore.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, q1_id).is_deleted is False
        assert db.session.get(QrCode, q2_id).is_deleted is False

    # 3. Bulk purge QR codes
    res_purge = admin_client.post("/admin/qr/bulk", data={"action": "purge", "ids": [q1_id, q2_id]}, follow_redirects=True)
    assert res_purge.status_code == 200
    with app.app_context():
        assert db.session.get(QrCode, q1_id) is None
        assert db.session.get(QrCode, q2_id) is None
