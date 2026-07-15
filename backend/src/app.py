import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS

import database_manager
import firebase_manager
from endpoints import rest
from errors import ApiError, InternalServerError, error_body


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

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify(error_body(error)), error.status_code

    def handle_http_error(error):
        return jsonify({
            'error': {
                'code': error.name.lower().replace(' ', '_'),
                'message': error.description,
            }
        }), error.code

    @app.errorhandler(404)
    def handle_not_found(error):
        return handle_http_error(error)

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return handle_http_error(error)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception('Unhandled server exception')
        internal_error = InternalServerError()
        return jsonify(error_body(internal_error)), internal_error.status_code

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
