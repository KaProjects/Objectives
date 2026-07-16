import os
import unittest
from unittest.mock import patch

from auth_manager import generate_token, validate_token


class TestAuthManager(unittest.TestCase):
    @patch.dict(os.environ, {'APP_ENV': 'prod', 'AUTH_TOKEN_SECRET': 'test-token-secret'}, clear=False)
    def test_signed_token_is_valid_without_in_memory_state(self):
        token = generate_token('user')

        self.assertTrue(validate_token(token))
        self.assertFalse(validate_token('not-a-valid-token'))
