"""Single place for MySQL connection string (used by db.py, serve.py, load_mysql_seeds.py)."""
from __future__ import annotations

import os
from urllib.parse import quote_plus


def get_database_url() -> str:
    """
    1) DATABASE_URL — full SQLAlchemy URL (highest priority)
    2) MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE — built into a URL

    Special characters in the password are escaped automatically.
    """
    direct = os.getenv("DATABASE_URL")
    if direct:
        return direct
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "Mysql@1234")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "bankdb")
    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )
