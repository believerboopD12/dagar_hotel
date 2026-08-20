"""Customer creation, updates, and search."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Customer
from app.utils.validation import clean_name, validate_email, validate_phone


def save_customer(
    session: Session, name: str, phone: str, email: str | None = None, address: str | None = None
) -> Customer:
    phone = validate_phone(phone)
    values = {
        "name": clean_name(name),
        "email": validate_email(email),
        "address": address.strip() if address else None,
    }
    customer = session.scalar(select(Customer).where(Customer.phone == phone))
    if customer:
        customer.name, customer.email, customer.address = (
            values["name"],
            values["email"],
            values["address"],
        )
        return customer
    customer = Customer(phone=phone, **values)
    session.add(customer)
    try:
        session.flush()
    except IntegrityError as exc:
        raise ValueError("A customer with this phone or email already exists.") from exc
    return customer


def search_customers(session: Session, query: str = "", limit: int = 100) -> list[Customer]:
    statement = select(Customer).order_by(Customer.created_at.desc()).limit(limit)
    if query.strip():
        term = f"%{query.strip()}%"
        statement = statement.where(
            or_(Customer.name.ilike(term), Customer.phone.ilike(term), Customer.email.ilike(term))
        )
    return list(session.scalars(statement))
