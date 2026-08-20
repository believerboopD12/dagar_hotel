from decimal import Decimal

import pytest

from app.services.menu import list_menu_items, save_menu_item
from app.utils.logging import configure_logging
from app.utils.security import hash_password, verify_password


def test_menu_create_update_filter_and_validation(session):
    item = save_menu_item(session, "Tea", "Drinks", Decimal("20"))
    session.flush()
    same = save_menu_item(session, "Tea", "Beverages", Decimal("25"), False)
    assert same.id == item.id
    assert same.price == Decimal("25")
    assert list_menu_items(session) == [same]
    assert list_menu_items(session, available_only=True) == []
    with pytest.raises(ValueError, match="required"):
        save_menu_item(session, "", "Drinks", Decimal("20"))
    with pytest.raises(ValueError, match="greater"):
        save_menu_item(session, "Water", "Drinks", Decimal("0"))


def test_password_hashing_and_verification():
    encoded = hash_password("strong-password")
    assert "strong-password" not in encoded
    assert verify_password("strong-password", encoded)
    assert not verify_password("wrong-password", encoded)
    assert not verify_password("anything", "invalid")
    with pytest.raises(ValueError, match="10"):
        hash_password("short")


def test_logging_configuration_accepts_unknown_level():
    configure_logging("NOT_A_LEVEL")
