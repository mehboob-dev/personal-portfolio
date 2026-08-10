"""Public page smoke tests."""

PAGES = ["/", "/about", "/experience", "/projects", "/trading-systems", "/contact", "/expo"]


def test_public_pages_render(client):
    for path in PAGES:
        res = client.get(path)
        assert res.status_code == 200, f"{path} returned {res.status_code}"


def test_home_shows_benchmark(client):
    html = client.get("/").get_data(as_text=True)
    assert "SYMBOLS" in html or "Symbols" in html


def test_expo_data_endpoint(client):
    res = client.get("/expo/data/BTCUSDT_1m_orb.json")
    assert res.status_code == 200
    data = res.get_json()
    assert "candles" in data
    assert len(data["candles"]) > 0


def test_expo_data_path_traversal_blocked(client):
    res = client.get("/expo/data/../config.json")
    assert res.status_code == 404
