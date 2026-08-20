from decimal import Decimal

import pytest

from app.db.models import MenuItem, OrderStatus, PaymentStatus
from app.services.customers import save_customer
from app.services.orders import create_order, record_payment, update_order_status


@pytest.fixture
def order_data(session):
    customer = save_customer(session, "Demo Customer", "9876543210")
    item = MenuItem(name="Paneer", category="Curries", price=Decimal("200"), is_available=True)
    session.add(item)
    session.flush()
    return customer, item


def test_valid_order_calculates_lines_and_payment(session, order_data):
    customer, item = order_data
    order = create_order(session, customer.id, {item.id: 2}, Decimal("20"), "UPI", True)
    assert order.subtotal == Decimal("400.00")
    assert order.total == Decimal("399.00")
    assert order.items[0].quantity == 2
    assert order.payment.status == PaymentStatus.PAID
    assert order.status == OrderStatus.PENDING


@pytest.mark.parametrize("quantity", [-1, 0, 101, 1.5])
def test_order_rejects_invalid_quantity(session, order_data, quantity):
    customer, item = order_data
    with pytest.raises(ValueError):
        create_order(session, customer.id, {item.id: quantity})


def test_order_rejects_unavailable_item(session, order_data):
    customer, item = order_data
    item.is_available = False
    with pytest.raises(ValueError, match="unavailable"):
        create_order(session, customer.id, {item.id: 1})


def test_order_rejects_below_minimum(session, order_data):
    customer, item = order_data
    item.price = Decimal("100")
    with pytest.raises(ValueError, match="Minimum"):
        create_order(session, customer.id, {item.id: 1})


def test_valid_state_machine_and_completion(session, order_data):
    customer, item = order_data
    order = create_order(session, customer.id, {item.id: 1})
    update_order_status(session, order.id, OrderStatus.PREPARING)
    update_order_status(session, order.id, OrderStatus.READY)
    with pytest.raises(ValueError, match="payment"):
        update_order_status(session, order.id, OrderStatus.COMPLETED)
    record_payment(session, order.id)
    update_order_status(session, order.id, OrderStatus.COMPLETED)
    assert order.status == OrderStatus.COMPLETED


@pytest.mark.parametrize("target", [OrderStatus.READY, OrderStatus.COMPLETED])
def test_invalid_transition_from_pending(session, order_data, target):
    customer, item = order_data
    order = create_order(session, customer.id, {item.id: 1})
    with pytest.raises(ValueError, match="cannot move"):
        update_order_status(session, order.id, target)


def test_completed_order_is_terminal(session, order_data):
    customer, item = order_data
    order = create_order(session, customer.id, {item.id: 1}, mark_paid=True)
    update_order_status(session, order.id, OrderStatus.PREPARING)
    update_order_status(session, order.id, OrderStatus.READY)
    update_order_status(session, order.id, OrderStatus.COMPLETED)
    with pytest.raises(ValueError, match="cannot move"):
        update_order_status(session, order.id, OrderStatus.PREPARING)


def test_payment_cannot_be_recorded_twice(session, order_data):
    customer, item = order_data
    order = create_order(session, customer.id, {item.id: 1})
    record_payment(session, order.id)
    with pytest.raises(ValueError, match="already"):
        record_payment(session, order.id)
