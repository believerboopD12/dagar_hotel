"""Idempotently seed the preserved restaurant menu and fictional demo customer."""

from sqlalchemy import select

from app.db.database import initialize_database, session_scope
from app.db.models import MenuItem
from app.sample_data import flattened_menu
from app.services.customers import save_customer
from app.services.menu import save_menu_item


def seed() -> None:
    initialize_database()
    with session_scope() as session:
        for name, category, price in flattened_menu():
            save_menu_item(session, name, category, price)
        if not session.scalar(select(MenuItem).limit(1)):
            raise RuntimeError("Menu seed failed")
        save_customer(session, "Demo Customer", "9876543210", "demo@example.com", "Demo address")
    print("Demo menu and customer are ready.")


if __name__ == "__main__":
    seed()
