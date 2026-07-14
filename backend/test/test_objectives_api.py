import json
import unittest

from utils import get_request, post_request, put_request, today, delete_request, assert_method_not_allowed


class TestObjectivesApi(unittest.TestCase):

    def test_create_objective(self):
        before_status, before_value, before_message = get_request("/value/4")
        self.assertEqual(before_status, 200, before_message)
        before_obj_count = len(before_value["objectives"])

        name = "new obj"
        description = "a desc obj"
        value_id = 4
        payload = json.dumps({"name": name, "description": description, "value_id": value_id})
        created_status, created_obj, created_message = post_request("/objective", payload)

        self.assertEqual(created_status, 201, created_message)
        self.assertEqual(created_obj["name"], name, created_message)
        self.assertEqual(created_obj["description"], description, created_message)
        self.assertEqual(created_obj["value_id"], value_id, created_message)
        self.assertEqual(created_obj["state"], "active", created_message)
        self.assertEqual(created_obj["date_created"], today(), created_message)
        self.assertEqual(created_obj["date_finished"], "", created_message)
        self.assertEqual(created_obj["ideas_count"], 0, created_message)

        after_status, after_value, after_message = get_request("/value/4")
        self.assertEqual(after_status, 200, after_message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == created_obj["id"])
        self.assertEqual(after_obj["name"], name, str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["description"], description, str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["value_id"], value_id, str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["state"], "active", str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["date_created"], today(), str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["date_finished"], "", str(created_obj) + '\n' + str(after_obj))
        self.assertTrue(len(after_obj["key_results"]) == 0, str(created_obj) + '\n' + str(after_obj))
        self.assertEqual(after_obj["ideas_count"], 0, str(created_obj) + '\n' + str(after_obj))

    def test_create_objective_null(self):
        status, error, message = post_request("/objective", None)
        self.assertEqual(status, 500, message)

    def test_create_objective_null_name(self):
        payload = json.dumps({"name": None, "description": "a desc", "value_id": 4})
        status, error, message = post_request("/objective", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_create_objective_null_description(self):
        payload = json.dumps({"name": "a name", "description": None, "value_id": 4})
        status, error, message = post_request("/objective", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_create_objective_none_value(self):
        payload = json.dumps({"name": "a name", "description": "a desc", "value_id": 44})
        status, error, message = post_request("/objective", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '44' not found" in error, message)

    def test_update_objective(self):
        before_status, before_value, before_message = get_request("/value/4")
        self.assertEqual(before_status, 200, before_message)
        before_objective = next(obj for obj in before_value["objectives"] if obj["id"] == 8)

        name = "new name"
        description = "new desc"
        payload = json.dumps({"name": name, "description": description})
        status, response, message = put_request("/objective/8", payload)
        self.assertEqual(status, 200, message)
        self.assertEqual(response, "", message)

        after_status, after_value, after_message = get_request("/value/4")
        self.assertEqual(after_status, 200, after_message)
        after_objective = next(obj for obj in after_value["objectives"] if obj["id"] == 8)

        self.assertEqual(before_objective["id"], after_objective["id"], before_message + '\n' + after_message)
        self.assertEqual(before_objective["value_id"], after_objective["value_id"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_objective["state"], after_objective["state"], before_message + '\n' + after_message)
        self.assertEqual(after_objective["name"], name, before_message + '\n' + after_message)
        self.assertEqual(after_objective["description"], description, before_message + '\n' + after_message)
        self.assertEqual(before_objective["date_created"], after_objective["date_created"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_objective["date_finished"], after_objective["date_finished"],
                         before_message + '\n' + after_message)

    def test_update_objective_missing_value(self):
        payload = json.dumps({"name": "new name"})
        status, error, message = put_request("/objective/8", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("KeyError" in error, message)

    def test_update_objective_null(self):
        status, error, message = put_request("/objective/8", None)
        self.assertEqual(status, 500, message)

    def test_update_objective_null_name(self):
        payload = json.dumps({"name": None, "description": "new desc"})
        status, error, message = put_request("/objective/8", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_objective_null_description(self):
        payload = json.dumps({"name": "new name", "description": None})
        status, error, message = put_request("/objective/8", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_objective_nonexistent(self):
        payload = json.dumps({"name": "new name", "description": "new desc"})
        status, error, message = put_request("/objective/33", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    def test_update_objective_invalid_id(self):
        payload = json.dumps({"name": "new name", "description": "new desc"})
        status, error, message = put_request("/objective/x", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_objective_no_id(self):
        payload = json.dumps({"name": "new name", "description": "new desc"})
        status, error, message = put_request("/objective", payload)
        assert_method_not_allowed(self, status, error, message)

    def test_update_objective_state(self):
        before_status, before_value, before_message = get_request("/value/4")
        self.assertEqual(before_status, 200, before_message)
        before_objective = next(obj for obj in before_value["objectives"] if obj["id"] == 8)

        failed_status = "failed"
        status, response, message = put_request("/objective/8/state", json.dumps({"state": failed_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(response["state"], failed_status, message)
        self.assertEqual(response["date"], today(), message)

        after_failed_status, after_failed_value, after_failed_message = get_request("/value/4")
        self.assertEqual(after_failed_status, 200, after_failed_message)
        after_failed_objective = next(obj for obj in after_failed_value["objectives"] if obj["id"] == 8)
        self.assertEqual(failed_status, after_failed_objective["state"], before_message + '\n' + after_failed_message)
        self.assertEqual(today(), after_failed_objective["date_finished"], before_message + '\n' + after_failed_message)

        achieved_status = "achieved"
        status, response, message = put_request("/objective/8/state", json.dumps({"state": achieved_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(response["state"], achieved_status, message)
        self.assertEqual(response["date"], today(), message)

        after_achieved_status, after_achieved_value, after_achieved_message = get_request("/value/4")
        self.assertEqual(after_achieved_status, 200, after_achieved_message)
        after_achieved_objective = next(obj for obj in after_achieved_value["objectives"] if obj["id"] == 8)
        self.assertEqual(after_achieved_objective["state"], achieved_status,
                         after_failed_message + '\n' + after_achieved_message)
        self.assertEqual(after_achieved_objective["date_finished"], today(),
                         after_failed_message + '\n' + after_achieved_message)

        active_status = "active"
        status, response, message = put_request("/objective/8/state", json.dumps({"state": active_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(response["state"], active_status, message)
        self.assertEqual(response["date"], "", message)

        after_active_status, after_active_value, after_active_message = get_request("/value/4")
        self.assertEqual(after_active_status, 200, after_active_message)
        after_active_objective = next(obj for obj in after_active_value["objectives"] if obj["id"] == 8)
        self.assertEqual(after_active_objective["state"], active_status,
                         after_achieved_message + '\n' + after_active_message)
        self.assertEqual(after_active_objective["date_finished"], "",
                         after_achieved_message + '\n' + after_active_message)

        self.assertEqual(before_objective["id"], after_active_objective["id"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_objective["value_id"], after_active_objective["value_id"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_objective["name"], after_active_objective["name"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_objective["description"], after_active_objective["description"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_objective["date_created"], after_active_objective["date_created"],
                         before_message + '\n' + after_active_message)

    def test_update_objective_state_null(self):
        status, error, message = put_request("/objective/8/state", None)
        self.assertEqual(status, 500, message)
        self.assertTrue("Bad Request" in error, message)

    def test_update_objective_state_null_state(self):
        status, error, message = put_request("/objective/8/state", json.dumps({"state": None}))
        self.assertEqual(status, 422, message)
        self.assertTrue("invalid objective state" in error, message)

    def test_update_objective_state_nonexistent(self):
        status, error, message = put_request("/objective/33/state", json.dumps({"state": "failed"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    def test_update_objective_state_invalid_id(self):
        status, error, message = put_request("/objective/x/state", json.dumps({"state": "failed"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_objective_state_invalid_state(self):
        status, error, message = put_request("/objective/8/state", json.dumps({"state": "completed"}))
        self.assertEqual(status, 422, message)
        self.assertTrue("invalid objective state" in error, message)

    def test_delete_objective(self):
        before_status, before_value, before_message = get_request("/value/5")
        self.assertEqual(before_status, 200, before_message)

        payload = json.dumps({"name": "obj to del", "description": "description", "value_id": 5})
        created_status, created_obj, created_message = post_request("/objective", payload)
        self.assertEqual(created_status, 201, created_message)
        obj_id = str(created_obj["id"])

        status, idea, message = post_request("/objective/" + obj_id + "/idea", json.dumps({"value": "value"}))
        self.assertEqual(status, 201, message)
        idea_id = str(idea["id"])

        del_status, nothing, del_message = delete_request("/objective/" + obj_id)
        self.assertEqual(del_status, 204, del_message)

        after_status, after_value, after_message = get_request("/value/5")
        self.assertEqual(after_status, 200, after_message)

        self.assertEqual(len(before_value["objectives"]), len(after_value["objectives"]),
                         str(before_value["objectives"]) + " should be same as " + str(after_value["objectives"]))

        status, error, message = delete_request("/objective/" + obj_id + "/idea/" + idea_id)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '" + idea_id + "' not found" in error, message)

    def test_delete_objective_with_key_results(self):
        del_status, nothing, del_message = delete_request("/objective/14")
        self.assertEqual(del_status, 403, del_message)

    def test_delete_objective_nonexistent(self):
        status, error, message = delete_request("/objective/333")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_delete_objective_invalid_id(self):
        status, error, message = delete_request("/objective/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_delete_objective_no_id(self):
        status, error, message = delete_request("/objective")
        assert_method_not_allowed(self, status, error, message)

    def test_objective_ideas(self):
        status, ideas, message = get_request("/objective/10/idea")
        self.assertEqual(status, 200, message)
        self.assertTrue(len(ideas) == 3, message)
        self.assertEqual(ideas[0]["id"], 1, message)
        self.assertEqual(ideas[0]["objective_id"], 10, message)

        status, value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        objective = next(obj for obj in value["objectives"] if obj["id"] == 10)
        self.assertEqual(objective["ideas_count"], 3, message)

    def test_objective_idea_update(self):
        new_value = "new value"
        status, value, message = put_request("/objective/10/idea/2", json.dumps({"value": new_value}))
        self.assertEqual(status, 200, message)

        status, ideas, message = get_request("/objective/10/idea")
        idea = next(idea for idea in ideas if idea["id"] == 2)
        self.assertEqual(idea["value"], new_value, message)

    def test_objective_idea_update_null(self):
        status, error, message = put_request("/objective/10/idea/2", None)
        self.assertEqual(status, 500, message)
        self.assertTrue("Bad Request" in error, message)

    def test_objective_idea_update_null_value(self):
        status, error, message = put_request("/objective/10/idea/2", json.dumps({"value": None}))
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_objective_idea_update_nonexistent(self):
        status, error, message = put_request("/objective/10/idea/33", json.dumps({"value": "new_value"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '33' not found" in error, message)

    def test_objective_idea_update_nonexistent_objevtive(self):
        status, error, message = put_request("/objective/444/idea/2", json.dumps({"value": "new_value"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '444' not found" in error, message)

    def test_objective_idea_update_invalid_id(self):
        status, error, message = put_request("/objective/x/idea/2", json.dumps({"value": "new_value"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

        status, error, message = put_request("/objective/10/idea/x", json.dumps({"value": "new_value"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_objective_idea_create(self):
        status, value, before_value_message = get_request("/value/4")
        self.assertEqual(status, 200, before_value_message)
        before_objective = next(obj for obj in value["objectives"] if obj["id"] == 11)

        before_status, before_ideas, before_message = get_request("/objective/11/idea")
        self.assertEqual(before_status, 200, before_message)

        status, idea, message = post_request("/objective/11/idea", json.dumps({"value": "value"}))
        self.assertEqual(status, 201, message)
        self.assertEqual(idea["objective_id"], "11", message)
        self.assertEqual(idea["value"], "value", message)

        after_status, after_ideas, after_message = get_request("/objective/11/idea")
        self.assertEqual(after_status, 200, after_message)

        self.assertEqual(len(before_ideas) + 1, len(after_ideas), before_message + '\n' + after_message)

        status, value, after_value_message = get_request("/value/4")
        self.assertEqual(status, 200, after_value_message)
        after_objective = next(obj for obj in value["objectives"] if obj["id"] == 11)

        self.assertEqual(before_objective["ideas_count"] + 1, after_objective["ideas_count"],
                         before_value_message + '\n' + after_value_message)

    def test_objective_idea_create_null(self):
        status, error, message = post_request("/objective/11/idea", None)
        self.assertEqual(status, 500, message)

    def test_objective_idea_create_null_value(self):
        status, error, message = post_request("/objective/11/idea", json.dumps({"value": None}))
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_objective_idea_create_none_objective(self):
        status, error, message = post_request("/objective/44/idea", json.dumps({"value": "value"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '44' not found" in error, message)

    def test_objective_idea_delete(self):
        status, idea, message = post_request("/objective/12/idea", json.dumps({"value": "to del"}))
        self.assertEqual(status, 201, message)

        status, value, before_value_message = get_request("/value/4")
        self.assertEqual(status, 200, before_value_message)
        before_objective = next(obj for obj in value["objectives"] if obj["id"] == 12)

        before_status, before_ideas, before_message = get_request("/objective/12/idea")
        self.assertEqual(before_status, 200, before_message)

        status, none, message = delete_request("/objective/12/idea/" + str(idea["id"]))
        self.assertEqual(status, 204, message)

        after_status, after_ideas, after_message = get_request("/objective/12/idea")
        self.assertEqual(after_status, 200, after_message)

        self.assertEqual(len(before_ideas), len(after_ideas) + 1, before_message + '\n' + after_message)

        status, value, after_value_message = get_request("/value/4")
        self.assertEqual(status, 200, after_value_message)
        after_objective = next(obj for obj in value["objectives"] if obj["id"] == 12)

        self.assertEqual(before_objective["ideas_count"], after_objective["ideas_count"] + 1,
                         before_value_message + '\n' + after_value_message)

    def test_objective_idea_delete_nonexistent(self):
        status, error, message = delete_request("/objective/12/idea/333")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

        status, error, message = delete_request("/objective/444/idea/1")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '444' not found" in error, message)

    def test_objective_idea_delete_invalid_id(self):
        status, error, message = delete_request("/objective/12/idea/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

        status, error, message = delete_request("/objective/x/idea/1")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_objective_idea_delete_no_id(self):
        status, error, message = delete_request("/objective/12/idea")
        assert_method_not_allowed(self, status, error, message)


if __name__ == '__main__':
    unittest.main()
