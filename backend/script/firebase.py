"""Standalone Firebase administration utility.

Run from the backend directory:

    ./.venv/bin/python script/firebase.py backup
    ./.venv/bin/python script/firebase.py restore <backup.json>
    ./.venv/bin/python script/firebase.py migrate-1.2-1.3

The migration copies legacy labels and ideas into the values/subvalues structure.
It keeps the legacy Firebase branches unchanged; create a backup first.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

import firebase_admin
from firebase_admin import credentials, db


PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SUBVALUE_ID = '0'
DEFAULT_SUBVALUE_NAME = 'default'


def init_firebase():
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    credential = credentials.Certificate(PROJECT_ROOT / 'envs_firebase_sa.json')
    with (PROJECT_ROOT / 'envs_firebase_db.json').open(encoding='utf-8') as envs_file:
        firebase_admin.initialize_app(credential, json.load(envs_file))


def backup_data():
    return db.reference('/').get()


def create_backup(output_path: Path):
    with output_path.open('w', encoding='utf-8') as output_file:
        json.dump(backup_data(), output_file, indent=2, ensure_ascii=False)
    print(f'Firebase backup written to {output_path}')


def restore_data(data):
    db.reference('/').set(data)


def restore_backup(backup_path: Path):
    with backup_path.open(encoding='utf-8') as backup_file:
        restore_data(json.load(backup_file))
    print(f'Firebase restored from {backup_path}')


def firebase_items(data):
    if isinstance(data, dict):
        return data.items()
    if isinstance(data, list):
        return ((str(index), value) for index, value in enumerate(data) if value is not None)
    return ()


def migrate_legacy_data():
    """Write the new values tree while retaining legacy labels and ideas."""
    labels = dict(firebase_items(db.reference('labels').get()))
    legacy_ideas = dict(firebase_items(db.reference('ideas').get()))
    values = {}

    for value_id in set(labels) | set(legacy_ideas):
        ideas = legacy_ideas.get(value_id) or {}
        values[str(value_id)] = {
            'name': labels.get(value_id, ''),
            'subvalues': {
                DEFAULT_SUBVALUE_ID: {
                    'name': DEFAULT_SUBVALUE_NAME,
                    'ideas': {
                        str(idea_key): {'name': str(idea_name), 'description': ''}
                        for idea_key, idea_name in firebase_items(ideas)
                    },
                },
            },
        }

    db.reference('values').set(values)
    return len(values)


def main():
    parser = argparse.ArgumentParser(description='Firebase administration commands.')
    commands = parser.add_subparsers(dest='command', required=True)

    commands.add_parser('backup', help='Write a timestamped Firebase JSON backup.')

    restore_parser = commands.add_parser('restore', help='Restore Firebase from a JSON backup.')
    restore_parser.add_argument('backup', type=Path)

    commands.add_parser('migrate-1.2-1.3', help='Migrate legacy labels and ideas to values/subvalues.')
    args = parser.parse_args()

    init_firebase()
    if args.command == 'backup':
        output = Path(f'firebase-backup-{datetime.now():%Y%m%d-%H%M%S}.json')
        create_backup(output)
    elif args.command == 'restore':
        restore_backup(args.backup)
    else:
        migrated_values = migrate_legacy_data()
        print(f'Migrated {migrated_values} value(s) to the new Firebase structure.')


if __name__ == '__main__':
    main()
