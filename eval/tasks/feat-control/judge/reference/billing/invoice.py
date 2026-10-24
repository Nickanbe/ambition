"""Plain-text invoices."""

from decimal import Decimal

from .cart import compute_total, subtotal


def render_invoice(number, items, tax_rate=Decimal("0"), discount=Decimal("0")):
    lines = [f"Invoice {number}", ""]
    for item in items:
        lines.append(f"{item.sku:<12} {item.quantity:>3} x {item.unit_price:>8}  {item.amount:>9}")
    lines.append("")
    lines.append(f"{'Subtotal':<28}{subtotal(items):>9}")
    if discount:
        lines.append(f"{'Discount':<28}{-discount:>9}")
    total = compute_total(items, tax_rate=tax_rate, discount=discount)
    lines.append(f"{'Total':<28}{total:>9}")
    return "\n".join(lines)
