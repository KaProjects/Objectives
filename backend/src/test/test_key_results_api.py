import json
import unittest

from utils import get_request, post_request, put_request, today, delete_request, assert_method_not_allowed


class TestKeyResultsApi(unittest.TestCase):

    def test_get_key_result(self):
        status, key_result, message = get_request("/key_result/4")

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
        status, error, message = get_request("/key_result/333")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_get_key_result_invalid_id(self):
        status, error, message = get_request("/key_result/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_get_key_result_no_id(self):
        status, error, message = get_request("/key_result")
        assert_method_not_allowed(self, status, error, message)

    def test_create_key_result(self):
        before_status, before_value, before_message = get_request("/value/4")
        self.assertEqual(before_status, 200, before_message)
        before_kr_count = len(next(obj for obj in before_value["objectives"] if obj["id"] == 4)["key_results"])

        name = "new kr"
        description = "a desc"
        objective_id = 4
        payload = json.dumps({"name": name, "description": description, "objective_id": objective_id})
        created_status, created_kr, created_message = post_request("/key_result", payload)

        self.assertEqual(created_status, 201, created_message)
        self.assertEqual(created_kr["name"], name, created_message)
        self.assertEqual(created_kr["description"], description, created_message)
        self.assertEqual(created_kr["objective_id"], objective_id, created_message)
        self.assertEqual(created_kr["state"], "active", created_message)
        self.assertEqual(created_kr["date_reviewed"], today(), created_message)
        self.assertEqual(created_kr["all_tasks_count"], 0, created_message)
        self.assertEqual(created_kr["resolved_tasks_count"], 0, created_message)

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
        self.assertEqual(created_kr["all_tasks_count"], after_kr["all_tasks_count"],
                         str(created_kr) + '\n' + str(after_kr))
        self.assertEqual(created_kr["resolved_tasks_count"], after_kr["resolved_tasks_count"],
                         str(created_kr) + '\n' + str(after_kr))

        new_status, new_kr, new_message = get_request("/key_result/" + str(created_kr["id"]))
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
        status, error, message = post_request("/key_result", None)
        self.assertEqual(status, 500, message)

    def test_create_key_result_null_name(self):
        payload = json.dumps({"name": None, "description": "a desc", "objective_id": 4})
        status, error, message = post_request("/key_result", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_create_key_result_null_description(self):
        payload = json.dumps({"name": "a name", "description": None, "objective_id": 4})
        status, error, message = post_request("/key_result", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_create_key_result_none_objective(self):
        payload = json.dumps({"name": "a name", "description": "a desc", "objective_id": 44})
        status, error, message = post_request("/key_result", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '44' not found" in error, message)

    def test_update_key_result(self):
        before_status, before_key_result, before_message = get_request("/key_result/12")
        self.assertEqual(before_status, 200, before_message)

        name = "new name"
        description = "new desc"
        s, m, a, r, t = "s", "m", "a", "r", "r"
        payload = json.dumps({"name": name, "description": description, "s": s, "m": m, "a": a, "r": r, "t": t})
        status, review_date, message = put_request("/key_result/12", payload)
        self.assertEqual(status, 200, message)
        self.assertEqual(review_date, today(), message)

        after_status, after_key_result, after_message = get_request("/key_result/12")
        self.assertEqual(after_status, 200, after_message)
        self.assertEqual(before_key_result["id"], after_key_result["id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["objective_id"], after_key_result["objective_id"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_key_result["state"], after_key_result["state"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["date_created"], after_key_result["date_created"],
                         before_message + '\n' + after_message)
        self.assertEqual(after_key_result["name"], name, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["description"], description, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["s"], s, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["m"], m, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["a"], a, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["r"], r, before_message + '\n' + after_message)
        self.assertEqual(after_key_result["t"], t, before_message + '\n' + after_message)

    def test_update_key_result_missing_value(self):
        payload = json.dumps({"name": "new name", "description": "new desc"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("KeyError" in error, message)

    def test_update_key_result_null(self):
        status, error, message = put_request("/key_result/7", None)
        self.assertEqual(status, 500, message)

    def test_update_key_result_null_name(self):
        payload = json.dumps(
            {"name": None, "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_key_result_null_description(self):
        payload = json.dumps(
            {"name": "new name", "description": None, "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_key_result_null_smart(self):
        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": None, "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": None, "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": None, "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": None, "t": "t"})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": None})
        status, error, message = put_request("/key_result/7", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_key_result_nonexistent(self):
        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/333", payload)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_update_key_result_invalid_id(self):
        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = put_request("/key_result/x", payload)
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_key_result_no_id(self):
        payload = json.dumps(
            {"name": "new name", "description": "new desc", "s": "s", "m": "m", "a": "a", "r": "r", "t": "t"})
        status, error, message = post_request("/key_result", payload)
        # 500 because it's same url as create kr, just invalid payload
        self.assertEqual(status, 500, message)

    def test_review_key_result(self):
        before_status, before_key_result, before_message = get_request("/key_result/13")
        self.assertEqual(before_status, 200, before_message)

        status, review_date, message = put_request("/key_result/13/review", None)
        self.assertEqual(status, 200, message)
        self.assertEqual(review_date, today(), message)

        after_status, after_key_result, after_message = get_request("/key_result/13")
        self.assertEqual(after_status, 200, after_message)
        self.assertEqual(before_key_result["id"], after_key_result["id"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["objective_id"], after_key_result["objective_id"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_key_result["state"], after_key_result["state"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["date_created"], after_key_result["date_created"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_key_result["name"], after_key_result["name"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["description"], after_key_result["description"],
                         before_message + '\n' + after_message)
        self.assertEqual(before_key_result["s"], after_key_result["s"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["m"], after_key_result["m"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["a"], after_key_result["a"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["r"], after_key_result["r"], before_message + '\n' + after_message)
        self.assertEqual(before_key_result["t"], after_key_result["t"], before_message + '\n' + after_message)

    def test_review_key_result_nonexistent(self):
        status, error, message = put_request("/key_result/333/review", None)
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_review_key_result_invalid_id(self):
        status, error, message = put_request("/key_result/x/review", None)
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_key_result_state(self):
        before_status, before_key_result, before_message = get_request("/key_result/14")
        self.assertEqual(before_status, 200, before_message)

        failed_status = "failed"
        status, new_status, message = put_request("/key_result/14/state", json.dumps({"state": failed_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(failed_status, new_status, message)

        after_failed_status, after_failed_key_result, after_failed_message = get_request("/key_result/14")
        self.assertEqual(after_failed_status, 200, after_failed_message)
        self.assertEqual(failed_status, after_failed_key_result["state"], before_message + '\n' + after_failed_message)

        completed_status = "completed"
        status, new_status, message = put_request("/key_result/14/state", json.dumps({"state": completed_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(completed_status, new_status, message)

        after_completed_status, after_completed_key_result, after_completed_message = get_request("/key_result/14")
        self.assertEqual(after_completed_status, 200, after_completed_message)
        self.assertEqual(completed_status, after_completed_key_result["state"],
                         after_failed_message + '\n' + after_completed_message)

        active_status = "active"
        status, new_status, message = put_request("/key_result/14/state", json.dumps({"state": active_status}))
        self.assertEqual(status, 200, message)
        self.assertEqual(active_status, new_status, message)

        after_active_status, after_active_key_result, after_active_message = get_request("/key_result/14")
        self.assertEqual(after_active_status, 200, after_active_message)
        self.assertEqual(active_status, after_active_key_result["state"],
                         after_completed_message + '\n' + after_active_message)

        self.assertEqual(before_key_result["id"], after_active_key_result["id"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["objective_id"], after_active_key_result["objective_id"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["date_created"], after_active_key_result["date_created"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["name"], after_active_key_result["name"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["description"], after_active_key_result["description"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["s"], after_active_key_result["s"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["m"], after_active_key_result["m"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["a"], after_active_key_result["a"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["r"], after_active_key_result["r"],
                         before_message + '\n' + after_active_message)
        self.assertEqual(before_key_result["t"], after_active_key_result["t"],
                         before_message + '\n' + after_active_message)

        self.assertEqual(after_active_key_result["date_reviewed"], today(), after_active_message)

    def test_update_key_result_state_null(self):
        status, error, message = put_request("/key_result/14/state", None)
        self.assertEqual(status, 500, message)
        self.assertTrue("Bad Request" in error, message)

    def test_update_key_result_state_null_state(self):
        status, error, message = put_request("/key_result/14/state", json.dumps({"state": None}))
        self.assertEqual(status, 422, message)

    def test_update_key_result_state_nonexistent(self):
        status, error, message = put_request("/key_result/333/state", json.dumps({"state": "failed"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_update_key_result_state_invalid_id(self):
        status, error, message = put_request("/key_result/x/state", json.dumps({"state": "failed"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_key_result_state_invalid_state(self):
        status, error, message = put_request("/key_result/14/state", json.dumps({"state": "achieved"}))
        self.assertEqual(status, 422, message)
        self.assertTrue("invalid key result state" in error, message)

    def test_key_result_smart(self):
        status, value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)

        obj = next(obj for obj in value["objectives"] if obj["id"] == 9)

        for id in [16, 17, 18]:
            self.assertTrue(next(kr for kr in obj["key_results"] if kr["id"] == id)["is_smart"], message)

        for id in [19, 20, 21]:
            self.assertFalse(next(kr for kr in obj["key_results"] if kr["id"] == id)["is_smart"], message)

        for id in [16, 17, 18]:
            status, key_result, message = get_request("/key_result/" + str(id))
            self.assertEqual(status, 200, message)
            self.assertTrue(key_result["is_smart"], message)

        for id in [19, 20, 21]:
            status, key_result, message = get_request("/key_result/" + str(id))
            self.assertEqual(status, 200, message)
            self.assertFalse(key_result["is_smart"], message)

    def test_delete_key_result(self):
        status, before_value, message = get_request("/value/5")
        self.assertEqual(status, 200, message)
        before_obj = next(obj for obj in before_value["objectives"] if obj["id"] == 14)
        kr_id_to_del = str(before_obj["key_results"][1]["id"])

        status, key_result_to_del, message = get_request("/key_result/" + kr_id_to_del)
        self.assertEqual(status, 200, message)

        status, del_result, del_message = delete_request("/key_result/" + kr_id_to_del)
        self.assertEqual(status, 204, del_message)

        status, after_value, message = get_request("/value/5")
        self.assertEqual(status, 200, message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 14)

        self.assertEqual(len(before_obj["key_results"]), len(after_obj["key_results"]) + 1,
                         str(after_obj) + "should contain less KR than " + str(before_obj))

        status, content, message = delete_request("/task/" + str(key_result_to_del["tasks"][0]["id"]))
        self.assertEqual(status, 404, message)

        status, content, message = delete_request("/task/" + str(key_result_to_del["tasks"][1]["id"]))
        self.assertEqual(status, 404, message)

        rollback_status, rollback_kr, rollback_message = post_request("/key_result", json.dumps(
            {"name": "to del", "description": "", "objective_id": 14}))
        self.assertEqual(rollback_status, 201, message)
        status, new_task, message = post_request("/task", json.dumps({"kr_id": rollback_kr["id"], "value": "3"}))
        self.assertEqual(status, 201, message)
        status, new_task, message = post_request("/task", json.dumps({"kr_id": rollback_kr["id"], "value": "4"}))
        self.assertEqual(status, 201, message)

    def test_delete_key_result_nonexistent(self):
        status, error, message = delete_request("/key_result/333")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_delete_key_result_invalid_id(self):
        status, error, message = delete_request("/key_result/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_delete_key_result_no_id(self):
        status, error, message = delete_request("/key_result")
        assert_method_not_allowed(self, status, error, message)


if __name__ == '__main__':
    unittest.main()
