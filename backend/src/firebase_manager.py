from classes import Idea


DEFAULT_SUBVALUE_ID = '0'
DEFAULT_SUBVALUE_NAME = 'default'
db = None


def _value_path(value_id: str) -> str:
    return f'values/{value_id}'


def _subvalue_path(value_id: str, subvalue_id: str) -> str:
    return f'{_value_path(value_id)}/subvalues/{subvalue_id}'


def _ideas_path(value_id: str, subvalue_id: str) -> str:
    return f'{_subvalue_path(value_id, subvalue_id)}/ideas'


def _firebase_items(data):
    """Support Firebase nodes returned as either keyed objects or arrays."""
    if isinstance(data, dict):
        return data.items()
    if isinstance(data, list):
        return ((str(index), value) for index, value in enumerate(data) if value is not None)
    return ()


def _firebase_mapping(data):
    return {str(key): value for key, value in _firebase_items(data)}


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
        current = _firebase_mapping(current)
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
    subvalues = _firebase_mapping(db.reference(f'{_value_path(value_id)}/subvalues').get())
    if DEFAULT_SUBVALUE_ID not in subvalues:
        subvalues = {
            DEFAULT_SUBVALUE_ID: {
                'name': DEFAULT_SUBVALUE_NAME,
                'ideas': {},
            },
            **subvalues,
        }
    return [
        {
            'id': str(subvalue_id),
            'name': subvalue.get('name', '') if isinstance(subvalue, dict) else '',
            'ideas': [
                {
                    'id': str(idea_key),
                    'name': idea.get('name', '') if isinstance(idea, dict) else str(idea),
                    'description': idea.get('description', '') if isinstance(idea, dict) else '',
                }
                for idea_key, idea in _firebase_items(subvalue.get('ideas') if isinstance(subvalue, dict) else None)
            ],
        }
        for subvalue_id, subvalue in subvalues.items()
    ]


def get_ideas_of_value(value_id: str) -> list[Idea]:
    """Compatibility API: return names of ideas in the default subvalue."""
    ideas = db.reference(_ideas_path(value_id, DEFAULT_SUBVALUE_ID)).get()
    return [Idea(str(idea_key), idea.get('name', '') if isinstance(idea, dict) else idea)
            for idea_key, idea in _firebase_items(ideas)]


def add_idea(value_id: str, idea: str) -> str:
    """Compatibility API: add an idea to the default subvalue."""
    return add_idea_to_subvalue(value_id, DEFAULT_SUBVALUE_ID, str(idea), '')


def delete_idea(value_id: str, idea_id: str):
    """Compatibility API: delete an idea from the default subvalue."""
    delete_idea_from_subvalue(value_id, DEFAULT_SUBVALUE_ID, idea_id)
