import json
import os

from typing import Union
from hashlib import sha256
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


TOKEN_MAX_AGE_SECONDS = 18_000
DEVELOPMENT_TOKEN_SECRET = 'development-token-secret'


def token_secret() -> str:
    secret = os.getenv('AUTH_TOKEN_SECRET')
    if secret:
        return secret
    if os.getenv('APP_ENV') in {'dev', 'test'}:
        return DEVELOPMENT_TOKEN_SECRET
    raise RuntimeError('AUTH_TOKEN_SECRET must be set in production')


def token_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(token_secret(), salt='objectives-auth')


def generate_token(user: str) -> str:
    return token_serializer().dumps({'user': user})


def authenticate(user, password) -> Union[None, str]:
    if os.getenv('APP_ENV') == 'test' or os.getenv('APP_ENV') == 'dev':
        return generate_token(user)
    with open("envs_user.json") as envs_file:
        envs = json.load(envs_file)
        if envs["user"] == user and envs["hash"] == sha256(password.encode('utf-8')).hexdigest():
            return generate_token(user)


def validate_token(token) -> bool:
    if not token:
        return False
    try:
        token_serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return True
    except (BadSignature, SignatureExpired):
        return False
