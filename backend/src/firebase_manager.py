import copy
import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db

from classes import Idea


DEFAULT_SUBVALUE_ID = '0'
DEFAULT_SUBVALUE_NAME = 'default'
DEVELOPMENT_DATA_PATH = Path(__file__).resolve().parent.parent / 'json' / 'data_dev.json'


def _load_development_data():
    with DEVELOPMENT_DATA_PATH.open(encoding='utf-8') as data_file:
        return json.load(data_file)


class _MemoryPushResult:
    def __init__(self, key):
        self.key = key


class _MemoryReference:
    def __init__(self, store, path=''):
        self.store = store
        self.path = [part for part in path.split('/') if part]

    def _parent_and_key(self, create=False):
        target = self.store
        for part in self.path[:-1]:
            target = target.setdefault(part, {}) if create else target.get(part, {})
        return target, self.path[-1] if self.path else None

    def _value(self, create=False):
        if not self.path:
            return self.store
        parent, key = self._parent_and_key(create)
        return parent.setdefault(key, {}) if create else parent.get(key)

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
        return _MemoryPushResult(key)

    def transaction(self, callback):
        self.set(callback(self.get()))


class _MemoryDatabase:
    def __init__(self, data):
        self.data = copy.deepcopy(data)

    def reference(self, path=''):
        return _MemoryReference(self.data, path)


def init_firebase():
    """Initialize Firebase once for the current process."""
    global db
    if os.getenv('APP_ENV') in {'dev', 'test'}:
        db = _MemoryDatabase(_load_development_data())
        return

    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    cred = credentials.Certificate('envs_firebase_sa.json')
    with open('envs_firebase_db.json') as envs_file:
        envs = json.load(envs_file)
    firebase_admin.initialize_app(cred, envs)


def _value_path(value_id: str) -> str:
    return f'values/{value_id}'


def _subvalue_path(value_id: str, subvalue_id: str) -> str:
    return f'{_value_path(value_id)}/subvalues/{subvalue_id}'


def _ideas_path(value_id: str, subvalue_id: str) -> str:
    return f'{_subvalue_path(value_id, subvalue_id)}/ideas'


def create_value(value_id: str, name: str):
    """Create or replace a value with its required default subvalue."""
    db.reference(_value_path(value_id)).set({
        'name': name,
        'subvalues': {
            DEFAULT_SUBVALUE_ID: {
                'name': DEFAULT_SUBVALUE_NAME,
                'ideas': {},
            },
        },
    })


def create_subvalue(value_id: str, name: str) -> str:
    """Create the next numeric subvalue ID atomically."""
    subvalues_ref = db.reference(f'{_value_path(value_id)}/subvalues')
    created_id = None

    def add_subvalue(current):
        nonlocal created_id
        current = current or {}
        numeric_ids = [int(subvalue_id) for subvalue_id in current if str(subvalue_id).isdigit()]
        created_id = str(max(numeric_ids, default=-1) + 1)
        current[created_id] = {'name': name, 'ideas': {}}
        return current

    subvalues_ref.transaction(add_subvalue)
    return created_id


def update_subvalue(value_id: str, subvalue_id: str, name: str):
    db.reference(_subvalue_path(value_id, subvalue_id)).update({'name': name})


def delete_subvalue(value_id: str, subvalue_id: str):
    db.reference(_subvalue_path(value_id, subvalue_id)).delete()


def add_idea_to_subvalue(value_id: str, subvalue_id: str, name: str, description: str) -> str:
    return db.reference(_ideas_path(value_id, subvalue_id)).push({
        'name': name,
        'description': description,
    }).key


def update_idea(value_id: str, subvalue_id: str, idea_key: str, name: str, description: str):
    db.reference(f'{_ideas_path(value_id, subvalue_id)}/{idea_key}').update({
        'name': name,
        'description': description,
    })


def delete_idea_from_subvalue(value_id: str, subvalue_id: str, idea_key: str):
    db.reference(f'{_ideas_path(value_id, subvalue_id)}/{idea_key}').delete()


def get_subvalues(value_id: str) -> list[dict]:
    subvalues = db.reference(f'{_value_path(value_id)}/subvalues').get() or {}
    return [
        {
            'id': str(subvalue_id),
            'name': subvalue.get('name', ''),
            'ideas': [
                {
                    'id': str(idea_key),
                    'name': idea.get('name', '') if isinstance(idea, dict) else str(idea),
                    'description': idea.get('description', '') if isinstance(idea, dict) else '',
                }
                for idea_key, idea in (subvalue.get('ideas') or {}).items()
            ],
        }
        for subvalue_id, subvalue in subvalues.items()
    ]


def get_ideas_of_value(value_id: str) -> list[Idea]:
    """Compatibility API: return names of ideas in the default subvalue."""
    ideas = db.reference(_ideas_path(value_id, DEFAULT_SUBVALUE_ID)).get() or {}
    return [Idea(idea_key, idea.get('name', '') if isinstance(idea, dict) else idea)
            for idea_key, idea in ideas.items()]


def add_idea(value_id: str, idea: str) -> str:
    """Compatibility API: add an idea to the default subvalue."""
    return add_idea_to_subvalue(value_id, DEFAULT_SUBVALUE_ID, str(idea), '')


def delete_idea(value_id: str, idea_id: str):
    """Compatibility API: delete an idea from the default subvalue."""
    delete_idea_from_subvalue(value_id, DEFAULT_SUBVALUE_ID, idea_id)
