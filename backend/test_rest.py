import unittest
import requests
import json
from classes import Value
from datetime import date


origin = "http://127.0.0.1:7702"


def post_request(path, payload):
    response = requests.post(origin + path, payload, headers={'Content-Type': 'application/json'})
    content = parseContent(response)
    return response.status_code, content, "Response: " + str(content)

def get_request(path):
    response = requests.get(origin + path)
    content = parseContent(response)
    return response.status_code, content, "Response: " + str(content)

def parseContent(response):
    if (response.headers.get('content-type').casefold() == "application/json"):
        return response.json()
    else:
        return response.content.decode("utf-8")

def assertBadUrl(self, status, error, message):
    self.assertEqual(status, 404, message)
    self.assertTrue("The requested URL was not found on the server." in error, message)

def assertMethodNotAllowed(self, status, error, message):
    self.assertEqual(status, 405, message)
    self.assertTrue("The method is not allowed for the requested URL." in error, message)

def today():
    return date.today().strftime("%d/%m/%Y")


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
        self.assertEqual(value["objectives"][0]["key_results"][0]["finished_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["id"], 2, message)
        self.assertEqual(value["objectives"][1]["state"], "active", message)
        self.assertEqual(len(value["objectives"][1]["key_results"]), 3, message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["state"], "completed", message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][0]["finished_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["state"], "failed", message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][1]["key_results"][1]["finished_tasks_count"], 0, message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["state"], "active", message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["all_tasks_count"], 3, message)
        self.assertEqual(value["objectives"][1]["key_results"][2]["finished_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][2]["id"], 3, message)
        self.assertEqual(value["objectives"][2]["state"], "failed", message)
        self.assertEqual(len(value["objectives"][2]["key_results"]), 1, message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["state"], "failed", message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["all_tasks_count"], 1, message)
        self.assertEqual(value["objectives"][2]["key_results"][0]["finished_tasks_count"], 0, message)


    def test_get_value_nonexistent(self):
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
        self.assertEqual(len(values), 4, message)
        self.assertEqual(values[0]["name"], "Zdravie", message)


    # TODO test create/update/delete value here


# class TestObjectivesApi(unittest.TestCase):
    # TODO test objective crud here


class TestKeyResultsApi(unittest.TestCase):

    def test_get_key_result(self):
        status, key_result, message = get_request("/keyresult/4")

        self.assertEqual(status, 200, message)
        self.assertEqual(key_result["id"], 4, message)
        self.assertEqual(key_result["objective_id"], 2, message)
        self.assertEqual(key_result["name"], "ccc", message)
        self.assertEqual(key_result["state"], "active", message)
        self.assertEqual(key_result["description"], "desc", message)
        self.assertEqual(key_result["s"], "a", message)
        self.assertEqual(key_result["m"], "b", message)
        self.assertEqual(key_result["a"], "c", message)
        self.assertEqual(key_result["r"], "d", message)
        self.assertEqual(key_result["t"], "e", message)
        self.assertEqual(key_result["date_created"], "10/03/2023", message)
        self.assertEqual(key_result["date_reviewed"], "13/03/2023", message)
        self.assertEqual(len(key_result["tasks"]), 3, message)
        self.assertEqual(key_result["tasks"][0]["kr_id"], 4, message)
        self.assertTrue("task2" in key_result["tasks"][0]["value"], message)


    def test_get_key_result_nonexistent(self):
        status, error, message = get_request("/keyresult/33")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    
    def test_get_key_result_invalid_id(self):
        status, error, message = get_request("/keyresult/x")
        self.assertEqual(status, 500, message)


    def test_get_key_result_no_id(self):
        status, error, message = get_request("/keyresult")
        assertMethodNotAllowed(self, status, error, message)


    def test_create_key_result(self):
        before_status, before_value, before_message = get_request("/value/4")
        self.assertEqual(before_status, 200, before_message)
        before_kr_count = len(next(obj for obj in before_value["objectives"] if obj["id"] == 4)["key_results"])

        name = "new kr"
        description = "a desc"
        objective_id = 4
        payload = json.dumps({"name": name, "description": description, "objective_id": objective_id})
        created_status, created_kr, created_message = post_request("/keyresult", payload)

        self.assertEqual(created_status, 200, created_message)
        self.assertEqual(created_kr["name"], name, created_message)
        self.assertEqual(created_kr["description"], description, created_message)
        self.assertEqual(created_kr["objective_id"], objective_id, created_message)
        self.assertEqual(created_kr["state"], "active", created_message)
        self.assertEqual(created_kr["date_reviewed"], today(), created_message)
        self.assertEqual(created_kr["all_tasks_count"], 0, created_message)
        self.assertEqual(created_kr["finished_tasks_count"], 0, created_message)

        after_status, after_value, after_message = get_request("/value/4")
        self.assertEqual(after_status, 200, after_message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 4)
        self.assertEqual(len(after_obj["key_results"]), before_kr_count + 1, after_message)
        after_kr = next(kr for kr in after_obj["key_results"] if kr["id"] == created_kr["id"])
        self.assertEqual(created_kr["id"], after_kr["id"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["objective_id"], after_kr["objective_id"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["state"], after_kr["state"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["name"], after_kr["name"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["date_reviewed"], after_kr["date_reviewed"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["all_tasks_count"], after_kr["all_tasks_count"], str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["finished_tasks_count"], after_kr["finished_tasks_count"], str(created_kr) + '\n' + str(after_kr))
                
        new_status, new_kr, new_message = get_request("/keyresult/" + str(created_kr["id"]))
        self.assertEqual(new_status, 200, new_message)
        self.assertEqual(created_kr["id"], new_kr["id"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["objective_id"], new_kr["objective_id"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["state"], new_kr["state"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["name"], new_kr["name"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["description"], new_kr["description"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["date_reviewed"], new_kr["date_reviewed"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(created_kr["date_reviewed"], new_kr["date_created"], str(created_kr) + '\n' + str(new_kr))
        self.assertEqual(new_kr["s"], "", new_message)
        self.assertEqual(new_kr["m"], "", new_message)
        self.assertEqual(new_kr["a"], "", new_message)
        self.assertEqual(new_kr["r"], "", new_message)
        self.assertEqual(new_kr["t"], "", new_message)
        self.assertEqual(len(new_kr["tasks"]), 0, new_message)


    def test_create_key_result_null(self):
        status, error, message = post_request("/keyresult", None)
        self.assertEqual(status, 400, message)


    def test_create_key_result_null_name(self):
        payload = json.dumps({"name": None, "description": "a desc", "objective_id": 4})
        status, error, message = post_request("/keyresult", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)


    def test_create_key_result_null_description(self):
        payload = json.dumps({"name": "a name", "description": None, "objective_id": 4})
        status, error, message = post_request("/keyresult", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)


    def test_create_key_result_none_objective(self):
        payload = json.dumps({"name": "a name", "description": "a desc", "objective_id": 44})
        status, error, message = post_request("/keyresult", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '44' not found" in error, message)


    def test_update_key_result(self):
        before_status, before_key_result, before_message = get_request("/keyresult/12")
        self.assertEqual(before_status, 200, before_message)

        name = "new name"
        description = "new desc"
        s, m, a, r, t = "s", "m", "a", "r", "r"
        payload = json.dumps({"name": name, "description": description, "s": s, "m": m, "a": a, "r": r, "t": t})
        status, review_date, message = post_request("/keyresult/12", payload)
        self.assertEqual(status, 200, message)
        self.assertEqual(review_date, today(), message)

        after_status, after_key_result, after_message = get_request("/keyresult/12")
        self.assertEqual(after_status, 200, after_message)
        self.assertEqual(before_key_result["id"], after_key_result["id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["objective_id"], after_key_result["objective_id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["state"], after_key_result["state"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["date_created"], after_key_result["date_created"], before_message + '\n' + after_message)
        self.assertEqual(after_key_result["name"], name, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["description"], description, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["s"], s, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["m"], m, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["a"], a, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["r"], r, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["t"], t, before_message + '\n' + after_message)


    def test_update_key_result_missing_value(self):
        payload = json.dumps({"name": "new name", "description": "new desc"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("s" in error, message)


    def test_update_key_result_null(self):
        status, error, message = post_request("/keyresult/7", None)
        self.assertEqual(status, 400, message)

        
    def test_update_key_result_null_name(self):
        payload = json.dumps({"name": None, "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)
    

    def test_update_key_result_null_description(self):
        payload = json.dumps({"name": "new name", "description": None, "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)


    def test_update_key_result_null_smart(self):
        payload = json.dumps({"name": "new name", "description": "new desc", "s": None, "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": None, "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": None, "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": None, "t": "t"})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": None})
        status, error, message = post_request("/keyresult/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)


    def test_update_key_result_nonexistent(self):
        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/33", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    
    def test_update_key_result_invalid_id(self):
        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult/x", payload)
        self.assertEqual(status, 500, message)


    def test_update_key_result_no_id(self):
        payload = json.dumps({"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/keyresult", payload)
        # 500 because it's same url as create kr, just invalid payload
        self.assertEqual(status, 500, message)


    def test_review_key_result(self):
        before_status, before_key_result, before_message = get_request("/keyresult/13")
        self.assertEqual(before_status, 200, before_message)

        status, review_date, message = post_request("/keyresult/13/review", None)
        self.assertEqual(status, 200, message)
        self.assertEqual(review_date, today(), message)

        after_status, after_key_result, after_message = get_request("/keyresult/13")
        self.assertEqual(after_status, 200, after_message)
        self.assertEqual(before_key_result["id"], after_key_result["id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["objective_id"], after_key_result["objective_id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["state"], after_key_result["state"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["date_created"], after_key_result["date_created"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["name"], after_key_result["name"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["description"], after_key_result["description"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["s"], after_key_result["s"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["m"], after_key_result["m"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["a"], after_key_result["a"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["r"], after_key_result["r"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["t"], after_key_result["t"], before_message + '\n' + after_message)


    def test_review_key_result_nonexistent(self):
        status, error, message = post_request("/keyresult/33/review", None)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    
    def test_review_key_result_invalid_id(self):
        status, error, message = post_request("/keyresult/x/review", None)
        self.assertEqual(status, 500, message)       




    # TODO test kr state

    # TODO test delete kr here


# class TestTasksApi(unittest.TestCase):
    # TODO test task crud here



    
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