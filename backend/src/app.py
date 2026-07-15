import os
import sys

from flask import Flask
from flask_cors import CORS

import database_manager
import firebase_manager
from endpoints import rest


def configure_runtime(mode):
    if mode == 'prod':
        database_manager.datasource = database_manager.DataSource.PRODUCTION
        port, debug = 7777, False
        if not os.getenv('FRONTEND_ORIGIN'):
            raise RuntimeError('FRONTEND_ORIGIN must be set in production')
        origins = os.getenv('FRONTEND_ORIGIN')
    elif mode == 'dev':
        database_manager.datasource = database_manager.DataSource.DEVEL
        database_manager.DatabaseManager()\
            .execute_scripts(["sql/drop_tables.sql", "sql/create_tables.sql", "sql/data_dev.sql"])
        port, debug = 7702, True
        origins = "http://localhost:5173"
    elif mode == 'test':
        database_manager.datasource = database_manager.DataSource.TEST
        database_manager.DatabaseManager()\
            .execute_scripts(["sql/drop_tables.sql", "sql/create_tables.sql", "sql/data_test.sql"])
        port, debug = 7890, True
        origins = "http://*:*"
    else:
        raise ValueError("mode must be one of: test, dev, prod")

    return port, debug, origins


def create_app(mode=None):
    """Create an application for Flask tooling and production WSGI servers."""
    mode = mode or os.getenv('APP_ENV', 'prod')
    os.environ['APP_ENV'] = mode
    port, debug, origins = configure_runtime(mode)

    firebase_manager.init_firebase()
    app = Flask(__name__)
    CORS(rest, resources={r"/*": {"origins": origins}})
    app.register_blueprint(rest)
    app.config["RESTX_MASK_SWAGGER"] = False
    app.config['SERVER_PORT'] = port
    app.config['SERVER_DEBUG'] = debug

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    return app


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception("usage: python3 app.py test/dev/prod")

    app = create_app(sys.argv[1])
    app.run(port=app.config['SERVER_PORT'], debug=app.config['SERVER_DEBUG'], host="0.0.0.0")
else:
    # Gunicorn imports this module and serves this WSGI application.
    app = create_app()
