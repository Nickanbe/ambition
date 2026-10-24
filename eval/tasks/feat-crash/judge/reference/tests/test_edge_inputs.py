import os
import tempfile
import unittest

from ingest import load_rows, summarize


def write_tmp(text):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return path


class EdgeInputTest(unittest.TestCase):
    def load(self, text):
        path = write_tmp(text)
        try:
            return load_rows(path)
        finally:
            os.remove(path)

    def test_empty_and_blank_files(self):
        for text in ["", "\n", "   \n\n  \n", "id,amount\n", "id,amount\n\n\n"]:
            self.assertEqual(self.load(text), [], repr(text))

    def test_bom_and_crlf(self):
        rows = self.load("﻿id,amount\r\n1,5\r\n")
        self.assertEqual(rows, [{"id": 1, "amount": 5}])

    def test_ragged(self):
        self.assertEqual(self.load("a,b,c\n1,2\n"), [{"a": 1, "b": 2, "c": None}])
        with self.assertRaisesRegex(ValueError, "line 2"):
            self.load("a,b\n1,2,3\n")

    def test_summary_empty(self):
        path = write_tmp("")
        try:
            stats = summarize(path)
        finally:
            os.remove(path)
        self.assertEqual(stats, {"rows": 0, "total": 0, "mean": None, "max": None})


if __name__ == "__main__":
    unittest.main()
