"""Login form, login action, logout action."""
from __future__ import annotations

import streamlit as st

from app.auth.cookies import _clear_auth_cookie, _set_auth_cookie, get_cookie_controller
from app.auth.session import clear_session, save_session
from app.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.styles.palettes import Palette


def do_login(username: str, password: str, remember: bool) -> bool:
    """Validate credentials and, on success, persist auth in cookie + file."""
    if username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        if remember:
            _set_auth_cookie()
            save_session(_auth_token())
        return True
    return False


def _auth_token() -> str:
    from app.config import COOKIE_TOKEN
    return COOKIE_TOKEN


def do_logout() -> None:
    """Clear all auth state: session_state, cookie, file session."""
    for k in ("authenticated", "df_results", "last_scan", "scanned",
              "trade_preview", "portfolio_prices", "_confirm_reset"):
        st.session_state.pop(k, None)
    _clear_auth_cookie()
    clear_session()


def render_login_page(p: Palette) -> None:
    """Render the login form and stop further script execution."""
    st.markdown(f"""
<style>
.block-container {{
    max-width:440px !important; margin:0 auto !important;
    padding-top:5rem !important; padding-left:1.2rem !important; padding-right:1.2rem !important;
}}
@media (max-width:480px) {{ .block-container {{ padding-top:2.5rem !important; }} }}
</style>
<div style="background:{p['bg2']};border:1px solid {p['border']};border-radius:16px;
    padding:2.2rem 2.4rem 1.6rem;box-shadow:0 16px 48px rgba(0,0,0,.22);margin-bottom:1.2rem;">
  <div style="font-size:1.5rem;font-weight:800;color:{p['text']};letter-spacing:-.4px;margin-bottom:.2rem;">
    📈 Breakout Scanner
  </div>
  <div style="font-size:.85rem;color:{p['text_muted']};">Sign in to access the dashboard</div>
</div>
""", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username  = st.text_input("Username", placeholder="admin")
        password  = st.text_input("Password", type="password", placeholder="••••••••")
        remember  = st.checkbox("Remember me for 30 days")
        submitted = st.form_submit_button("🔐 Sign In", width="stretch")
    if submitted:
        if do_login(username, password, remember):
            st.rerun()
        else:
            st.error("❌ Incorrect username or password.", icon="🚫")
    st.markdown(
        '<div class="footer">Authorised access only · Not financial advice</div>',
        unsafe_allow_html=True,
    )
    st.stop()
