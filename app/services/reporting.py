"""Bounded operational queries for dashboards and order lists."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import MenuItem, Order, OrderItem, OrderStatus, Payment, PaymentStatus


def dashboard_metrics(session: Session, day: date | None = None) -> dict[str, object]:
    day = day or date.today()
    start, end = datetime.combine(day, time.min), datetime.combine(day, time.max)
    day_filter = Order.created_at.between(start, end)
    order_count = (
        session.scalar(
            select(func.count(Order.id)).where(day_filter, Order.status != OrderStatus.CANCELLED)
        )
        or 0
    )
    revenue = session.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .join(Order)
        .where(
            Payment.status == PaymentStatus.PAID,
            Payment.paid_at.between(start, end),
            Order.status != OrderStatus.CANCELLED,
        )
    ) or Decimal("0")
    active = (
        session.scalar(
            select(func.count(Order.id)).where(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.READY])
            )
        )
        or 0
    )
    completed = (
        session.scalar(
            select(func.count(Order.id)).where(day_filter, Order.status == OrderStatus.COMPLETED)
        )
        or 0
    )
    average = Decimal(revenue) / order_count if order_count else Decimal("0")
    return {
        "orders": order_count,
        "revenue": Decimal(revenue),
        "average_order": average.quantize(Decimal("0.01")),
        "active_orders": active,
        "completed_orders": completed,
    }


def recent_orders(
    session: Session, status: OrderStatus | None = None, limit: int = 100
) -> list[Order]:
    statement = (
        select(Order)
        .options(selectinload(Order.customer), selectinload(Order.payment))
        .order_by(Order.created_at.desc())
        .limit(min(max(limit, 1), 500))
    )
    if status:
        statement = statement.where(Order.status == status)
    return list(session.scalars(statement))


def popular_items(session: Session, limit: int = 5) -> list[tuple[str, int]]:
    statement = (
        select(MenuItem.name, func.sum(OrderItem.quantity).label("quantity"))
        .join(OrderItem)
        .join(Order)
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(MenuItem.id, MenuItem.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(min(max(limit, 1), 50))
    )
    return [(name, int(quantity)) for name, quantity in session.execute(statement)]
