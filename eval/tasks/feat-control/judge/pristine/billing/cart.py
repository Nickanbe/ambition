"""Cart math. Money is Decimal throughout; rounding happens once, at the end."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class LineItem:
    sku: str
    unit_price: Decimal
    quantity: int = 1
    taxable: bool = True

    @property
    def amount(self):
        return self.unit_price * self.quantity


def subtotal(items):
    return sum((item.amount for item in items), Decimal("0"))


def calc_total(items, tax_rate=Decimal("0"), discount=Decimal("0")):
    """Subtotal minus discount plus tax on taxable lines, rounded to cents.

    The discount is spread across lines in proportion to their amount, so
    tax is charged on the discounted taxable amount.
    """
    gross = subtotal(items)
    if gross == 0:
        return Decimal("0.00")
    discount = min(discount, gross)
    taxable = sum((i.amount for i in items if i.taxable), Decimal("0"))
    taxable_after_discount = taxable - discount * (taxable / gross)
    total = gross - discount + taxable_after_discount * tax_rate
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
