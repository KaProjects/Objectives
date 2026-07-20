import json
import unittest
from decimal import Decimal

from classes import JsonEncoder


class TestJsonEncoder(unittest.TestCase):
    def test_serializes_integral_decimal_as_json_number(self):
        payload = json.dumps({'active_count': Decimal('2')}, cls=JsonEncoder)

        self.assertEqual(payload, '{"active_count": 2}')
