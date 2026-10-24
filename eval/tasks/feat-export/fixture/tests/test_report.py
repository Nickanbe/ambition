import datetime
import io
import os
import unittest
from contextlib import redirect_stdout
from decimal import Decimal

from report.__main__ import main
from report.build import build_report
from report.data import load_orders
from report.render import render_table

HERE = os.path.dirname(os.path.abspath(__file__))
ORDERS = os.path.join(HERE, "..", "data", "orders.csv")


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.orders = load_orders(ORDERS)

    def test_totals(self):
        rows = build_report(self.orders)
        self.assertEqual(rows[0]["customer"], "Adventure Works Cycles International")
        northwind = next(r for r in rows if r["customer"] == "Northwind Traders")
        self.assertEqual(northwind["orders"], 3)
        self.assertEqual(northwind["revenue"], Decimal("1979.99"))
        self.assertEqual(northwind["last_order"], datetime.date(2026, 9, 10))

    def test_refund_nets_out(self):
        fabrikam = next(r for r in build_report(self.orders) if r["customer"] == "Fabrikam")
        self.assertEqual(fabrikam["revenue"], Decimal("2250.00"))

    def test_filters(self):
        rows = build_report(self.orders, region="EU", since=datetime.date(2026, 8, 1))
        self.assertEqual([r["customer"] for r in rows], ["Tailspin Toys", "Café Lumière", "Contoso Ltd"])


class CliTest(unittest.TestCase):
    def test_table(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main([ORDERS]), 0)
        out = buf.getvalue()
        self.assertIn("Customer", out.splitlines()[0])
        self.assertIn("$5,300.00", out)
        self.assertIn("Adventure Works Cycle…", out)
        self.assertIn("7 customers", out)

    def test_render_empty(self):
        self.assertIn("0 customers", render_table([]))


if __name__ == "__main__":
    unittest.main()
