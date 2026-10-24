import os
import tempfile
import unittest

from ingest import load_rows, summarize

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "..", "data", "payments.csv")


def write_tmp(text):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return path


class LoadRowsTest(unittest.TestCase):
    def test_sample_file(self):
        rows = load_rows(SAMPLE)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["customer"], "Northwind Traders")
        self.assertEqual(rows[0]["id"], 1001)

    def test_coercion(self):
        rows = load_rows(SAMPLE)
        self.assertEqual(rows[1]["amount"], 99.5)
        self.assertEqual(rows[3]["amount"], 1200)
        self.assertIsNone(rows[2]["amount"])
        self.assertEqual(rows[4]["amount"], 42.10)

    def test_other_delimiter(self):
        path = write_tmp("a;b\n1;x\n2;y\n")
        try:
            rows = load_rows(path, delimiter=";")
        finally:
            os.remove(path)
        self.assertEqual(rows, [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])

    def test_quoted_commas(self):
        path = write_tmp('name,amount\n"Smith, J",10\n')
        try:
            rows = load_rows(path)
        finally:
            os.remove(path)
        self.assertEqual(rows, [{"name": "Smith, J", "amount": 10}])


class SummaryTest(unittest.TestCase):
    def test_summary(self):
        stats = summarize(SAMPLE)
        self.assertEqual(stats["rows"], 5)
        self.assertAlmostEqual(stats["total"], 1591.6)
        self.assertEqual(stats["max"], 1200)


if __name__ == "__main__":
    unittest.main()
