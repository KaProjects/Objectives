import unittest
import requests
import json
from classes import Value


origin = "http://127.0.0.1:7702"


def get_request(path):
    response = requests.get(origin + path)
    return response.status_code, response.json(), "Response: " + str(response.json())


class TestApi(unittest.TestCase):
    
    def test_value_get(self):
        status, value, message = get_request("/value/1")

        self.assertEqual(status, 200, message)
        self.assertEqual(value["id"], 1, message)
        self.assertEqual(value["name"], "Zdravie", message)
        self.assertIsNotNone(value["description"], message)
        self.assertEqual(len(value["objectives"]), 0, message)
        self.assertEqual(value["active_count"], 0, message)
        self.assertEqual(value["achievements_count"], 0, message)


    def test_value_get_none(self):
        status, error, message = get_request("/value/3")

        self.assertEqual(status, 404, message)
        self.assertTrue("id '3' not found" in error, message)










if __name__ == '__main__':
    unittest.main()