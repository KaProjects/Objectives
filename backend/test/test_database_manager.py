import sqlite3
import tempfile
import unittest
from pathlib import Path

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


class TestDatabaseManagerDateUpdates(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / 'dates.db'
        self.database = DatabaseManager(connect=lambda: sqlite3.connect(database_path))

        with self.database.open() as database:
            with database.cursor(commit=True) as cursor:
                cursor.execute('''
                    create table KeyResults (
                        id integer primary key,
                        state text not null,
                        name text not null,
                        date_created text not null,
                        date_reviewed text not null
                    )
                ''')
                cursor.execute('''
                    create table Objectives (
                        id integer primary key,
                        state text not null,
                        name text not null,
                        date_created text not null,
                        date_finished text not null
                    )
                ''')
                cursor.execute(
                    "insert into KeyResults values (1, 'completed', 'preserved KR', '2023-01-01', '2023-01-02')",
                )
                cursor.execute(
                    "insert into Objectives values (1, 'achieved', 'preserved objective', '2023-02-01', '2023-02-02')",
                )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_updates_both_dates_on_inactive_key_result_and_preserves_other_columns(self):
        with self.database.open() as database:
            updated = database.update_key_result_dates(1, '2022-11-10', '2022-12-12')
            with database.cursor() as cursor:
                cursor.execute('select state,name,date_created,date_reviewed from KeyResults where id=1')
                row = cursor.fetchone()

        self.assertEqual(updated, ('2022-11-10', '2022-12-12'))
        self.assertEqual(row, ('completed', 'preserved KR', '2022-11-10', '2022-12-12'))

    def test_invalid_key_result_date_does_not_partially_update_dates(self):
        with self.database.open() as database:
            with self.assertRaises(ValueError):
                database.update_key_result_dates(1, '2022-11-10', 'invalid')
            with database.cursor() as cursor:
                cursor.execute('select date_created,date_reviewed from KeyResults where id=1')
                row = cursor.fetchone()

        self.assertEqual(row, ('2023-01-01', '2023-01-02'))

    def test_updates_both_dates_on_inactive_objective_and_preserves_other_columns(self):
        with self.database.open() as database:
            updated = database.update_objective_dates(1, '2021-05-06', '')
            with database.cursor() as cursor:
                cursor.execute('select state,name,date_created,date_finished from Objectives where id=1')
                row = cursor.fetchone()

        self.assertEqual(updated, ('2021-05-06', ''))
        self.assertEqual(row, ('achieved', 'preserved objective', '2021-05-06', ''))

    def test_invalid_objective_date_does_not_partially_update_dates(self):
        with self.database.open() as database:
            with self.assertRaises(ValueError):
                database.update_objective_dates(1, '2021-05-06', 'invalid')
            with database.cursor() as cursor:
                cursor.execute('select date_created,date_finished from Objectives where id=1')
                row = cursor.fetchone()

        self.assertEqual(row, ('2023-02-01', '2023-02-02'))
