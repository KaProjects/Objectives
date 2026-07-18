import copy
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import firebase_manager

firebase_admin_script_path = Path(__file__).resolve().parents[1] / 'script' / 'firebase.py'
firebase_admin_spec = importlib.util.spec_from_file_location('firebase_admin_script', firebase_admin_script_path)
firebase_admin_script = importlib.util.module_from_spec(firebase_admin_spec)
firebase_admin_spec.loader.exec_module(firebase_admin_script)


class FakePushResult:
    def __init__(self, key):
        self.key = key


class FakeReference:
    def __init__(self, store, path=''):
        self.store = store
        self.path = [part for part in path.split('/') if part]

    def _parent_and_key(self, create=False):
        target = self.store
        for part in self.path[:-1]:
            if create:
                target = target.setdefault(part, {})
            else:
                target = target.get(part, {})
        return target, self.path[-1] if self.path else None

    def _value(self, create=False):
        if not self.path:
            return self.store
        parent, key = self._parent_and_key(create)
        if create:
            return parent.setdefault(key, {})
        return parent.get(key)

    def get(self):
        return copy.deepcopy(self._value())

    def set(self, value):
        if not self.path:
            self.store.clear()
            self.store.update(copy.deepcopy(value or {}))
            return
        parent, key = self._parent_and_key(create=True)
        parent[key] = copy.deepcopy(value)

    def update(self, value):
        self._value(create=True).update(copy.deepcopy(value))

    def delete(self):
        if not self.path:
            self.store.clear()
            return
        parent, key = self._parent_and_key()
        parent.pop(key, None)

    def push(self, value):
        target = self._value(create=True)
        key = f'idea-{len(target) + 1}'
        target[key] = copy.deepcopy(value)
        return FakePushResult(key)

    def transaction(self, callback):
        self.set(callback(self.get()))


class FakeDb:
    def __init__(self, store):
        self.store = store

    def reference(self, path=''):
        return FakeReference(self.store, path)


class TestFirebaseManager(unittest.TestCase):
    def setUp(self):
        self.store = {}
        self.db_patch = patch.object(firebase_manager, 'db', FakeDb(self.store))
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

    def test_test_environment_uses_in_memory_firebase_data(self):
        original_db = firebase_manager.db
        try:
            with patch.dict(os.environ, {'APP_ENV': 'test'}, clear=False):
                firebase_manager.init_firebase()
            self.assertEqual(firebase_manager.get_subvalues('1')[0]['name'], 'default')
        finally:
            firebase_manager.db = original_db

    def test_migration_script_creates_default_subvalues(self):
        self.store.update({
            'labels': {'1': 'Health'},
            'ideas': {'1': {'idea-a': 'Drink water', 'idea-b': 'Walk'}},
        })

        with patch.object(firebase_admin_script, 'db', FakeDb(self.store)):
            self.assertEqual(firebase_admin_script.migrate_legacy_data(), 1)
        self.assertEqual(self.store['values'], {
            '1': {
                'name': 'Health',
                'subvalues': {
                    '0': {
                        'name': 'default',
                        'ideas': {
                            'idea-a': {'name': 'Drink water', 'description': ''},
                            'idea-b': {'name': 'Walk', 'description': ''},
                        },
                    },
                },
            },
        })

    def test_migration_script_supports_array_like_firebase_nodes(self):
        self.store.update({
            'labels': [None, 'Health'],
            'ideas': [None, {'idea-a': 'Drink water'}],
        })

        with patch.object(firebase_admin_script, 'db', FakeDb(self.store)):
            firebase_admin_script.migrate_legacy_data()

        self.assertEqual(self.store['values']['1']['name'], 'Health')
        self.assertEqual(self.store['values']['1']['subvalues']['0']['ideas'], {
            'idea-a': {'name': 'Drink water', 'description': ''},
        })

    def test_backup_and_restore_scripts(self):
        self.store.update({'values': {'1': {'name': 'Health'}}})
        with patch.object(firebase_admin_script, 'db', FakeDb(self.store)):
            backup = firebase_admin_script.backup_data()
        self.store.clear()

        with patch.object(firebase_admin_script, 'db', FakeDb(self.store)):
            firebase_admin_script.restore_data(backup)

        self.assertEqual(self.store, {'values': {'1': {'name': 'Health'}}})


if __name__ == '__main__':
    unittest.main()
