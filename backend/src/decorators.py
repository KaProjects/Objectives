from functools import wraps

from flask import current_app, request, Response


AUTH_COOKIE_NAME = 'objectives_session'
CLIENT_HEADER_NAME = 'X-Objectives-Client'
CLIENT_HEADER_VALUE = 'web'
UNSAFE_METHODS = frozenset({'POST', 'PUT', 'PATCH', 'DELETE'})


def authenticated(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(AUTH_COOKIE_NAME)
        if not token:
            return Response(response="missing auth cookie", status=401, mimetype="text/plain")
        if not current_app.extensions['auth'].validate_token(token):
            return Response(response="invalid token", status=401, mimetype="text/plain")
        return f(*args, **kwargs)

    return decorated
