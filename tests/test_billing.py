from decimal import Decimal

import pytest

from app.services.billing import calculate_bill


def test_bill_calculates_discount_tax_and_total():
    bill = calculate_bill(Decimal("500"), Decimal("50"), Decimal("5"))
    assert bill.subtotal == Decimal("500.00")
    assert bill.tax == Decimal("22.50")
    assert bill.total == Decimal("472.50")


@pytest.mark.parametrize("subtotal,discount", [("-1", "0"), ("100", "-1"), ("100", "101")])
def test_bill_rejects_invalid_amounts(subtotal, discount):
    with pytest.raises(ValueError):
        calculate_bill(Decimal(subtotal), Decimal(discount))
