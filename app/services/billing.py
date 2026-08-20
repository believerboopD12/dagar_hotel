"""Precise restaurant bill calculations."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MONEY = Decimal("0.01")


@dataclass(frozen=True)
class Bill:
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal


def calculate_bill(
    subtotal: Decimal, discount: Decimal = Decimal("0"), tax_rate: Decimal = Decimal("5")
) -> Bill:
    subtotal = Decimal(subtotal).quantize(MONEY, ROUND_HALF_UP)
    discount = Decimal(discount).quantize(MONEY, ROUND_HALF_UP)
    tax_rate = Decimal(tax_rate)
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative.")
    if discount < 0 or discount > subtotal:
        raise ValueError("Discount must be between zero and the subtotal.")
    if tax_rate < 0 or tax_rate > 100:
        raise ValueError("Tax rate must be between 0 and 100.")
    taxable = subtotal - discount
    tax = (taxable * tax_rate / Decimal("100")).quantize(MONEY, ROUND_HALF_UP)
    return Bill(subtotal, discount, tax, taxable + tax)
