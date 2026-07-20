import json
import unittest

from support import ApiTestCase
from utils import get_request, post_request, put_request, today, delete_request, assert_method_not_allowed


class TestTasksApi(ApiTestCase):

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
        self.assertEqual(new_task["kr_id"], after_kr_task["kr_id"], str(new_task) + '\n' + str(after_kr_task))
        self.assertEqual(new_task["value"], after_kr_task["value"], str(new_task) + '\n' + str(after_kr_task))
        self.assertEqual(new_task["state"], after_kr_task["state"], str(new_task) + '\n' + str(after_kr_task))

        self.assertEqual(after_key_result["date_reviewed"], today(), after_message)

        status, after_value, message = get_request("/value/4")
        self.assertEqual(status, 200, message)
        after_obj = next(obj for obj in after_value["objectives"] if obj["id"] == 6)
        after_obj_kr = next(kr for kr in after_obj["key_results"] if kr["id"] == 10)
        self.assertEqual(before_obj_kr["resolved_tasks_count"], after_obj_kr["resolved_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))
        self.assertEqual(before_obj_kr["all_tasks_count"] + 1, after_obj_kr["all_tasks_count"],
                         str(before_obj_kr) + '\n' + str(after_obj_kr))

    def test_create_multiple_tasks(self):
        status, before_key_result, message = get_request('/key_result/10')
        self.assertEqual(status, 200, message)

        status, created_tasks, message = post_request('/task/bulk', json.dumps({
            'kr_id': 10,
            'value': 'Generated task',
            'count': 3,
        }))
        self.assertEqual(status, 201, message)
        self.assertEqual([task['value'] for task in created_tasks], [
            'Generated task 1', 'Generated task 2', 'Generated task 3',
        ], message)
        self.assertTrue(all(task['kr_id'] == 10 for task in created_tasks), message)
        self.assertTrue(all(task['state'] == 'active' for task in created_tasks), message)

        status, after_key_result, message = get_request('/key_result/10')
        self.assertEqual(status, 200, message)
        self.assertEqual(len(after_key_result['tasks']), len(before_key_result['tasks']) + 3, message)

    def test_create_multiple_tasks_rejects_count_outside_limit(self):
        for count in (0, 21):
            status, _, message = post_request('/task/bulk', json.dumps({
                'kr_id': 10,
                'value': 'Generated task',
                'count': count,
            }))
            self.assertIn(status, (400, 422), message)

    def test_create_daily_tasks(self):
        status, before_key_result, message = get_request('/key_result/10')
        self.assertEqual(status, 200, message)

        status, created_tasks, message = post_request('/task/daily', json.dumps({
            'kr_id': 10,
            'value': 'Drink water',
            'from_date': '2026-07-02',
            'to_date': '2026-07-04',
        }))
        self.assertEqual(status, 201, message)
        self.assertEqual([task['value'] for task in created_tasks], [
            '2.7. Drink water', '3.7. Drink water', '4.7. Drink water',
        ], message)

        status, after_key_result, message = get_request('/key_result/10')
        self.assertEqual(status, 200, message)
        self.assertEqual(len(after_key_result['tasks']), len(before_key_result['tasks']) + 3, message)

    def test_create_daily_tasks_allows_an_empty_value(self):
        status, created_tasks, message = post_request('/task/daily', json.dumps({
            'kr_id': 10,
            'value': '',
            'from_date': '2026-07-02',
            'to_date': '2026-07-02',
        }))
        self.assertEqual(status, 201, message)
        self.assertEqual(created_tasks[0]['value'], '2.7.', message)

    def test_create_daily_tasks_rejects_invalid_ranges(self):
        for from_date, to_date, expected_error in (
            ('2026-07-04', '2026-07-02', 'The end date cannot be before the start date.'),
            ('2026-07-01', '2026-07-21', 'A daily task range cannot exceed 20 days.'),
        ):
            status, error, message = post_request('/task/daily', json.dumps({
                'kr_id': 10,
                'value': 'Drink water',
                'from_date': from_date,
                'to_date': to_date,
            }))
            self.assertEqual(status, 400, message)
            self.assertEqual(error, expected_error, message)

    def test_create_task_null(self):
        status, error, message = post_request("/task", None)
        self.assertIn(status, (400, 422), message)

        status, error, message = post_request("/task", json.dumps(None))
        self.assertIn(status, (400, 422), message)

    def test_create_task_null_kr_id(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": None, "value": "value"}))
        self.assertIn(status, (400, 422), message)

    def test_create_task_null_value(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": 10, "value": None}))
        self.assertIn(status, (400, 422), message)

    def test_create_task_none_key_result(self):
        status, error, message = post_request("/task", json.dumps({"kr_id": 777, "value": "None"}))
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
        self.assertIn(status, (400, 422), message)

    def test_update_task_null(self):
        status, error, message = put_request("/task/8", None)
        self.assertIn(status, (400, 422), message)

    def test_update_task_null_kr_id(self):
        status, error, message = put_request("/task/8",
                                             json.dumps({"kr_id": None, "value": "value", "state": "active"}))
        self.assertIn(status, (400, 422), message)

    def test_update_task_null_value(self):
        status, error, message = put_request("/task/8", json.dumps({"kr_id": 9, "value": None, "state": "active"}))
        self.assertIn(status, (400, 422), message)

    def test_update_task_null_state(self):
        status, error, message = put_request("/task/8", json.dumps({"kr_id": 9, "value": "value", "state": None}))
        self.assertEqual(status, 400, message)

    def test_update_task_nonexistent(self):
        status, error, message = put_request("/task/333", json.dumps({"kr_id": 9, "value": "value", "state": "active"}))
        self.assertEqual(status, 404, message)
        self.assertTrue("id '333' not found" in error, message)

    def test_update_task_invalid_id(self):
        status, error, message = put_request("/task/x", json.dumps({"kr_id": 9, "value": "value", "state": "active"}))
        self.assertIn(status, (400, 422), message)

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
        self.assertIn(status, (400, 422), message)

    def test_delete_task_no_id(self):
        status, error, message = delete_request("/task")
        assert_method_not_allowed(self, status, error, message)


if __name__ == '__main__':
    unittest.main()
