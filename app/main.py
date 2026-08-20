"""Streamlit entry point with customer and role-based staff portals."""

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import initialize_database, session_scope  # noqa: E402, I001
from app.db.models import UserRole  # noqa: E402
from app.services.auth import authenticate_user, authorize_action  # noqa: E402
from app.ui.pages import (  # noqa: E402
    customer_management_page,
    customer_order_page,
    dashboard_page,
    menu_browse_page,
    menu_page,
    orders_page,
    staff_customers_page,
    staff_order_page,
    track_order_page,
)
from app.utils.logging import configure_logging  # noqa: E402
from app.config import settings  # noqa: E402

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Dagar Hotel", page_icon="???", layout="wide")


@st.cache_resource
def prepare_database() -> bool:
    initialize_database()
    logger.info("Application started in %s mode", settings.app_env)
    return True


def staff_login() -> bool:
    if st.session_state.get("authenticated_user"):
        return True
    st.header("Staff login")
    with st.form("staff_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        with session_scope() as session:
            user = authenticate_user(session, username, password, settings.app_env)
        if user:
            st.session_state.authenticated_user = {
                "id": user.id,
                "username": user.username,
                "role": user.role.value,
            }
            logger.info("Staff login succeeded for role %s", user.role.value)
            st.rerun()
        else:
            st.error("Invalid username or password.")
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
    st.sidebar.caption("Order food or track your own order")
    page = st.sidebar.radio("Customer menu", ["Place order", "Track order"])
    {"Place order": customer_order_page, "Track order": track_order_page}[page]()
else:
    if not staff_login():
        st.stop()
    current = st.session_state.authenticated_user
    role = UserRole(current["role"])
    st.sidebar.success(f"Signed in: {current['username']} ({role.value})")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("authenticated_user", None)
        st.rerun()

    admin_pages = {
        "Dashboard": ("dashboard", dashboard_page),
        "Counter order": ("counter_order", staff_order_page),
        "Orders & payments": ("orders", orders_page),
        "Customer management": ("customers_admin", customer_management_page),
        "Menu management": ("menu_admin", menu_page),
    }
    staff_pages = {
        "Dashboard": ("dashboard", dashboard_page),
        "Counter order": ("counter_order", staff_order_page),
        "Orders & payments": ("orders", orders_page),
        "Customer lookup": ("customers_staff", staff_customers_page),
        "Menu availability": ("menu_view", menu_browse_page),
    }
    pages = admin_pages if role == UserRole.ADMIN else staff_pages
    selected = st.sidebar.radio("Operations", list(pages))
    action, render = pages[selected]
    try:
        authorize_action(role, action)
    except PermissionError as exc:
        st.error(str(exc))
        st.stop()
    render()
