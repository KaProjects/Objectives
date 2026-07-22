import unittest

from auth_manager import AuthManager


class TestAuthManager(unittest.TestCase):
    def test_signed_token_is_valid_without_in_memory_state(self):
        auth = AuthManager('test-token-secret')
        token = auth.generate_token('user')

        self.assertTrue(auth.validate_token(token))
        self.assertFalse(auth.validate_token('not-a-valid-token'))
