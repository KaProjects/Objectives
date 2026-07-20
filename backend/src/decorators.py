from functools import wraps

from flask import current_app, request, Response


def authenticated(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return Response(response="missing auth header", status=401, mimetype="text/plain")
        if not token.startswith("Bearer "):
            return Response(response="invalid token format", status=401, mimetype="text/plain")
        if not current_app.extensions['auth'].validate_token(token.split(" ")[1]):
            return Response(response="invalid token", status=401, mimetype="text/plain")
        return f(*args, **kwargs)

    return decorated

