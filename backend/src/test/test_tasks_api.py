import json
import unittest

from utils import get_request, post_request, put_request, today, delete_request, assert_method_not_allowed


class TestTasksApi(unittest.TestCase):

    def test_create_task(self):
        status, before_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        before_obj = next(obj for obj in before_value["objectives"] if obj["id"] == 6)
        before_obj_kr = next(kr for kr in before_obj["key_results"] if kr["id"] == 10)

        before_status, before_key_result, before_message = get_request("/key_result/10")
        self.assertEqual(before_status, 200, before_message)

        kr_id = 10
        value = "task value"
        status, new_task, message = post_request("/task", json.dumps({"kr_id": kr_id, "value": value}))
        self.assertEqual(status, 201, message)
        self.assertEqual(new_task["state"], "active", message)
        self.assertEqual(new_task["kr_id"], kr_id, message)
        self.assertEqual(new_task["value"], value, message)

        after_status, after_key_result, after_message = get_request("/key_result/10")
        self.assertEqual(after_status, 200, after_message)
        self.assertEqual(len(before_key_result["tasks"]) + 1, len(after_key_result["tasks"]),
                         before_message + '\n' + after_message)
        after_kr_task = next(t for t in after_key_result["tasks"] if t["id"] == new_task["id"])
        self.assertEqual(new_task["kr_id"], new_task["kr_id"], str(new_task) + '\n' + str(after_kr_task))
        self.assertEqual(new_task["value"], new_task["value"], str(new_task) + '\n' + str(after_kr_task))
        self.assertEqual(new_task["state"], new_task["state"], str(new_task) + '\n' + str(after_kr_task))

        self.assertEqual(after_key_result["date_reviewed"], today(), after_message)

        status, after_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 6)
        after_obj_kr = next(kr for kr in after_obj["key_results"] if kr["id"] == 10)
        self.assertEqual(before_obj_kr["resolved_tasks_count"], after_obj_kr["resolved_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))
        self.assertEqual(before_obj_kr["all_tasks_count"] + 1, after_obj_kr["all_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))

    def test_create_task_null(self):
        status, error, message = post_request("/task", None)
        self.assertEqual(status, 500, message)

        status, error, message = post_request("/task", json.dumps(None))
        self.assertEqual(status, 500, message)

    def test_create_task_null_kr_id(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": None, "value": "value"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("not 'NoneType'" in error, message)

    def test_create_task_null_value(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": 10, "value": None}))
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_create_task_none_key_result(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": "777", "value": "None"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '777' not found" in error, message)

    def test_update_task(self):
        status, before_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        before_obj = next(obj for obj in before_value["objectives"] if obj["id"] == 6)
        before_obj_kr = next(kr for kr in before_obj["key_results"] if kr["id"] == 9)

        before_status, before_key_result, before_message = get_request("/key_result/9")
        self.assertEqual(before_status, 200, before_message)
        before_kr_task = next(t for t in before_key_result["tasks"] if t["id"] == 8)

        value = "updated value"
        state = "finished"
        payload = json.dumps({"kr_id": before_kr_task["kr_id"], "value": value, "state": state})
        updated_status, updated_task, updated_message = put_request("/task/8", payload)
        self.assertEqual(updated_status, 200, updated_message)
        self.assertEqual(updated_task["value"], value, updated_message)
        self.assertEqual(updated_task["state"], state, updated_message)
        self.assertEqual(updated_task["kr_id"], before_kr_task["kr_id"], updated_message)

        after_status, after_key_result, after_message = get_request("/key_result/9")
        self.assertEqual(after_status, 200, after_message)
        after_kr_task = next(t for t in after_key_result["tasks"] if t["id"] == 8)
        self.assertEqual(before_kr_task["kr_id"], after_kr_task["kr_id"], updated_message + '\n' + str(after_kr_task))
        self.assertEqual(value, after_kr_task["value"], updated_message + '\n' + str(after_kr_task))
        self.assertEqual(state, after_kr_task["state"], updated_message + '\n' + str(after_kr_task))

        self.assertEqual(after_key_result["date_reviewed"], today(), after_message)

        status, after_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 6)
        after_obj_kr = next(kr for kr in after_obj["key_results"] if kr["id"] == 9)
        self.assertEqual(before_obj_kr["resolved_tasks_count"] + 1, after_obj_kr["resolved_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))
        self.assertEqual(before_obj_kr["all_tasks_count"], after_obj_kr["all_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))

        payload = json.dumps({"kr_id": before_kr_task["kr_id"], "value": value, "state": "active"})
        rollback_status, rollback_task, rollback_message = put_request("/task/8", payload)
        self.assertEqual(rollback_status, 200, rollback_status)

    def test_update_task_invalid_state(self):
        status, error, message = put_request("/task/8", json.dumps({"kr_id": 9, "value": "value", "state": "xxx"}))
        self.assertEqual(status, 422, message)
        self.assertTrue("invalid task state" in error, message)

    def test_update_task_missing_value(self):
        status, error, message = put_request("/task/8", json.dumps({"value": "value", "state": "active"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("KeyError" in error, message)

    def test_update_task_null(self):
        status, error, message = put_request("/task/8", None)
        self.assertEqual(status, 500, message)
        self.assertTrue("Bad Request" in error, message)

    def test_update_task_null_kr_id(self):
        status, error, message = put_request("/task/8",
                                             json.dumps({"kr_id": None, "value": "value", "state": "active"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("NoneType" in error, message)

    def test_update_task_null_value(self):
        status, error, message = put_request("/task/8", json.dumps({"kr_id": 9, "value": None, "state": "active"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("NOT NULL constraint" in error, message)

    def test_update_task_null_state(self):
        status, error, message = put_request("/task/8", json.dumps({"kr_id": 9, "value": "value", "state": None}))
        self.assertEqual(status, 422, message)
        self.assertTrue("invalid task state" in error, message)

    def test_update_task_nonexistent(self):
        status, error, message = put_request("/task/333", json.dumps({"kr_id": 9, "value": "value", "state": "active"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_update_task_invalid_id(self):
        status, error, message = put_request("/task/x", json.dumps({"kr_id": 9, "value": "value", "state": "active"}))
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_update_task_no_id(self):
        status, error, message = put_request("/task", json.dumps({"kr_id": 9, "value": "value", "state": "active"}))
        assert_method_not_allowed(self, status, error, message)

    def test_delete_task(self):
        status, before_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        before_obj = next(obj for obj in before_value["objectives"] if obj["id"] == 6)
        before_obj_kr = next(kr for kr in before_obj["key_results"] if kr["id"] == 11)

        status, before_key_result, before_message = get_request("/key_result/11")
        self.assertEqual(status, 200, before_message)

        status, content, message = delete_request("/task/" + str(before_key_result["tasks"][1]["id"]))
        self.assertEqual(status, 204, message)

        status, after_key_result, after_message = get_request("/key_result/11")
        self.assertEqual(status, 200, after_message)
        self.assertEqual(len(before_key_result["tasks"]) - 1, len(after_key_result["tasks"]),
                         before_message + '\n' + after_message)

        status, after_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 6)
        after_obj_kr = next(kr for kr in after_obj["key_results"] if kr["id"] == 11)
        self.assertEqual(before_obj_kr["resolved_tasks_count"], after_obj_kr["resolved_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))
        self.assertEqual(before_obj_kr["all_tasks_count"] - 1, after_obj_kr["all_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))

        rollback_status, rollback_task, rollback_message = post_request("/task",
                                                                        json.dumps({"kr_id": 11, "value": "to del"}))
        self.assertEqual(rollback_status, 201, message)

    def test_delete_task_nonexistent(self):
        status, error, message = delete_request("/task/333")
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_delete_task_invalid_id(self):
        status, error, message = delete_request("/task/x")
        self.assertEqual(status, 500, message)
        self.assertTrue("ValueError" in error, message)

    def test_delete_task_no_id(self):
        status, error, message = delete_request("/task")
        assert_method_not_allowed(self, status, error, message)


if __name__ == '__main__':
    unittest.main()
