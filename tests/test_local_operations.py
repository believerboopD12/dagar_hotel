from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from app.config import DEFAULT_DATABASE_PATH, Settings
from app.db.database import create_database_engine, initialize_database, session_scope
from app.db.models import Customer, MenuItem, Order
from app.services.customers import save_customer
from app.services.exports import export_customers, export_orders, export_payments
from app.services.orders import create_order
from scripts.backup_db import create_backup
from scripts.restore_db import restore_backup


def test_configuration_falls_back_to_project_sqlite():
    assert (
        Settings(database_url="").sqlalchemy_url()
        == f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
    )


def test_file_database_initializes_persists_and_enables_foreign_keys(tmp_path):
    database = tmp_path / "restaurant.db"
    engine = create_database_engine(f"sqlite:///{database}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_scope(factory) as session:
        save_customer(session, "Local Customer", "9876543210")
    with session_scope(factory) as session:
        assert session.scalar(select(Customer).where(Customer.phone == "9876543210"))
        assert session.scalar(text("PRAGMA foreign_keys")) == 1


def test_transaction_rolls_back_complete_order_graph(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'rollback.db'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with pytest.raises(RuntimeError):
        with session_scope(factory) as session:
            customer = save_customer(session, "Rollback Customer", "9876543210")
            item = MenuItem(name="Test Meal", category="Meals", price=Decimal("250"))
            session.add(item)
            session.flush()
            create_order(session, customer.id, {item.id: 1})
            raise RuntimeError("simulated failure")
    with session_scope(factory) as session:
        assert session.scalar(select(Order)) is None
        assert session.scalar(select(Customer)) is None


def test_csv_exports_contain_expected_records(session):
    customer = save_customer(session, "Export Customer", "9876543210")
    item = MenuItem(name="Export Meal", category="Meals", price=Decimal("250"))
    session.add(item)
    session.flush()
    order = create_order(session, customer.id, {item.id: 1}, mark_paid=True)
    session.flush()
    assert b"Export Customer" in export_customers(session)
    assert order.order_number.encode() in export_orders(session)
    assert b"262.50" in export_payments(session)
    assert b"password" not in export_customers(session).lower()


def test_backup_and_confirmed_restore(tmp_path):
    source = tmp_path / "restaurant.db"
    source.write_bytes(b"sqlite-content")
    backup = create_backup(source, tmp_path / "backups", datetime(2026, 8, 20, 15, 30))
    assert backup.exists() and backup.read_bytes() == b"sqlite-content"
    destination = tmp_path / "restored.db"
    with pytest.raises(ValueError, match="confirmation"):
        restore_backup(backup, destination)
    restore_backup(backup, destination, confirm=True)
    assert destination.read_bytes() == b"sqlite-content"
