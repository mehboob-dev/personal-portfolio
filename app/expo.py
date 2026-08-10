"""Money Expo interactive trading-engine demo.

Serves a mobile-first 5-screen flow. Strategy metadata comes from
config.json; the replay dataset is static JSON served from /expo/data/<file>.
"""

import json
from pathlib import Path

from flask import Blueprint, render_template

from .helpers import get_site_config

bp = Blueprint("expo", __name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@bp.get("/expo")
def index():
    cfg = get_site_config()
    return render_template(
        "expo/index.html",
        expo=cfg.get("expo", {}),
        identity=cfg.get("identity", {}),
        benchmark=cfg.get("benchmark", {}),
        engine=cfg.get("engine", {}),
        site=cfg.get("site", {}),
    )


@bp.get("/expo/data/<path:name>")
def dataset(name: str):
    """Serve a replay dataset. Guard against path traversal."""
    path = (DATA_DIR / name).resolve()
    if not str(path).startswith(str(DATA_DIR.resolve())) or not path.exists():
        return json.dumps({"error": "not found"}), 404, {"Content-Type": "application/json"}
    return path.read_text(encoding="utf-8"), 200, {"Content-Type": "application/json"}
