import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dates import normalize_date, validate_iso_date


class TestDates(unittest.TestCase):
    def test_normalize_legacy_date(self):
        self.assertEqual(normalize_date('15/07/2026'), '2026-07-15')

    def test_normalize_rejects_malformed_legacy_date(self):
        with self.assertRaises(ValueError):
            normalize_date('15-07-2026')

    def test_validate_requires_iso_date(self):
        self.assertEqual(validate_iso_date('2026-07-15'), '2026-07-15')
        with self.assertRaises(ValueError):
            validate_iso_date('15/07/2026')

    def test_validate_allows_an_empty_optional_date(self):
        self.assertEqual(validate_iso_date('', allow_empty=True), '')
