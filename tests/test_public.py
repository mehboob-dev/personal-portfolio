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
