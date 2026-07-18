import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import firebase_manager
from run import init_firebase
from devel.fake_firebase import MemoryDatabase


class TestFirebaseManager(unittest.TestCase):
    def setUp(self):
        self.store = {}
        self.db_patch = patch.object(firebase_manager, 'db', MemoryDatabase(self.store))
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

    def test_create_value_includes_default_subvalue(self):
        firebase_manager.create_value('1', 'Health')

        self.assertEqual(self.store, {
            'values': {
                '1': {
                    'name': 'Health',
                    'subvalues': {'0': {'name': 'default', 'ideas': {}}},
                },
            },
        })

    def test_subvalue_and_idea_crud(self):
        firebase_manager.create_value('1', 'Health')
        subvalue_id = firebase_manager.create_subvalue('1', 'Running')
        self.assertEqual(subvalue_id, '1')

        firebase_manager.update_subvalue('1', subvalue_id, 'Cycling')
        idea_key = firebase_manager.add_idea_to_subvalue('1', subvalue_id, 'Ride', '30 minutes')
        firebase_manager.update_idea('1', subvalue_id, idea_key, 'Ride outside', '45 minutes')

        idea = self.store['values']['1']['subvalues']['1']['ideas'][idea_key]
        self.assertEqual(idea, {'name': 'Ride outside', 'description': '45 minutes'})

        firebase_manager.delete_idea_from_subvalue('1', subvalue_id, idea_key)
        firebase_manager.delete_subvalue('1', subvalue_id)
        self.assertNotIn('1', self.store['values']['1']['subvalues'])

    def test_get_subvalues_returns_each_idea_list(self):
        firebase_manager.create_value('1', 'Health')
        fitness_id = firebase_manager.create_subvalue('1', 'Fitness')
        firebase_manager.add_idea_to_subvalue('1', fitness_id, 'Run', '30 minutes')

        self.assertEqual(firebase_manager.get_subvalues('1'), [
            {'id': '0', 'name': 'default', 'ideas': []},
            {'id': '1', 'name': 'Fitness', 'ideas': [
                {'id': 'idea-1', 'name': 'Run', 'description': '30 minutes'},
            ]},
        ])

    def test_adding_ideas_to_a_list_with_non_sequential_keys_does_not_overwrite_them(self):
        firebase_manager.create_value('1', 'Health')
        subvalue_id = firebase_manager.create_subvalue('1', 'Exercise')
        ideas = self.store['values']['1']['subvalues'][subvalue_id]['ideas']
        ideas.update({
            'idea-4': {'name': 'Walk', 'description': ''},
            'idea-5': {'name': 'Strength train', 'description': ''},
            'idea-6': {'name': 'Stretch', 'description': ''},
        })

        first_new_id = firebase_manager.add_idea_to_subvalue('1', subvalue_id, 'Run', '')
        second_new_id = firebase_manager.add_idea_to_subvalue('1', subvalue_id, 'Swim', '')

        self.assertEqual((first_new_id, second_new_id), ('idea-7', 'idea-8'))
        self.assertEqual([idea['name'] for idea in ideas.values()], [
            'Walk', 'Strength train', 'Stretch', 'Run', 'Swim',
        ])

    def test_test_runtime_uses_in_memory_firebase_data(self):
        original_db = firebase_manager.db
        try:
            init_firebase()
            self.assertEqual(firebase_manager.get_subvalues('1')[0]['name'], 'default')
        finally:
            firebase_manager.db = original_db


if __name__ == '__main__':
    unittest.main()
