from functools import wraps
from flask import request, Response
from auth_manager import validate_token


def authenticated(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return Response(response="missing auth header", status=401, mimetype="text/plain")
        if not token.startswith("Bearer "):
            return Response(response="invalid token format", status=401, mimetype="text/plain")
        if not validate_token(token.split(" ")[1]):
            return Response(response="invalid token", status=401, mimetype="text/plain")
        return f(*args, **kwargs)

    return decorated


