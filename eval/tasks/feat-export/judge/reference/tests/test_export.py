import csv
import io
import unittest
from decimal import Decimal
import datetime

from report.export import write_csv


class ExportTest(unittest.TestCase):
    def test_roundtrip_and_injection(self):
        rows = [
            {"customer": 'A "q", b\nc', "region": "EU", "orders": 1, "revenue": Decimal("-1.50"),
             "last_order": datetime.date(2026, 1, 2)},
            {"customer": "=1+1", "region": "NA", "orders": 2, "revenue": Decimal("3"),
             "last_order": datetime.date(2026, 1, 3)},
        ]
        buf = io.StringIO()
        write_csv(rows, buf)
        parsed = list(csv.reader(io.StringIO(buf.getvalue(), newline="")))
        self.assertEqual(parsed[0], ["customer", "region", "orders", "revenue", "last_order"])
        self.assertEqual(parsed[1], ['A "q", b\nc', "EU", "1", "-1.50", "2026-01-02"])
        self.assertEqual(parsed[2][0], "'=1+1")


if __name__ == "__main__":
    unittest.main()
