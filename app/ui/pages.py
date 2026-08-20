"""Role-appropriate Streamlit pages for customers and restaurant staff."""

from decimal import Decimal

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.database import session_scope
from app.db.models import Customer, Order, OrderStatus
from app.services.billing import calculate_bill
from app.services.customers import save_customer, search_customers
from app.services.exports import export_customers, export_orders, export_payments
from app.services.menu import list_menu_items, save_menu_item
from app.services.orders import create_order, record_payment, update_order_status
from app.services.reporting import dashboard_metrics, popular_items, recent_orders
from app.utils.assets import resolve_menu_image
from app.utils.validation import validate_phone


def money(value: Decimal) -> str:
    return f"₹{value:,.2f}"


def _quantity_inputs(menu_items: list, key_prefix: str) -> dict[int, int]:
    st.markdown(
        """
        <style>
        div[data-testid="stImage"] img {
            aspect-ratio: 3 / 2;
            object-fit: cover;
            border-radius: 0.55rem;
        }
        div[data-testid="stNumberInput"] { margin-bottom: 0.15rem; }
        div[data-testid="stVerticalBlockBorderWrapper"] { background: #fffdfa; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    quantities: dict[int, int] = {}
    categories = sorted({item.category for item in menu_items})
    for category, tab in zip(categories, st.tabs(categories), strict=True):
        category_items = [item for item in menu_items if item.category == category]
        grouped: dict[str, list] = {}
        for item in category_items:
            display_name = item.name
            for suffix in (" (Half)", " (Full)"):
                if display_name.endswith(suffix):
                    display_name = display_name.removesuffix(suffix)
                    break
            grouped.setdefault(display_name, []).append(item)

        with tab:
            columns = st.columns(3, gap="small")
            for index, (display_name, variants) in enumerate(grouped.items()):
                with columns[index % 3]:
                    with st.container(border=True):
                        first = variants[0]
                        st.image(
                            str(resolve_menu_image(first.name, first.category)),
                            use_container_width=True,
                        )
                        st.markdown(f"**{display_name}**")
                        controls = st.columns(len(variants), gap="small")
                        for control, item in zip(controls, variants, strict=True):
                            variant = ""
                            if item.name.endswith(" (Half)"):
                                variant = "Half · "
                            elif item.name.endswith(" (Full)"):
                                variant = "Full · "
                            with control:
                                quantities[item.id] = st.number_input(
                                    f"{variant}{money(item.price)}",
                                    min_value=0,
                                    max_value=100,
                                    key=f"{key_prefix}_{item.id}",
                                )
    return quantities


def _bill_preview(menu_items: list, quantities: dict[int, int], discount: Decimal) -> None:
    subtotal = sum((item.price * quantities.get(item.id, 0) for item in menu_items), Decimal("0"))
    if subtotal:
        try:
            bill = calculate_bill(subtotal, discount, settings.tax_rate)
            cols = st.columns(4)
            cols[0].metric("Subtotal", money(bill.subtotal))
            cols[1].metric("Discount", money(bill.discount))
            cols[2].metric(f"Tax ({settings.tax_rate}%)", money(bill.tax))
            cols[3].metric("Total", money(bill.total))
        except ValueError as exc:
            st.warning(str(exc))


def customer_order_page() -> None:
    st.header("Place your order")
    st.caption("Choose items and enter your own contact details. Restaurant staff confirm payment.")
    with session_scope() as session:
        menu_items = list_menu_items(session, available_only=True)
    if not menu_items:
        st.info("The menu is currently unavailable. Please contact restaurant staff.")
        return
    quantities = _quantity_inputs(menu_items, "customer_qty")
    _bill_preview(menu_items, quantities, Decimal("0"))
    with st.form("customer_checkout"):
        st.subheader("Your details")
        name = st.text_input("Name *")
        phone = st.text_input("Mobile number *", max_chars=12)
        email = st.text_input("Email (optional)")
        address = st.text_area("Delivery/table details", max_chars=500)
        payment_method = st.selectbox("Preferred payment method", ["Cash", "UPI", "Card"])
        notes = st.text_area("Order notes", max_chars=500)
        submitted = st.form_submit_button("Place order", type="primary")
    if submitted:
        try:
            with session_scope() as session:
                customer = save_customer(
                    session, name, phone, email, address, update_existing=False
                )
                order = create_order(
                    session,
                    customer.id,
                    quantities,
                    payment_method=payment_method,
                    mark_paid=False,
                    notes=notes,
                )
                number, total = order.order_number, order.total
            st.success(
                f"Order {number} placed. Total: {money(total)}. "
                "Payment will remain pending until restaurant staff confirm it."
            )
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Your order could not be placed. No partial order was saved.")


def track_order_page() -> None:
    st.header("Track your order")
    order_number = st.text_input("Order number", placeholder="DH-YYYYMMDD-XXXXXX")
    phone = st.text_input("Mobile number", max_chars=12, key="tracking_phone")
    if not order_number or not phone:
        st.info("Enter both the order number and mobile number used at checkout.")
        return
    try:
        normalized_phone = validate_phone(phone)
        with session_scope() as session:
            order = session.scalar(
                select(Order)
                .join(Customer)
                .options(selectinload(Order.payment))
                .where(
                    Customer.phone == normalized_phone,
                    Order.order_number == order_number.strip().upper(),
                )
            )
        if not order:
            st.info("No matching order was found. Check both values and try again.")
            return
        cols = st.columns(3)
        cols[0].metric("Status", order.status.value.title())
        cols[1].metric("Payment", order.payment.status.value.title())
        cols[2].metric("Total", money(order.total))
        st.caption(f"Placed: {order.created_at:%d %b %Y %H:%M}")
    except ValueError as exc:
        st.error(str(exc))


def _orders_frame(orders: list[Order]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Order": order.order_number,
                "Customer": order.customer.name,
                "Status": order.status.value.title(),
                "Total": money(order.total),
                "Payment": order.payment.status.value.title(),
                "Created": order.created_at.strftime("%d %b %Y %H:%M"),
            }
            for order in orders
        ]
    )


def dashboard_page() -> None:
    st.header("Staff dashboard")
    selected_day = st.date_input("Business date")
    with session_scope() as session:
        metrics = dashboard_metrics(session, selected_day)
        recent = recent_orders(session, limit=10)
        popular = popular_items(session)
    cols = st.columns(5)
    cols[0].metric("Orders", metrics["orders"])
    cols[1].metric("Paid revenue", money(metrics["revenue"]))
    cols[2].metric("Average order", money(metrics["average_order"]))
    cols[3].metric("Active", metrics["active_orders"])
    cols[4].metric("Completed", metrics["completed_orders"])
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Recent orders")
        if recent:
            st.dataframe(_orders_frame(recent), hide_index=True, use_container_width=True)
        else:
            st.info("No orders have been recorded.")
    with right:
        st.subheader("Popular items")
        if popular:
            st.bar_chart(pd.DataFrame(popular, columns=["Item", "Quantity"]).set_index("Item"))
        else:
            st.caption("Popularity appears after orders are created.")


def customer_management_page() -> None:
    st.header("Customer management")
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


def staff_order_page() -> None:
    st.header("Create staff order")
    st.caption("Counter staff can authorize discounts and confirm received payments.")
    with session_scope() as session:
        customers = search_customers(session, limit=200)
        menu_items = list_menu_items(session, available_only=True)
    if not customers or not menu_items:
        st.info("A customer and available menu item are required.")
        return
    labels = {f"{c.name} - {c.phone}": c.id for c in customers}
    customer_label = st.selectbox("Customer", labels)
    quantities = _quantity_inputs(menu_items, "staff_qty")
    discount_value = st.number_input(
        "Authorized discount (INR)",
        min_value=0.0,
        step=10.0,
        help="Only staff can apply a discount. It is validated against the subtotal.",
    )
    discount = Decimal(str(discount_value))
    _bill_preview(menu_items, quantities, discount)
    payment_method = st.selectbox("Payment method", ["Cash", "UPI", "Card"])
    mark_paid = st.checkbox("Staff confirms payment received")
    notes = st.text_area("Kitchen/order notes", max_chars=500)
    if st.button("Create staff order", type="primary"):
        try:
            with session_scope() as session:
                order = create_order(
                    session,
                    labels[customer_label],
                    quantities,
                    discount,
                    payment_method,
                    mark_paid,
                    notes,
                )
                number, total = order.order_number, order.total
            st.success(f"Order {number} created. Total: {money(total)}")
        except ValueError as exc:
            st.error(str(exc))


def orders_page() -> None:
    st.header("Orders and payments")
    status_label = st.selectbox("Status filter", ["All", *[s.value.title() for s in OrderStatus]])
    selected_status = None if status_label == "All" else OrderStatus(status_label.lower())
    with session_scope() as session:
        orders = recent_orders(session, selected_status, 200)
        orders_csv, payments_csv = export_orders(session), export_payments(session)
    download_cols = st.columns(2)
    download_cols[0].download_button("Download orders CSV", orders_csv, "orders.csv", "text/csv")
    download_cols[1].download_button(
        "Download payments CSV", payments_csv, "payments.csv", "text/csv"
    )
    if not orders:
        st.info("No matching orders.")
        return
    st.dataframe(_orders_frame(orders), hide_index=True, use_container_width=True)
    order_map = {f"{o.order_number} - {o.customer.name}": o.id for o in orders}
    selected = st.selectbox("Manage order", order_map)
    status_col, payment_col = st.columns(2)
    with status_col:
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
    with payment_col:
        reference = st.text_input("Payment reference (optional)")
        if st.button("Confirm payment received"):
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
        price = st.number_input("Price (INR)", min_value=1.0, step=5.0)
        available = st.checkbox("Available", value=True)
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


def staff_customers_page() -> None:
    st.header("Customer lookup")
    with st.form("staff_customer"):
        name = st.text_input("Name")
        phone = st.text_input("Mobile number", max_chars=12)
        submitted = st.form_submit_button("Create or update customer")
    if submitted:
        try:
            with session_scope() as session:
                save_customer(session, name, phone)
            st.success("Customer saved.")
        except ValueError as exc:
            st.error(str(exc))
    query = st.text_input("Search customers")
    with session_scope() as session:
        customers = search_customers(session, query, limit=100)
    st.dataframe(
        [{"Name": c.name, "Mobile": c.phone} for c in customers],
        hide_index=True,
        use_container_width=True,
    )


def menu_browse_page() -> None:
    st.header("Menu availability")
    with session_scope() as session:
        items = list_menu_items(session)
    for category in sorted({item.category for item in items}):
        st.subheader(category)
        columns = st.columns(3)
        for index, item in enumerate(i for i in items if i.category == category):
            with columns[index % 3]:
                st.image(str(resolve_menu_image(item.name, item.category)), width=140)
                st.write(item.name)
                status = "Available" if item.is_available else "Unavailable"
                st.caption(f"{money(item.price)} - {status}")
