from pathlib import Path

from sqlalchemy import select

from app.db.models import User, UserRole
from app.services.auth import authenticate_user, authorize_action
from app.utils.assets import ASSET_ROOT, ITEM_IMAGES, resolve_menu_image
from scripts.seed_demo_data import seed_demo_users


def test_demo_users_are_hashed_authentic_and_idempotent(session):
    assert seed_demo_users(session, "development") == 2
    session.flush()
    assert seed_demo_users(session, "development") == 0
    users = {user.username: user for user in session.scalars(select(User))}
    assert users["admin"].role == UserRole.ADMIN
    assert users["staff"].role == UserRole.STAFF
    assert users["admin"].password_hash != "admin123"
    assert users["staff"].password_hash != "staff123"
    assert authenticate_user(session, "admin", "admin123").role == UserRole.ADMIN
    assert authenticate_user(session, "staff", "staff123").role == UserRole.STAFF
    assert authenticate_user(session, "admin", "admin123", "production") is None
    assert users["admin"].is_demo and users["staff"].is_demo
    assert authenticate_user(session, "admin", "wrong") is None


def test_production_does_not_seed_demo_users(session):
    assert seed_demo_users(session, "production") == 0
    assert list(session.scalars(select(User))) == []


def test_role_authorization():
    authorize_action(UserRole.ADMIN, "menu_admin")
    authorize_action(UserRole.STAFF, "counter_order")
    try:
        authorize_action(UserRole.STAFF, "menu_admin")
    except PermissionError:
        pass
    else:
        raise AssertionError("Staff received admin-only permission")


def test_known_and_missing_images_resolve_portably():
    known = resolve_menu_image("Tea", "Sides & Drinks")
    fallback = resolve_menu_image("Unknown Item", "Curries")
    assert known.name == "chai.jpg" and known.is_file()
    assert fallback.name == "generic-curry.webp" and fallback.is_file()
    assert ASSET_ROOT in known.parents and ASSET_ROOT in fallback.parents
    assert all(not Path(value).is_absolute() for value in ITEM_IMAGES.values())
