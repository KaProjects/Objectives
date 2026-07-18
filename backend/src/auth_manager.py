from hashlib import sha256

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_MAX_AGE_SECONDS = 18_000


class AuthManager:
    def __init__(self, token_secret, user=None, password_hash=None):
        self._serializer = URLSafeTimedSerializer(token_secret, salt='objectives-auth')
        self._user = user
        self._password_hash = password_hash

    def generate_token(self, user):
        return self._serializer.dumps({'user': user})

    def authenticate(self, user, password):
        if self._user is None:
            return self.generate_token(user)
        if self._user == user and self._password_hash == sha256(password.encode('utf-8')).hexdigest():
            return self.generate_token(user)
        return None

    def validate_token(self, token):
        if not token:
            return False
        try:
            self._serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
            return True
        except (BadSignature, SignatureExpired):
            return False
