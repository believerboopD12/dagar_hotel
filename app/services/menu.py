"""Menu item management."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MenuItem


def list_menu_items(session: Session, available_only: bool = False) -> list[MenuItem]:
    statement = select(MenuItem).order_by(MenuItem.category, MenuItem.name)
    if available_only:
        statement = statement.where(MenuItem.is_available.is_(True))
    return list(session.scalars(statement))


def save_menu_item(
    session: Session, name: str, category: str, price: Decimal, available: bool = True
) -> MenuItem:
    name, category = name.strip(), category.strip()
    if not name or not category:
        raise ValueError("Item name and category are required.")
    if Decimal(price) <= 0:
        raise ValueError("Price must be greater than zero.")
    existing = session.scalar(select(MenuItem).where(MenuItem.name == name))
    if existing:
        existing.category, existing.price, existing.is_available = (
            category,
            Decimal(price),
            available,
        )
        return existing
    item = MenuItem(name=name, category=category, price=Decimal(price), is_available=available)
    session.add(item)
    session.flush()
    return item
