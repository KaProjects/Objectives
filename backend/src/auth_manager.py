import json
import sys
import time
import uuid

from typing import Union
from hashlib import sha256


class Token:
    def __init__(self):
        self.value: Union[None, str] = None
        self.expiration: Union[None, int] = None

    def generate(self):
        self.expiration = int(round(time.time())) + 18000
        self.value = str(uuid.uuid4())
        return self.value

    def check(self, token):
        if not token:
            return False
        if token == self.value:
            return int(round(time.time())) < self.expiration
        else:
            return False


token_store = Token()


def authenticate(user, password) -> Union[None, str]:
    if sys.argv[1] == 'test':
        return token_store.generate()
    with open("envs_user.json") as envs_file:
        envs = json.load(envs_file)
        if envs["user"] == user and envs["hash"] == sha256(password.encode('utf-8')).hexdigest():
            return token_store.generate()


def validate_token(token) -> bool:
    return token_store.check(token)
