import sqlite3

from werkzeug.exceptions import BadRequest


class ApiError(Exception):
    status_code = 500
    code = 'internal_error'
    default_message = 'An unexpected server error occurred.'

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


class ValidationError(ApiError):
    status_code = 400
    code = 'validation_error'
    default_message = 'The request contains invalid or missing data.'


class NotFoundError(ApiError):
    status_code = 404
    code = 'not_found'


class ConflictError(ApiError):
    status_code = 409
    code = 'conflict'


class UnprocessableEntityError(ApiError):
    status_code = 422
    code = 'unprocessable_entity'
    default_message = 'The request data cannot be processed.'


class InternalServerError(ApiError):
    pass


def translate_exception(error):
    """Turn expected boundary/database input failures into safe API errors."""
    if isinstance(error, ApiError):
        return error
    if isinstance(error, ValueError):
        return ValidationError(str(error))
    if isinstance(error, (BadRequest, KeyError, TypeError)):
        return ValidationError()
    if isinstance(error, sqlite3.IntegrityError):
        return UnprocessableEntityError()
    return InternalServerError()


def error_body(error):
    return {
        'error': {
            'code': error.code,
            'message': str(error),
        }
    }
