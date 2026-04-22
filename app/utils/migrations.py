import logging
from sqlalchemy import text
from app import db

def migrate_database(app):
    """
    Manually add missing columns to the database.
    This is a temporary measure because db.create_all() does not handle schema changes.
    """
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                columns_to_add = [
                    ('total_fuel_cost', 'FLOAT DEFAULT 0.0'),
                    ('distance_km', 'FLOAT DEFAULT 0.0'),
                    ('passenger_preference', 'VARCHAR(20) DEFAULT \'any\''),
                    ('other_charges', 'FLOAT DEFAULT 0.0'),
                    ('max_wait_time', 'INTEGER DEFAULT 5'),
                ]

                for col_name, col_type in columns_to_add:
                    # Check if column exists
                    result = conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        f"WHERE table_name='rides' AND column_name='{col_name}';"
                    ))
                    if not result.fetchone():
                        app.logger.info(f"Adding '{col_name}' column to 'rides' table...")
                        conn.execute(text(f"ALTER TABLE rides ADD COLUMN {col_name} {col_type};"))
                        conn.commit()
                        app.logger.info(f"Column '{col_name}' added successfully.")

        except Exception as e:
            app.logger.error(f"Migration error: {e}")
