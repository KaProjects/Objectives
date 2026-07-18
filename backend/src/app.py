from flask import Flask, jsonify
from flask_cors import CORS

from endpoints import rest
from errors import ApiError, InternalServerError, error_body


def create_app(service, auth, origins, port, debug):
    """Create the API from dependencies supplied by a runtime bootstrap."""
    app = Flask(__name__)
    app.extensions['auth'] = auth
    app.extensions['service'] = service
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
