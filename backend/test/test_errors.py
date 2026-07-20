import unittest

from errors import InternalServerError, ValidationError, translate_exception
from werkzeug.exceptions import BadRequest


class TestErrorTranslation(unittest.TestCase):
    def test_boundary_validation_errors_are_bad_requests(self):
        self.assertIsInstance(translate_exception(BadRequest()), ValidationError)
        self.assertIsInstance(translate_exception(ValueError('invalid input')), ValidationError)

    def test_unexpected_type_and_key_errors_are_internal_server_errors(self):
        self.assertIsInstance(translate_exception(TypeError('unexpected type')), InternalServerError)
        self.assertIsInstance(translate_exception(KeyError('unexpected key')), InternalServerError)
