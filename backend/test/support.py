import atexit
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


from app import create_app
from auth_manager import AuthManager
from database_manager import DatabaseManager
from devel.fake_firebase import create_memory_database
import firebase_manager
from service import Service
from utils import configure_client


def _mysql_settings():
    names = {
        'host': 'MYSQL_TEST_HOST',
        'port': 'MYSQL_TEST_PORT',
        'user': 'MYSQL_TEST_USER',
        'password': 'MYSQL_TEST_PASSWORD',
        'database': 'MYSQL_TEST_DATABASE',
    }
    missing = [environment_name for environment_name in names.values() if not os.getenv(environment_name)]
    if missing:
        raise RuntimeError('Missing MySQL test settings: ' + ', '.join(missing))

    settings = {name: os.environ[environment_name] for name, environment_name in names.items()}
    settings['port'] = int(settings['port'])
    return settings


def create_test_database(database_path=None):
    if os.getenv('TEST_DATABASE', 'sqlite').casefold() == 'mysql':
        import mysql.connector

        settings = _mysql_settings()
        return DatabaseManager(
            connect=lambda: mysql.connector.connect(**settings, buffered=True),
            placeholder='%s',
            integrity_errors=(mysql.connector.IntegrityError,),
        )

    if database_path is None:
        raise ValueError('database_path is required for SQLite tests')

    def connect():
        connection = sqlite3.connect(database_path)
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    return DatabaseManager(
        connect=connect,
        placeholder='?',
        integrity_errors=(sqlite3.IntegrityError,),
    )


def _execute_mysql_scripts(session, scripts):
    with session.cursor(commit=True) as cursor:
        for script in scripts:
            statements = Path(script).read_text(encoding='utf-8').split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)


def _execute_sqlite_scripts(session, scripts):
    with session.cursor(commit=True) as cursor:
        for script in scripts:
            cursor.executescript(Path(script).read_text(encoding='utf-8'))


def initialize_test_database(database_path=None):
    database = create_test_database(database_path)
    mysql = os.getenv('TEST_DATABASE', 'sqlite').casefold() == 'mysql'
    schema = 'create_tables-mysql.sql' if mysql else 'create_tables.sql'
    scripts = [
        str(BACKEND_ROOT / 'sql' / 'drop_tables.sql'),
        str(BACKEND_ROOT / 'sql' / schema),
        str(BACKEND_ROOT / 'test' / 'data.sql'),
    ]
    with database.open() as session:
        if mysql:
            _execute_mysql_scripts(session, scripts)
        else:
            _execute_sqlite_scripts(session, scripts)
    return database


def init_auth_manager():
    return AuthManager('test-token-secret')


def init_firebase(data_path=None):
    data_path = data_path or BACKEND_ROOT / 'test' / 'data.json'
    firebase_manager.db = create_memory_database(Path(data_path))
    return firebase_manager


def create_test_app(database_path=None):
    database = initialize_test_database(database_path)
    firebase = init_firebase()
    auth = init_auth_manager()
    app = create_app(Service(database, firebase, auth), auth, 'http://*:*', port=0, debug=False)
    app.config.update(TESTING=True)
    return app, auth


_runtime = None
_temporary_directory = None


def _get_runtime():
    global _runtime, _temporary_directory
    if _runtime is None:
        database_path = None
        if os.getenv('TEST_DATABASE', 'sqlite').casefold() != 'mysql':
            _temporary_directory = tempfile.TemporaryDirectory(prefix='objectives-tests-')
            atexit.register(_temporary_directory.cleanup)
            database_path = Path(_temporary_directory.name) / 'test.db'

        app, auth = create_test_app(database_path)
        _runtime = app, auth, database_path
    return _runtime


class ApiTestCase(unittest.TestCase):
    """Provide every API test with isolated SQL and Firebase fixtures."""

    def setUp(self):
        super().setUp()
        self.app, auth, database_path = _get_runtime()
        initialize_test_database(database_path)
        init_firebase()
        self.client = self.app.test_client()
        self.token = auth.generate_token('test-user')
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}
        configure_client(self.client, self.token)

    def tearDown(self):
        configure_client(None, None)
        super().tearDown()
