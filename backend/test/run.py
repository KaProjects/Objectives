import sqlite3
import unittest
import sys
import threading
from pathlib import Path

from werkzeug.serving import WSGIRequestHandler, make_server

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / 'src'))

from app import create_app
from auth_manager import AuthManager
from database_manager import DatabaseManager
import firebase_manager
from service import Service

class QuietRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        pass


def create_test_database():
    def connect():
        connection = sqlite3.connect('test.db')
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    return DatabaseManager(
        connect=connect,
        placeholder='?',
        integrity_errors=(sqlite3.IntegrityError,),
    )


def initialize_test_database():
    database = create_test_database()
    with database.open() as session:
        session.execute_scripts(['sql/drop_tables.sql', 'sql/create_tables.sql', 'test/data.sql'])
    return database


def init_auth_manager():
    return AuthManager('test-token-secret')


def init_firebase():
    from devel.run import init_firebase as init_development_firebase
    return init_development_firebase(Path(__file__).resolve().with_name('data.json'))


def create_test_app():
    database = initialize_test_database()
    firebase = init_firebase()
    auth = init_auth_manager()
    return create_app(Service(database, firebase, auth), auth, 'http://*:*', port=7890, debug=True)

def run_tests():
    app = create_test_app()
    server = make_server(
        '127.0.0.1', app.config['SERVER_PORT'], app,
        request_handler=QuietRequestHandler,
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        import test_key_results_api
        import test_objectives_api
        import test_tasks_api
        import test_values_api
        import test_error_contract_api
        import test_errors
        import test_database_manager
        import test_json_encoder
        import test_auth_manager
        import test_firebase_manager

        test_runner = unittest.TextTestRunner(verbosity=1)
        results = [
            test_runner.run(unittest.TestLoader().loadTestsFromModule(module))
            for module in (
                test_values_api, test_objectives_api, test_key_results_api,
                test_tasks_api, test_error_contract_api, test_errors, test_database_manager,
                test_json_encoder, test_auth_manager, test_firebase_manager,
            )
        ]
        if not all(result.wasSuccessful() for result in results):
            raise SystemExit(1)
    finally:
        server.shutdown()
        server_thread.join()


if __name__ == '__main__':
    if '--serve' in sys.argv:
        app = create_test_app()
        app.run(port=app.config['SERVER_PORT'], debug=app.config['SERVER_DEBUG'], host='0.0.0.0')
    else:
        run_tests()
