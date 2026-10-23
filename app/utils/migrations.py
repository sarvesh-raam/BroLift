"""
Lightweight schema sync for databases created from older versions of the models.

db.create_all() only creates missing tables; it never adds columns to existing ones.
This compares every model table with the live database and adds any missing columns.
Works on both PostgreSQL and SQLite. Each ALTER runs in its own transaction so one
failure cannot leave the rest of the migration stuck in an aborted transaction.
"""
from flask import current_app
from sqlalchemy import inspect, text

from app import db


def _default_sql(column):
    default = column.default
    if default is None or not default.is_scalar:
        return ''
    value = default.arg
    if isinstance(value, bool):
        return ' DEFAULT ' + ('TRUE' if value else 'FALSE')
    if isinstance(value, (int, float)):
        return f' DEFAULT {value}'
    if isinstance(value, str):
        return " DEFAULT '" + value.replace("'", "''") + "'"
    return ''


def migrate_database():
    engine = db.engine
    preparer = engine.dialect.identifier_preparer
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table in db.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_cols = {c['name'] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            ddl = (f'ALTER TABLE {preparer.quote(table.name)} '
                   f'ADD COLUMN {preparer.quote(column.name)} {col_type}{_default_sql(column)}')
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
                current_app.logger.info(f'Migration: added {table.name}.{column.name}')
            except Exception as e:
                current_app.logger.error(f'Migration failed for {table.name}.{column.name}: {e}')

    # Data backfill: databases from the first release stored car info in has_car/car_model/car_number
    if 'users' in existing_tables:
        user_cols = {c['name'] for c in inspect(engine).get_columns('users')}
        if {'has_car', 'car_model', 'car_number'} <= user_cols:
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        'UPDATE users SET has_vehicle = has_car, '
                        'vehicle_model = COALESCE(vehicle_model, car_model), '
                        'vehicle_number = COALESCE(vehicle_number, car_number) '
                        'WHERE has_car IS NOT NULL AND (has_vehicle IS NULL OR has_vehicle = FALSE) '
                        'AND has_car = TRUE'
                    ))
            except Exception as e:
                current_app.logger.error(f'Migration backfill of legacy car fields failed: {e}')
