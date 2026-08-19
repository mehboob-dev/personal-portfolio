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
    assert "SYMBOLS" in html or "Symbols" in html


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


def test_education_independent(client):
    from app.helpers import get_content
    education = get_content("education")
    assert education is not None
    assert "items" in education
    assert len(education["items"]) > 0
    for item in education["items"]:
        assert "degree" in item
        assert "institution" in item
        assert "period" in item
        assert "focus" in item
