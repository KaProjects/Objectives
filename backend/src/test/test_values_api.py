import unittest

from utils import get_request, assert_bad_url


class TestValuesApi(unittest.TestCase):

    def test_get_value(self):
        status, value, message = get_request("/value/1")

        self.assertEqual(status, 200, message)
        self.assertEqual(value["id"], 1, message)
        self.assertEqual(value["name"], "Zdravie", message)
        self.assertIsNotNone(value["description"], message)
        self.assertEqual(len(value["objectives"]), 0, message)
        self.assertEqual(value["active_count"], 0, message)
        self.assertEqual(value["achievements_count"], 0, message)

    def test_get_value_with_children(self):
        status, value, message = get_request("/value/3")

        self.assertEqual(status, 200, message)
        self.assertEqual(value["id"], 3, message)
        self.assertEqual(value["name"], "Third", message)
        self.assertEqual(value["active_count"], 1, message)
        self.assertEqual(value["achievements_count"], 1, message)
        self.assertEqual(value["objectives"][0]["id"], 1, message)
        self.assertEqual(value["objectives"][0]["state"], "achieved", message)
        self.assertEqual(len(value["objectives"][0]["key_results"]), 1, message)
        self.assertEqual(value["objectives"][0]["key_results"][0]["state"], "completed", message)
        self.assertEqual(value["objectives"][0]["key_results"][0]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][0]["key_results"][0]["resolved_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["id"], 2, message)
        self.assertEqual(value["objectives"][1]["state"], "active", message)
        self.assertEqual(len(value["objectives"][1]["key_results"]), 3, message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["state"], "completed", message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["resolved_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["state"], "failed", message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["resolved_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["state"], "active", message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["all_tasks_count"], 3, message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["resolved_tasks_count"], 2, message)
        self.assertEqual(value["objectives"][2]["id"], 3, message)
        self.assertEqual(value["objectives"][2]["state"], "failed", message)
        self.assertEqual(len(value["objectives"][2]["key_results"]), 1, message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["state"], "failed", message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["resolved_tasks_count"], 1, message)

    def test_get_value_nonexistent(self):
        status, error, message = get_request("/value/33")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    def test_get_value_invalid_id(self):
        status, error, message = get_request("/value/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_get_value_no_id(self):
        status, error, message = get_request("/value")
        assert_bad_url(self, status, error, message)

    def test_get_values(self):
        status, values, message = get_request("/values")
        self.assertEqual(status, 200, message)
        self.assertEqual(len(values), 5, message)
        self.assertEqual(values[0]["name"], "Zdravie", message)

    def test_get_value_check_tasks_count(self):
        status, value, message = get_request("/value/5")
        self.assertEqual(status, 200, message)
        objective = next(obj for obj in value["objectives"] if obj["id"] == 13)
        key_result = next(kr for kr in objective["key_results"] if kr["id"] == 22)

        self.assertEqual(key_result["all_tasks_count"], 8, message)
        self.assertEqual(key_result["resolved_tasks_count"], 4, message)


if __name__ == '__main__':
    unittest.main()
