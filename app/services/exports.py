"""Reusable, secret-free CSV exports."""

import csv
import io
from collections.abc import Iterable
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Customer, Order, Payment


def _csv_bytes(headers: list[str], rows: Iterable[Iterable[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def export_customers(session: Session) -> bytes:
    customers = session.scalars(select(Customer).order_by(Customer.id))
    return _csv_bytes(
        ["customer_id", "name", "phone", "email", "address", "created_at"],
        ((c.id, c.name, c.phone, c.email or "", c.address or "", c.created_at) for c in customers),
    )


def export_orders(session: Session, day: date | None = None) -> bytes:
    statement = (
        select(Order)
        .options(selectinload(Order.customer), selectinload(Order.payment))
        .order_by(Order.created_at)
    )
    if day:
        statement = statement.where(
            Order.created_at.between(
                datetime.combine(day, time.min), datetime.combine(day, time.max)
            )
        )
    orders = session.scalars(statement)
    return _csv_bytes(
        [
            "order_number",
            "customer",
            "status",
            "subtotal",
            "discount",
            "tax",
            "total",
            "payment_status",
            "created_at",
        ],
        (
            (
                o.order_number,
                o.customer.name,
                o.status.value,
                o.subtotal,
                o.discount,
                o.tax,
                o.total,
                o.payment.status.value if o.payment else "",
                o.created_at,
            )
            for o in orders
        ),
    )


def export_payments(session: Session) -> bytes:
    payments = session.scalars(select(Payment).order_by(Payment.created_at))
    return _csv_bytes(
        ["payment_id", "order_id", "amount", "method", "status", "reference", "paid_at"],
        (
            (
                p.id,
                p.order_id,
                p.amount,
                p.method,
                p.status.value,
                p.reference or "",
                p.paid_at or "",
            )
            for p in payments
        ),
    )
