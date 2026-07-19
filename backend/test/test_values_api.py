import json
import unittest

from utils import delete_request, get_request, post_request, put_request, assert_bad_url


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
        self.assertIn(status, (400, 422), message)

    def test_get_value_no_id(self):
        status, error, message = get_request("/value")
        assert_bad_url(self, status, error, message)

    def test_get_values(self):
        status, values, message = get_request("/values")
        self.assertEqual(status, 200, message)
        self.assertEqual(len(values), 5, message)
        self.assertEqual(values[0]["name"], "Zdravie", message)

    def test_get_subvalues_uses_test_firebase_data(self):
        status, subvalues, message = get_request('/value/1/subvalue')

        self.assertEqual(status, 200, message)
        self.assertEqual([subvalue['name'] for subvalue in subvalues], ['default', 'Exercise', 'Recovery'], message)
        self.assertEqual(subvalues[1]['ideas'][0], {
            'id': 'idea-4', 'name': 'Walk', 'description': '30 minutes after lunch.',
        }, message)

    def test_get_subvalues_includes_an_empty_default_list_when_value_has_no_firebase_data(self):
        status, subvalues, message = get_request('/value/2/subvalue')

        self.assertEqual(status, 200, message)
        self.assertEqual(subvalues, [{'id': '0', 'name': 'default', 'ideas': []}], message)

    def test_create_subvalue(self):
        status, subvalue, message = post_request('/value/4/subvalue', json.dumps({'name': 'Nutrition'}))

        self.assertEqual(status, 201, message)
        self.assertEqual(subvalue['name'], 'Nutrition', message)
        self.assertEqual(subvalue['ideas'], [], message)

        status, subvalues, message = get_request('/value/4/subvalue')
        self.assertIn(subvalue, subvalues, message)

    def test_update_subvalue(self):
        status, subvalue, message = put_request('/value/4/subvalue/1', json.dumps({'name': 'Trials'}))

        self.assertEqual(status, 200, message)
        self.assertEqual(subvalue, {'id': '1', 'name': 'Trials'}, message)

    def test_delete_subvalue(self):
        status, subvalue, message = post_request('/value/4/subvalue', json.dumps({'name': 'Temporary'}))
        self.assertEqual(status, 201, message)

        status, _, message = delete_request('/value/4/subvalue/' + subvalue['id'])
        self.assertEqual(status, 204, message)

        status, subvalues, message = get_request('/value/4/subvalue')
        self.assertNotIn(subvalue, subvalues, message)

    def test_default_subvalue_cannot_be_deleted(self):
        status, error, message = delete_request('/value/1/subvalue/0')

        self.assertEqual(status, 400, message)
        self.assertEqual(error, 'default subvalue cannot be deleted', message)

    def test_create_idea_in_a_specific_subvalue(self):
        status, idea, message = post_request('/value/1/subvalue/2/idea', json.dumps({
            'name': 'Stretch',
            'description': 'After training.',
        }))

        self.assertEqual(status, 201, message)
        self.assertEqual(idea['name'], 'Stretch', message)
        self.assertEqual(idea['description'], 'After training.', message)

        status, subvalues, message = get_request('/value/1/subvalue')
        recovery = next(subvalue for subvalue in subvalues if subvalue['id'] == '2')
        created_idea = next(item for item in recovery['ideas'] if item['id'] == idea['id'])
        self.assertEqual(created_idea, idea, message)

    def test_update_idea_in_a_specific_subvalue(self):
        status, idea, message = put_request('/value/1/subvalue/1/idea/idea-4', json.dumps({
            'name': 'Run',
            'description': 'Twenty minutes after work.',
        }))

        self.assertEqual(status, 200, message)
        self.assertEqual(idea, {
            'id': 'idea-4',
            'name': 'Run',
            'description': 'Twenty minutes after work.',
        }, message)

    def test_move_idea_to_another_subvalue(self):
        status, idea, message = post_request('/value/4/subvalue/0/idea', json.dumps({
            'name': 'Temporary idea',
            'description': '',
        }))
        self.assertEqual(status, 201, message)

        status, moved_idea, message = put_request('/value/4/subvalue/0/idea/' + idea['id'] + '/move', json.dumps({
            'target_subvalue_id': '1',
        }))
        self.assertEqual(status, 200, message)
        self.assertEqual(moved_idea, idea, message)

        status, subvalues, message = get_request('/value/4/subvalue')
        default_subvalue = next(subvalue for subvalue in subvalues if subvalue['id'] == '0')
        target_subvalue = next(subvalue for subvalue in subvalues if subvalue['id'] == '1')
        self.assertNotIn(idea, default_subvalue['ideas'], message)
        self.assertIn(idea, target_subvalue['ideas'], message)

    def test_get_value_check_tasks_count(self):
        status, value, message = get_request("/value/5")
        self.assertEqual(status, 200, message)
        objective = next(obj for obj in value["objectives"] if obj["id"] == 13)
        key_result = next(kr for kr in objective["key_results"] if kr["id"] == 22)

        self.assertEqual(key_result["all_tasks_count"], 8, message)
        self.assertEqual(key_result["resolved_tasks_count"], 4, message)


if __name__ == '__main__':
    unittest.main()
