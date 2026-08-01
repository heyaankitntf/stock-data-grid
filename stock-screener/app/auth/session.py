"""File-based session token persistence.

Used as a fallback / companion to the cookie-based auth — survives browser
cookie clears and is more reliable for long-lived sessions on a single host.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from app.config import COOKIE_TOKEN, SESSION_EXPIRY_DAYS, SESSION_FILE


def save_session(token: str, expiry_days: int = SESSION_EXPIRY_DAYS) -> None:
    """Persist session token to disk."""
    try:
        expiry = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        SESSION_FILE.write_text(json.dumps({"token": token, "expiry": expiry}))
    except Exception as e:
        logging.error("Failed to save session: %s", e)


def load_session() -> bool:
    """Return True if a valid (non-expired) session token exists on disk."""
    try:
        if not SESSION_FILE.exists():
            return False
        data = json.loads(SESSION_FILE.read_text())
        # Guard against missing/empty 'expiry' (e.g. freshly-seeded session.json
        # from the Docker entrypoint, or a hand-edited file). Without this,
        # datetime.fromisoformat('') raises ValueError and logs noise on every
        # page load.
        expiry_str = data.get("expiry", "")
        if not expiry_str:
            return False
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now() < expiry and data.get("token") == COOKIE_TOKEN:
            return True
        SESSION_FILE.unlink(missing_ok=True)
    except Exception as e:
        logging.error("Failed to load session: %s", e)
    return False


def clear_session() -> None:
    """Delete the session file (logout)."""
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except Exception as e:
        logging.error("Failed to clear session: %s", e)


def check_session() -> bool:
    """Alias for ``load_session`` — kept for API symmetry with cookie check."""
    return load_session()
