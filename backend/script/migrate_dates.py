"""One-off migration of production MySQL legacy dates to ISO 8601."""
import json
from datetime import date, datetime
from pathlib import Path

import mysql.connector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATE_COLUMNS = (
    ('Objectives', 'date_created', False),
    ('Objectives', 'date_finished', True),
    ('KeyResults', 'date_created', False),
    ('KeyResults', 'date_reviewed', False),
)


def normalize_date(value: str, allow_empty: bool) -> str:
    if value == '' and allow_empty:
        return value
    if not isinstance(value, str):
        raise ValueError('date must be a string')

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        try:
            return datetime.strptime(value, '%d/%m/%Y').date().isoformat()
        except ValueError as error:
            raise ValueError(f'Invalid date {value!r}; expected YYYY-MM-DD or DD/MM/YYYY.') from error


def connect():
    with (PROJECT_ROOT / 'envs_prod_db.json').open(encoding='utf-8') as envs_file:
        envs = json.load(envs_file)
    return mysql.connector.connect(
        host=envs['host'],
        port=envs['port'],
        user=envs['user'],
        password=envs['password'],
        database=envs['database'],
        buffered=True,
    )


def migrate_dates(connection) -> int:
    cursor = connection.cursor()
    updated = 0
    try:
        for table, column, allow_empty in DATE_COLUMNS:
            cursor.execute(f'select id, {column} from {table}')
            for record_id, value in cursor.fetchall():
                normalized = normalize_date(value, allow_empty)
                if normalized != value:
                    cursor.execute(f'update {table} set {column}=%s where id=%s', (normalized, record_id))
                    updated += 1
        connection.commit()
        return updated
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def main():
    connection = connect()
    try:
        updated = migrate_dates(connection)
    finally:
        connection.close()
    print(f'Migrated {updated} date value(s).')


if __name__ == '__main__':
    main()
