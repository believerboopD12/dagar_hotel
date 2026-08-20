"""Operator-facing Streamlit pages."""

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from app.db.database import session_scope
from app.db.models import OrderStatus
from app.services.customers import save_customer, search_customers
from app.services.exports import export_customers, export_orders, export_payments
from app.services.menu import list_menu_items, save_menu_item
from app.services.orders import create_order, record_payment, update_order_status
from app.services.reporting import dashboard_metrics, popular_items, recent_orders


def money(value: Decimal) -> str:
    return f"INR {value:,.2f}"


def _orders_frame(orders: list) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Order": o.order_number,
                "Customer": o.customer.name,
                "Status": o.status.value.title(),
                "Total": money(o.total),
                "Payment": o.payment.status.value.title() if o.payment else "Missing",
                "Created": o.created_at.strftime("%d %b %Y %H:%M"),
            }
            for o in orders
        ]
    )


def dashboard_page() -> None:
    st.header("Operations dashboard")
    selected_day = st.date_input("Business date", date.today())
    with session_scope() as session:
        metrics, recent, popular = (
            dashboard_metrics(session, selected_day),
            recent_orders(session, limit=10),
            popular_items(session),
        )
    cols = st.columns(5)
    cols[0].metric("Orders", metrics["orders"])
    cols[1].metric("Paid revenue", money(metrics["revenue"]))
    cols[2].metric("Average order", money(metrics["average_order"]))
    cols[3].metric("Active orders", metrics["active_orders"])
    cols[4].metric("Completed", metrics["completed_orders"])
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Recent orders")
        st.dataframe(
            _orders_frame(recent), hide_index=True, use_container_width=True
        ) if recent else st.info("No orders have been recorded.")
    with right:
        st.subheader("Popular items")
        if popular:
            st.bar_chart(pd.DataFrame(popular, columns=["Item", "Quantity"]).set_index("Item"))
        else:
            st.caption("Item popularity appears after orders are created.")


def customer_page() -> None:
    st.header("Customers")
    with st.form("customer"):
        name, phone = st.text_input("Name *"), st.text_input("Mobile number *", max_chars=12)
        email, address = st.text_input("Email"), st.text_area("Address", max_chars=500)
        submitted = st.form_submit_button("Save customer", type="primary")
    if submitted:
        try:
            with session_scope() as session:
                customer = save_customer(session, name, phone, email, address)
                customer_id = customer.id
            st.success(f"Customer saved (ID {customer_id}).")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Customer could not be saved. Check the database connection.")
    query = st.text_input("Search by name, mobile, or email")
    with session_scope() as session:
        customers = search_customers(session, query)
        customer_csv = export_customers(session)
    st.download_button("Download customers CSV", customer_csv, "customers.csv", "text/csv")
    st.dataframe(
        [
            {
                "ID": c.id,
                "Name": c.name,
                "Mobile": c.phone,
                "Email": c.email or "",
                "Address": c.address or "",
            }
            for c in customers
        ],
        hide_index=True,
        use_container_width=True,
    )


def new_order_page() -> None:
    st.header("Create order")
    with session_scope() as session:
        customers, menu_items = (
            search_customers(session, limit=200),
            list_menu_items(session, available_only=True),
        )
    if not customers or not menu_items:
        st.info("Add a customer and available menu items before creating an order.")
        return
    labels = {f"{c.name} ? {c.phone}": c.id for c in customers}
    customer_label = st.selectbox("Customer", labels)
    quantities = {}
    for category in sorted({item.category for item in menu_items}):
        with st.expander(category, expanded=True):
            columns = st.columns(2)
            for index, item in enumerate(i for i in menu_items if i.category == category):
                quantities[item.id] = columns[index % 2].number_input(
                    f"{item.name} ? {money(item.price)}",
                    min_value=0,
                    max_value=100,
                    key=f"qty_{item.id}",
                )
    discount = st.number_input("Discount (?)", min_value=0.0, step=10.0)
    payment_method, mark_paid = (
        st.selectbox("Payment method", ["Cash", "UPI", "Card"]),
        st.checkbox("Payment received"),
    )
    notes = st.text_area("Kitchen/order notes", max_chars=500)
    if st.button("Create order", type="primary"):
        try:
            with session_scope() as session:
                order = create_order(
                    session,
                    labels[customer_label],
                    quantities,
                    Decimal(str(discount)),
                    payment_method,
                    mark_paid,
                    notes,
                )
                order_number, total = order.order_number, order.total
            st.success(f"Order {order_number} created. Total: {money(total)}")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("The order could not be created. No partial order was saved.")


def orders_page() -> None:
    st.header("Orders & payments")
    status_label = st.selectbox(
        "Status filter", ["All", *[status.value.title() for status in OrderStatus]]
    )
    selected_status = None if status_label == "All" else OrderStatus(status_label.lower())
    with session_scope() as session:
        orders = recent_orders(session, selected_status, 200)
        orders_csv = export_orders(session)
        payments_csv = export_payments(session)
    st.download_button("Download orders CSV", orders_csv, "orders.csv", "text/csv")
    st.download_button("Download payments CSV", payments_csv, "payments.csv", "text/csv")
    if not orders:
        st.info("No matching orders.")
        return
    st.dataframe(_orders_frame(orders), hide_index=True, use_container_width=True)
    order_map = {f"{o.order_number} ? {o.customer.name}": o.id for o in orders}
    selected = st.selectbox("Manage order", order_map)
    col1, col2 = st.columns(2)
    with col1:
        new_status = st.selectbox("New status", [s.value.title() for s in OrderStatus])
        if st.button("Update status"):
            try:
                with session_scope() as session:
                    update_order_status(
                        session, order_map[selected], OrderStatus(new_status.lower())
                    )
                st.success("Order status updated.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with col2:
        reference = st.text_input("Payment reference (optional)")
        if st.button("Mark paid"):
            try:
                with session_scope() as session:
                    record_payment(session, order_map[selected], reference)
                st.success("Payment recorded.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def menu_page() -> None:
    st.header("Menu management")
    with st.form("menu_item"):
        name, category = st.text_input("Item name"), st.text_input("Category")
        price, available = (
            st.number_input("Price (?)", min_value=1.0, step=5.0),
            st.checkbox("Available", value=True),
        )
        submitted = st.form_submit_button("Add or update item", type="primary")
    if submitted:
        try:
            with session_scope() as session:
                save_menu_item(session, name, category, Decimal(str(price)), available)
            st.success("Menu item saved.")
        except ValueError as exc:
            st.error(str(exc))
    with session_scope() as session:
        items = list_menu_items(session)
    st.dataframe(
        [
            {
                "ID": i.id,
                "Category": i.category,
                "Item": i.name,
                "Price": money(i.price),
                "Available": i.is_available,
            }
            for i in items
        ],
        hide_index=True,
        use_container_width=True,
    )
