"""Transactional order creation and state management."""

import logging
import secrets
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db.models import MenuItem, Order, OrderItem, OrderStatus, Payment, PaymentStatus
from app.services.billing import calculate_bill

logger = logging.getLogger(__name__)
PAYMENT_METHODS = {"Cash", "UPI", "Card"}
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def create_order(
    session: Session,
    customer_id: int,
    quantities: dict[int, int],
    discount: Decimal = Decimal("0"),
    payment_method: str = "Cash",
    mark_paid: bool = False,
    notes: str | None = None,
) -> Order:
    selected = {item_id: qty for item_id, qty in quantities.items() if qty}
    if not selected:
        raise ValueError("Select at least one menu item.")
    if any(not isinstance(qty, int) or qty < 1 or qty > 100 for qty in selected.values()):
        raise ValueError("Each quantity must be between 1 and 100.")
    if payment_method not in PAYMENT_METHODS:
        raise ValueError("Choose a supported payment method.")

    items = list(
        session.scalars(
            select(MenuItem).where(MenuItem.id.in_(selected), MenuItem.is_available.is_(True))
        )
    )
    if len(items) != len(selected):
        raise ValueError("One or more selected menu items are unavailable.")
    subtotal = sum((item.price * selected[item.id] for item in items), Decimal("0"))
    if subtotal < settings.minimum_order_amount:
        raise ValueError(f"Minimum order amount is ?{settings.minimum_order_amount}.")
    bill = calculate_bill(subtotal, discount, settings.tax_rate)
    order = Order(
        order_number=f"DH-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(3).upper()}",
        customer_id=customer_id,
        subtotal=bill.subtotal,
        discount=bill.discount,
        tax=bill.tax,
        total=bill.total,
        notes=notes.strip()[:500] if notes else None,
    )
    order.items.extend(
        OrderItem(
            menu_item_id=item.id,
            quantity=selected[item.id],
            unit_price=item.price,
            line_total=item.price * selected[item.id],
        )
        for item in items
    )
    order.payment = Payment(
        amount=bill.total,
        method=payment_method,
        status=PaymentStatus.PAID if mark_paid else PaymentStatus.PENDING,
        paid_at=datetime.now(UTC) if mark_paid else None,
    )
    session.add(order)
    session.flush()
    logger.info("Created order %s", order.order_number)
    return order


def update_order_status(session: Session, order_id: int, status: OrderStatus) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise ValueError("Order was not found.")
    if status not in ALLOWED_TRANSITIONS[order.status]:
        raise ValueError(f"Order cannot move from {order.status.value} to {status.value}.")
    if status == OrderStatus.COMPLETED and (
        not order.payment or order.payment.status != PaymentStatus.PAID
    ):
        raise ValueError("Record payment before completing the order.")
    if (
        status == OrderStatus.CANCELLED
        and order.payment
        and order.payment.status == PaymentStatus.PAID
    ):
        raise ValueError("Refund a paid order before cancelling it.")
    order.status = status
    logger.info("Updated order %s to %s", order.order_number, status.value)
    return order


def record_payment(session: Session, order_id: int, reference: str | None = None) -> Payment:
    order = session.get(Order, order_id)
    if not order or not order.payment:
        raise ValueError("Order payment was not found.")
    if order.status in {OrderStatus.CANCELLED, OrderStatus.COMPLETED}:
        raise ValueError(f"Payment cannot be changed for a {order.status.value} order.")
    if order.payment.status == PaymentStatus.PAID:
        raise ValueError("Payment has already been recorded.")
    if order.payment.amount != order.total or order.payment.amount <= 0:
        raise ValueError("Payment amount must exactly match the positive order total.")
    order.payment.status = PaymentStatus.PAID
    order.payment.reference = reference.strip()[:100] if reference else None
    order.payment.paid_at = datetime.now(UTC)
    logger.info("Recorded payment for order %s", order.order_number)
    return order.payment


def get_order(session: Session, order_id: int) -> Order | None:
    return session.scalar(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.customer),
            selectinload(Order.payment),
        )
        .where(Order.id == order_id)
    )
