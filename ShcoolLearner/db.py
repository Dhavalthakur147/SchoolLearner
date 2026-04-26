import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


# Basic MySQL connection helper for the SchoolLearn project.
# Defaults are safe for local development and can be overridden via .env/system env vars.

load_dotenv(override=True)


def _connection_config(include_database=True):
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
    if include_database:
        config["database"] = os.getenv("DB_NAME", "schoollearn")
    return config


def ensure_database():
    database = os.getenv("DB_NAME", "schoollearn")
    conn = mysql.connector.connect(**_connection_config(include_database=False))
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def initialize_database_from_sql(sql_path=None):
    sql_file = Path(sql_path or Path(__file__).with_name("database.sql"))
    if not sql_file.exists():
        raise FileNotFoundError(f"Database SQL file not found: {sql_file}")

    conn = mysql.connector.connect(**_connection_config(include_database=False))
    try:
        cursor = conn.cursor()
        sql_script = sql_file.read_text(encoding="utf-8")
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def get_connection():
    ensure_database()
    return mysql.connector.connect(**_connection_config())


if __name__ == "__main__":
    # Simple connection test
    initialize_database_from_sql()
    conn = get_connection()
    try:
        print("Connected to MySQL:", conn.is_connected())
    finally:
        conn.close()
