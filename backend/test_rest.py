import unittest
import requests
import json
from classes import Value


origin = "http://127.0.0.1:7702"


def get_request(path):
    response = requests.get(origin + path)
    if (response.headers.get('content-type').casefold() == "application/json"):
        return response.status_code, response.json(), "Response: " + str(response.json())
    else:
        return response.status_code, str(response.content), "Response: " + str(response.content)


def assertBadUrl(self, status, error, message):
    self.assertEqual(status, 404, message)
    self.assertTrue("The requested URL was not found on the server." in error, message)


class TestApi(unittest.TestCase):
    
    def test_get_value(self):
        status, value, message = get_request("/value/1")

        self.assertEqual(status, 200, message)
        self.assertEqual(value["id"], 1, message)
        self.assertEqual(value["name"], "Zdravie", message)
        self.assertIsNotNone(value["description"], message)
        self.assertEqual(len(value["objectives"]), 0, message)
        self.assertEqual(value["active_count"], 0, message)
        self.assertEqual(value["achievements_count"], 0, message)


    def test_get_value_none(self):
        status, error, message = get_request("/value/33")

        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    
    def test_get_value_invalid_id(self):
        status, error, message = get_request("/value/x")

        self.assertEqual(status, 500, message)


    def test_get_value_no_id(self):
        status, error, message = get_request("/value")

        assertBadUrl(self, status, error, message)


    def test_get_values(self):
        status, values, message = get_request("/values")

        self.assertEqual(status, 200, message)
        self.assertEqual(len(values), 3, message)
        self.assertEqual(values[0]["name"], "Zdravie", message)





    
# NOTE: not testing external firebase db here
# class TestFirebase(unittest.TestCase):

#     def test_get_value_ideas(self):
#         status, ideas, message = get_request("/value/1/ideas")

#         self.assertEqual(status, 200, message)
#         self.assertEqual(len(ideas), 2, message)
#         self.assertEqual(ideas[0]["id"], "1234", message)


#     def test_get_value_ideas_empty(self):
#         status, ideas, message = get_request("/value/3/ideas")

#         self.assertEqual(status, 200, message)
#         self.assertEqual(len(ideas), 0, message)


if __name__ == '__main__':
    unittest.main()