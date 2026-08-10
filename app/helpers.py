"""Small pure helpers (KISS): JSON loading, slugify, scan/analytics helpers.

No app/request context needed here except where noted.
"""

import hashlib
import json
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent


# --- JSON config / content -------------------------------------------------

def load_json(name: str, base_dir: Path | None = None) -> dict:
    """Load a JSON file relative to the app dir (base_dir overrides for tests)."""
    path = (base_dir or APP_DIR) / name
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_site_config(base_dir: Path | None = None) -> dict:
    return load_json("config.json", base_dir)


def get_content(name: str, base_dir: Path | None = None) -> dict:
    return load_json(f"content/{name}.json", base_dir)


# --- Strings ---------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# --- Scan analytics --------------------------------------------------------

def anonymize_ip(ip: str | None) -> str | None:
    """Return a sha256 hash of the IP. Never store the raw IP."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def parse_user_agent(ua_string: str) -> dict:
    """Best-effort device/browser/OS from a UA string. Safe on garbage input."""
    try:
        from user_agents import parse

        ua = parse(ua_string or "")
        return {
            "device": (
                "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
            ),
            "browser": (ua.browser.family or "Unknown")[:60],
            "os": (ua.os.family or "Unknown")[:60],
        }
    except Exception:
        return {"device": "Unknown", "browser": "Unknown", "os": "Unknown"}
