"""Public page smoke tests for the single-page portfolio."""

# Legacy paths should redirect to the matching section anchor.
LEGACY_ANCHORS = {
    "/about": "#about",
    "/experience": "#experience",
    "/projects": "#projects",
    "/trading-systems": "#engine",
    "/contact": "#contact",
}


def test_home_renders(client):
    res = client.get("/")
    assert res.status_code == 200


def test_legacy_paths_redirect_to_anchors(client):
    for path, anchor in LEGACY_ANCHORS.items():
        res = client.get(path)
        assert res.status_code == 302, f"{path} expected 302, got {res.status_code}"
        assert anchor in res.headers["Location"], f"{path} → {res.headers['Location']}"


def test_home_shows_benchmark(client):
    html = client.get("/").get_data(as_text=True)
    assert "Market Domains" in html or "Memory Reduction" in html


def test_home_shows_sections(client):
    html = client.get("/").get_data(as_text=True)
    for section in ["about", "experience", "projects", "skills", "education", "contact"]:
        assert f'id="{section}"' in html, f"missing #{section} section"


def test_projects_defaults_preprocessing(client):
    from app.helpers import get_content
    projects = get_content("projects")
    assert projects is not None
    # Verify flagship systems defaults are merged
    for system in projects.get("flagship_systems", []):
        assert "classification_class" in system
        assert system["classification_class"] is not None
        for tech in system.get("stack", []):
            if isinstance(tech, dict):
                assert "class" in tech
                assert tech["class"] is not None

        evidence = system.get("evidence")
        if evidence and "link" in evidence:
            link = evidence["link"]
            assert link.get("label") is not None
            assert link.get("icon") is not None

    # Verify secondary artifacts defaults are merged
    for artifact in projects.get("secondary_artifacts", []):
        assert "classification_class" in artifact
        assert artifact["classification_class"] is not None

        link = artifact.get("link")
        if link:
            assert link.get("label") is not None
            assert link.get("icon") is not None


def test_contact_submit_with_phone(client, app):
    from app.models import Lead

    # 1. Valid phone submit without +
    res = client.post(
        "/contact",
        data={"name": "Alice Tester", "phone": "971501234567", "message": "Hello"},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        lead = Lead.query.filter_by(name="Alice Tester").first()
        assert lead is not None
        assert lead.phone == "971501234567"
        assert lead.email is None

    # 2. Phone submit with leading + gets cleaned
    res2 = client.post(
        "/contact",
        data={"name": "Bob Tester", "phone": "+971509998888"},
        follow_redirects=True,
    )
    assert res2.status_code == 200

    with app.app_context():
        lead2 = Lead.query.filter_by(name="Bob Tester").first()
        assert lead2 is not None
        assert lead2.phone == "971509998888"
