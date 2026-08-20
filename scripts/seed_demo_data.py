"""Idempotently seed fictional local demonstration data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import initialize_database, session_scope
from app.db.models import MenuItem, User, UserRole
from app.sample_data import flattened_menu
from app.services.customers import save_customer
from app.services.menu import save_menu_item
from app.utils.security import hash_password, verify_password

# Intentionally public, fictional credentials for local development only.
DEMO_ACCOUNTS = (
    ("admin", "admin123", UserRole.ADMIN),
    ("staff", "staff123", UserRole.STAFF),
)


def seed_demo_users(session: Session, app_env: str) -> int:
    if app_env != "development":
        return 0
    created = 0
    for username, password, role in DEMO_ACCOUNTS:
        existing = session.scalar(select(User).where(User.username == username))
        if existing:
            if existing.role == role and verify_password(password, existing.password_hash):
                existing.is_demo = True
            continue
        session.add(
            User(
                username=username,
                password_hash=hash_password(password, 8),
                role=role,
                is_demo=True,
            )
        )
        created += 1
    session.flush()
    return created


def seed() -> None:
    initialize_database()
    with session_scope() as session:
        for name, category, price in flattened_menu():
            save_menu_item(session, name, category, price)
        if not session.scalar(select(MenuItem).limit(1)):
            raise RuntimeError("Menu seed failed")
        save_customer(session, "Demo Customer", "9876543210", "demo@example.com", "Demo address")
        user_count = seed_demo_users(session, settings.app_env)
    print(f"Demo data ready; {user_count} demo user(s) created.")


if __name__ == "__main__":
    seed()
