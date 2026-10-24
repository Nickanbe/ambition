import copy
import json
import os
import unittest

from contacts import merge_contacts, normalize_email, normalize_phone

HERE = os.path.dirname(os.path.abspath(__file__))


def sample():
    with open(os.path.join(HERE, "..", "data", "sample.json"), encoding="utf-8") as f:
        return json.load(f)


class NormalizeTest(unittest.TestCase):
    def test_email(self):
        self.assertEqual(normalize_email(" Ada@Example.COM "), "ada@example.com")
        self.assertEqual(normalize_email(None), "")

    def test_phone(self):
        self.assertEqual(normalize_phone("+1 (555) 010-0001"), "5550100001")
        self.assertEqual(normalize_phone("555.010.0002"), "5550100002")
        self.assertEqual(normalize_phone(None), "")


class MergeTest(unittest.TestCase):
    def test_sample(self):
        merged = merge_contacts(sample())
        self.assertEqual([c["email"] for c in merged],
                         ["ada@example.com", "grace@example.com", "", "linus@example.com", ""])
        ada = merged[0]
        self.assertEqual(ada["name"], "Ada Lovelace")
        self.assertEqual(ada["tags"], ["vip", "newsletter", "beta"])
        self.assertEqual(ada["notes"], "Met at PyCon\nAsked about pricing")
        self.assertEqual(ada["count"], 2)
        grace = merged[1]
        self.assertEqual(grace["name"], "Grace Hopper")
        self.assertEqual(grace["phone"], "5550100002")
        self.assertEqual(grace["tags"], ["navy", "cobol"])
        self.assertEqual(merged[2]["count"], 1)

    def test_does_not_mutate_input(self):
        records = sample()
        before = copy.deepcopy(records)
        merge_contacts(records)
        self.assertEqual(records, before)

    def test_empty(self):
        self.assertEqual(merge_contacts([]), [])


if __name__ == "__main__":
    unittest.main()
