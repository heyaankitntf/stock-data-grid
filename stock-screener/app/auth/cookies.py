"""Cookie-based authentication controller.

Wraps ``streamlit_cookies_controller``. Each instance must have a stable
``key`` so Streamlit doesn't re-mount the underlying component on every
rerun (re-mounting causes a JS round-trip that briefly returns ``None``,
which previously caused the dark->light theme flash).
"""
from __future__ import annotations

import streamlit as st
from streamlit_cookies_controller import CookieController

from app.auth.session import clear_session, load_session, save_session
from app.config import COOKIE_AUTH, COOKIE_TOKEN


_CONTROLLER_KEY = "cookie_manager_v1"
_controller: CookieController | None = None


def get_cookie_controller() -> CookieController:
    """Return the singleton CookieController.

    Re-using the same instance with a stable key prevents Streamlit from
    re-mounting the cookie component on every rerun, which would otherwise
    cause a brief ``None`` return value and trigger a flash.
    """
    global _controller
    if _controller is None:
        _controller = CookieController(key=_CONTROLLER_KEY)
    return _controller


def is_authenticated() -> bool:
    """Return True if either the cookie or the file session is valid.

    Checking both means a browser cookie clear doesn't log the user out
    if the file session is still alive, and vice versa.
    """
    cookies = get_cookie_controller()
    try:
        cookie_ok = cookies.get(COOKIE_AUTH) == COOKIE_TOKEN
    except Exception:
        cookie_ok = False
    return cookie_ok or load_session()


def _set_auth_cookie() -> None:
    cookies = get_cookie_controller()
    try:
        cookies.set(COOKIE_AUTH, COOKIE_TOKEN, max_age=30 * 24 * 3600)
    except Exception:
        pass


def _clear_auth_cookie() -> None:
    cookies = get_cookie_controller()
    try:
        cookies.remove(COOKIE_AUTH)
    except Exception:
        pass
