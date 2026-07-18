import copy
import json
from pathlib import Path


class MemoryReference:
    def __init__(self, store, path=''):
        self.store = store
        self.path = [part for part in path.split('/') if part]

    def _parent(self, create=False):
        value = self.store
        for part in self.path[:-1]:
            value = value.setdefault(part, {}) if create else value.get(part, {})
        return value, self.path[-1] if self.path else None

    def _value(self, create=False):
        if not self.path:
            return self.store
        parent, key = self._parent(create)
        return parent.setdefault(key, {}) if create else parent.get(key)

    def get(self):
        return copy.deepcopy(self._value())

    def set(self, value):
        parent, key = self._parent(True)
        if key is None:
            self.store.clear()
            self.store.update(copy.deepcopy(value or {}))
        else:
            parent[key] = copy.deepcopy(value)

    def update(self, value):
        self._value(True).update(copy.deepcopy(value))

    def delete(self):
        parent, key = self._parent()
        parent.pop(key, None)

    def push(self, value):
        target = self._value(True)
        existing_numbers = [
            int(key.removeprefix('idea-'))
            for key in target
            if key.startswith('idea-') and key.removeprefix('idea-').isdigit()
        ]
        key = f'idea-{max(existing_numbers, default=0) + 1}'
        target[key] = copy.deepcopy(value)
        return type('PushResult', (), {'key': key})()

    def transaction(self, callback):
        self.set(callback(self.get()))


class MemoryDatabase:
    def __init__(self, data=None):
        self.store = data if data is not None else {}

    def reference(self, path=''):
        return MemoryReference(self.store, path)


def create_memory_database(data_path: Path):
    with data_path.open(encoding='utf-8') as file:
        return MemoryDatabase(json.load(file))
