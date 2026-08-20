"""Streamlit entry point with separate customer and staff portals."""

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings  # noqa: E402, I001
from app.db.database import initialize_database  # noqa: E402
from app.ui.pages import (  # noqa: E402
    customer_management_page,
    customer_order_page,
    dashboard_page,
    menu_page,
    orders_page,
    staff_order_page,
    track_order_page,
)
from app.utils.logging import configure_logging  # noqa: E402
from app.utils.security import verify_password  # noqa: E402

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Dagar Hotel", page_icon="???", layout="wide")


@st.cache_resource
def prepare_database() -> bool:
    initialize_database()
    logger.info("Application started in %s mode", settings.app_env)
    return True


def staff_login() -> bool:
    if st.session_state.get("staff_authenticated"):
        return True
    st.header("Staff administration")
    if not settings.admin_password_hash:
        st.warning("Staff login is not configured on this device.")
        st.code("python -m scripts.hash_password")
        st.caption(
            "Add the generated value to APP_ADMIN_PASSWORD_HASH in your local .env, then restart."
        )
        return False
    with st.form("staff_login"):
        password = st.text_input("Staff password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted and verify_password(password, settings.admin_password_hash):
        st.session_state.staff_authenticated = True
        logger.info("Staff login succeeded")
        st.rerun()
    elif submitted:
        st.error("Invalid staff password.")
    return False


try:
    prepare_database()
except Exception:
    logger.exception("Database initialization failed")
    st.error("The database is unavailable. Check local configuration and try again.")
    st.stop()

logo = PROJECT_ROOT / "assets" / "hologo.jpg"
if logo.exists():
    st.sidebar.image(str(logo), width=100)
st.sidebar.title("Dagar Hotel")
portal = st.sidebar.radio("Portal", ["Customer", "Staff / Admin"])

if portal == "Customer":
    st.sidebar.caption("Order food or track your own orders")
    page = st.sidebar.radio("Customer menu", ["Place order", "Track order"])
    {"Place order": customer_order_page, "Track order": track_order_page}[page]()
else:
    st.sidebar.caption("Restricted restaurant operations")
    if not staff_login():
        st.stop()
    if st.sidebar.button("Sign out"):
        st.session_state.staff_authenticated = False
        st.rerun()
    page = st.sidebar.radio(
        "Staff menu",
        ["Dashboard", "Counter order", "Orders & payments", "Customers", "Menu"],
    )
    {
        "Dashboard": dashboard_page,
        "Counter order": staff_order_page,
        "Orders & payments": orders_page,
        "Customers": customer_management_page,
        "Menu": menu_page,
    }[page]()
