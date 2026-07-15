import argparse

import database_manager
from database_manager import DatabaseManager, DataSource


def main():
    parser = argparse.ArgumentParser(description='Migrate legacy date values to ISO 8601.')
    parser.add_argument('environment', choices=[source.value for source in DataSource])
    args = parser.parse_args()

    database_manager.datasource = DataSource(args.environment)
    updated = DatabaseManager().migrate_legacy_dates()
    print(f'Migrated {updated} date value(s).')


if __name__ == '__main__':
    main()
