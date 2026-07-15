import unittest

import requests

from utils import origin, token


class TestErrorContractApi(unittest.TestCase):
    headers = {'Authorization': 'Bearer ' + token}

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.headers.get('content-type'), 'application/json')
        body = response.json()
        self.assertEqual(body['error']['code'], code)
        self.assertIsInstance(body['error']['message'], str)
        self.assertTrue(body['error']['message'])

    def test_invalid_id_is_a_validation_error(self):
        response = requests.get(origin + '/value/not-an-id', headers=self.headers)
        self.assert_error(response, 400, 'validation_error')

    def test_missing_resource_is_not_found(self):
        response = requests.get(origin + '/value/99999', headers=self.headers)
        self.assert_error(response, 404, 'not_found')

    def test_invalid_state_is_unprocessable(self):
        response = requests.put(
            origin + '/objective/8/state',
            json={'state': 'completed'},
            headers=self.headers,
        )
        self.assert_error(response, 422, 'unprocessable_entity')

    def test_delete_with_key_results_is_a_conflict(self):
        response = requests.delete(origin + '/objective/14', headers=self.headers)
        self.assert_error(response, 409, 'conflict')
