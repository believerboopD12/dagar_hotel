from datetime import date
from decimal import Decimal

from app.db.models import MenuItem, OrderStatus
from app.services.customers import save_customer
from app.services.orders import create_order, update_order_status
from app.services.reporting import dashboard_metrics, popular_items


def test_dashboard_revenue_average_and_popular_items(session):
    customer = save_customer(session, "Report Customer", "9876543210")
    item = MenuItem(name="Popular Meal", category="Meals", price=Decimal("250"))
    session.add(item)
    session.flush()
    first = create_order(session, customer.id, {item.id: 2}, mark_paid=True)
    second = create_order(session, customer.id, {item.id: 1}, mark_paid=True)
    for order in (first, second):
        update_order_status(session, order.id, OrderStatus.PREPARING)
        update_order_status(session, order.id, OrderStatus.READY)
        update_order_status(session, order.id, OrderStatus.COMPLETED)
    metrics = dashboard_metrics(session, date.today())
    assert metrics["orders"] == 2
    assert metrics["revenue"] == Decimal("787.50")
    assert metrics["average_order"] == Decimal("393.75")
    assert metrics["completed_orders"] == 2
    assert popular_items(session) == [("Popular Meal", 3)]
