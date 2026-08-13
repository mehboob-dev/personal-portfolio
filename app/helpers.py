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
    """Load a JSON file relative to the data dir (base_dir overrides for tests)."""
    path = (base_dir or (APP_DIR.parent / "data")) / name
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


def detect_app_source(ua_string: str) -> str:
    """Detect if scan was initiated inside a specific app webview/scanner."""
    ua = (ua_string or "").lower()
    if "whatsapp" in ua:
        return "WhatsApp"
    if "linkedin" in ua:
        return "LinkedIn"
    if "instagram" in ua:
        return "Instagram"
    if "fban" in ua or "fbav" in ua:
        return "Facebook"
    if "twitter" in ua or "tweet" in ua:
        return "Twitter / X"
    if "telegram" in ua:
        return "Telegram"
    if "slack" in ua:
        return "Slack"
    if "micromessenger" in ua:
        return "WeChat"
    if "line" in ua:
        return "LINE"
    if "crios" in ua or "chrome" in ua:
        return "Chrome"
    if "safari" in ua:
        return "Camera / Safari"
    if "firefox" in ua or "fxios" in ua:
        return "Firefox"
    if "edge" in ua or "edg" in ua:
        return "Edge"
    return "Direct / Browser"


def parse_user_agent(ua_string: str) -> dict:
    """Best-effort device/browser/OS/model from a UA string. Safe on garbage input."""
    try:
        from user_agents import parse

        ua = parse(ua_string or "")
        b_fam = ua.browser.family or "Unknown"
        b_ver = f"{b_fam} {ua.browser.version[0]}" if (ua.browser.version and len(ua.browser.version) > 0) else b_fam

        os_fam = ua.os.family or "Unknown"
        os_ver = f"{os_fam} {ua.os.version[0]}" if (ua.os.version and len(ua.os.version) > 0) else os_fam

        dev_type = "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
        dev_model = ua.device.family if (ua.device.family and ua.device.family != "Other") else ""

        return {
            "device": dev_type,
            "device_model": dev_model[:60] if dev_model else dev_type.capitalize(),
            "browser": b_ver[:60],
            "os": os_ver[:60],
            "app_source": detect_app_source(ua_string),
        }
    except Exception:
        return {
            "device": "Unknown",
            "device_model": "Unknown",
            "browser": "Unknown",
            "os": "Unknown",
            "app_source": "Direct / Browser",
        }
