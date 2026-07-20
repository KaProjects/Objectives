import sqlite3
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / 'src'))

from app import create_app
from auth_manager import AuthManager
from database_manager import DatabaseManager
from devel.fake_firebase import create_memory_database
import firebase_manager
from service import Service


def create_development_database():
    def connect():
        connection = sqlite3.connect('devel.db')
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    return DatabaseManager(
        connect=connect,
        placeholder='?',
        integrity_errors=(sqlite3.IntegrityError,),
    )


def initialize_development_database():
    database = create_development_database()
    with database.open() as session:
        session.execute_scripts(['sql/drop_tables.sql', 'sql/create_tables.sql', 'devel/data.sql'])
    return database


def init_auth_manager():
    return AuthManager('development-token-secret')


def init_firebase(data_path=None):
    data_path = data_path or Path(__file__).resolve().with_name('data.json')
    firebase_manager.db = create_memory_database(data_path)
    return firebase_manager


def create_development_app():
    database = initialize_development_database()
    firebase = init_firebase()
    auth = init_auth_manager()
    return create_app(Service(database, firebase, auth), auth, 'http://localhost:5173', port=7702, debug=True)


if __name__ == '__main__':
    app = create_development_app()
    app.run(port=app.config['SERVER_PORT'], debug=app.config['SERVER_DEBUG'], host='0.0.0.0')
