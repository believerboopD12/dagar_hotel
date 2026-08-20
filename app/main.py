"""Streamlit entry point for restaurant operations."""

import logging
from pathlib import Path

import streamlit as st

from app.config import settings
from app.db.database import initialize_database
from app.ui.pages import customer_page, dashboard_page, menu_page, new_order_page, orders_page
from app.utils.logging import configure_logging
from app.utils.security import verify_password

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Dagar Hotel Management", page_icon="???", layout="wide")


@st.cache_resource
def prepare_database() -> bool:
    initialize_database()
    logger.info("Application started in %s mode", settings.app_env)
    return True


def authenticated() -> bool:
    if settings.app_env == "development" and not settings.admin_password_hash:
        return True
    if not settings.admin_password_hash:
        st.error("APP_ADMIN_PASSWORD_HASH must be configured before production use.")
        return False
    if st.session_state.get("authenticated"):
        return True
    with st.form("login"):
        password = st.text_input("Administrator password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted and verify_password(password, settings.admin_password_hash):
        st.session_state.authenticated = True
        st.rerun()
    elif submitted:
        st.error("Invalid password.")
    return False


try:
    prepare_database()
except Exception:
    logger.exception("Database initialization failed")
    st.error("The database is unavailable. Verify DATABASE_URL and try again.")
    st.stop()

logo = Path(__file__).resolve().parents[1] / "assets" / "hologo.jpg"
if logo.exists():
    st.sidebar.image(str(logo), width=100)
st.sidebar.title("Dagar Hotel")
st.sidebar.caption("Restaurant operations")
if not authenticated():
    st.stop()

page = st.sidebar.radio(
    "Navigate", ["Dashboard", "Customers", "New order", "Orders & payments", "Menu"]
)
{
    "Dashboard": dashboard_page,
    "Customers": customer_page,
    "New order": new_order_page,
    "Orders & payments": orders_page,
    "Menu": menu_page,
}[page]()
