import sqlite3
import unittest

from database_manager import DatabaseManager, validate_iso_date
from errors import DatabaseIntegrityError, UnprocessableEntityError, translate_exception


class TestDatabaseManagerDateValidation(unittest.TestCase):
    def test_requires_an_iso_date(self):
        self.assertEqual(validate_iso_date('2026-07-18'), '2026-07-18')
        with self.assertRaises(ValueError):
            validate_iso_date('18/07/2026')

    def test_allows_an_empty_optional_date(self):
        self.assertEqual(validate_iso_date('', allow_empty=True), '')

    def test_normalizes_configured_integrity_errors(self):
        database = DatabaseManager(
            connect=lambda: sqlite3.connect(':memory:'),
            integrity_errors=(sqlite3.IntegrityError,),
        )

        with database.open() as session:
            with session.cursor(commit=True) as cursor:
                cursor.execute('create table items (name text unique)')
                cursor.execute("insert into items (name) values ('one')")

            with self.assertRaises(DatabaseIntegrityError) as raised:
                with session.cursor(commit=True) as cursor:
                    cursor.execute("insert into items (name) values ('one')")

        self.assertIsInstance(translate_exception(raised.exception), UnprocessableEntityError)
