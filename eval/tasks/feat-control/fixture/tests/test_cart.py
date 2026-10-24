import unittest
from decimal import Decimal as D

from billing import LineItem, calc_total, render_invoice, subtotal


ITEMS = [
    LineItem("MUG-01", D("12.50"), 2),
    LineItem("TEE-02", D("20.00"), 1),
    LineItem("GIFT-CARD", D("25.00"), 1, taxable=False),
]


class CalcTotalTest(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal(ITEMS), D("70.00"))

    def test_no_tax(self):
        self.assertEqual(calc_total(ITEMS), D("70.00"))

    def test_tax_only_on_taxable_lines(self):
        self.assertEqual(calc_total(ITEMS, tax_rate=D("0.08")), D("73.60"))

    def test_discount_reduces_taxable_amount(self):
        self.assertEqual(calc_total(ITEMS, tax_rate=D("0.10"), discount=D("7.00")), D("67.05"))

    def test_empty_cart(self):
        self.assertEqual(calc_total([]), D("0.00"))

    def test_discount_capped(self):
        self.assertEqual(calc_total(ITEMS, discount=D("100")), D("0.00"))


class InvoiceTest(unittest.TestCase):
    def test_invoice_total_line(self):
        text = render_invoice("INV-7", ITEMS, tax_rate=D("0.08"))
        self.assertTrue(text.splitlines()[-1].endswith("73.60"))


if __name__ == "__main__":
    unittest.main()
