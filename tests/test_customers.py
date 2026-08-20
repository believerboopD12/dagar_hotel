import pytest

from app.services.customers import save_customer


def test_customer_create_and_update(session):
    customer = save_customer(session, "  Demo   Customer ", "98765-43210", "Demo@Example.COM")
    session.flush()
    same_customer = save_customer(session, "Updated Customer", "9876543210")
    assert customer.id == same_customer.id
    assert same_customer.name == "Updated Customer"


@pytest.mark.parametrize("phone", ["123", "1234567890", "abcdefghij"])
def test_customer_rejects_invalid_phone(session, phone):
    with pytest.raises(ValueError):
        save_customer(session, "Valid Name", phone)


def test_customer_rejects_duplicate_email(session):
    save_customer(session, "First Person", "9876543210", "same@example.com")
    session.flush()
    with pytest.raises(ValueError, match="already exists"):
        save_customer(session, "Second Person", "9876543211", "same@example.com")
