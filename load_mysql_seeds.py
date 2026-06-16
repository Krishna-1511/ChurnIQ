"""
Load extra bank data into MySQL (customers 31–110, accounts, loans, etc.).

Requires: base schema + customers 1–30 already loaded.

Connection (pick one):
  • Set DATABASE_URL (same as for the API), or
  • Set MYSQL_PASSWORD (and optional MYSQL_USER, MYSQL_HOST, MYSQL_DATABASE), or
  • Run without those: you will be prompted for the MySQL password.

Examples (PowerShell):
  $env:MYSQL_PASSWORD = "YourRealPassword"
  python load_mysql_seeds.py

  $env:DATABASE_URL = "mysql+pymysql://root:YourRealPassword@localhost:3306/bankdb"
  python load_mysql_seeds.py
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

from db_config import get_database_url

ROOT = Path(__file__).resolve().parent

SEED_FILES = [
    ROOT / "seed_extension.sql",
    ROOT / "seed_extension_batch2.sql",
]


def parse_mysql_url(url: str) -> dict:
    from sqlalchemy.engine.url import make_url

    u = make_url(url)
    return {
        "host": u.host or "localhost",
        "port": u.port or 3306,
        "user": u.username or "root",
        "password": u.password or "",
        "database": u.database or "bankdb",
    }


def run_file(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        while cur.nextset():
            pass


def resolve_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    # MYSQL_PASSWORD explicitly set (even empty) → do not prompt
    if "MYSQL_PASSWORD" in os.environ:
        return get_database_url()
    print(
        "MySQL password not set. Enter the password you use in MySQL Workbench for user 'root'.\n"
        "(Press Enter if root has no password.)\n"
        "Tip: next time set  $env:MYSQL_PASSWORD = '...'  in PowerShell first.\n"
    )
    pw = getpass.getpass("Password: ")
    os.environ["MYSQL_PASSWORD"] = pw
    return get_database_url()


def main() -> int:
    missing = [p for p in SEED_FILES if not p.is_file()]
    if missing:
        print("Missing files:", missing, file=sys.stderr)
        return 1

    raw = resolve_url()
    cfg = parse_mysql_url(raw)

    print(f"Connecting {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']} …")
    try:
        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
            client_flag=CLIENT.MULTI_STATEMENTS,
            autocommit=True,
        )
    except RuntimeError as e:
        if "cryptography" in str(e).lower():
            print(
                "MySQL 8 needs the cryptography package for this Python.\n"
                "  python -m pip install cryptography\n",
                file=sys.stderr,
            )
        raise
    except pymysql.err.OperationalError as e:
        if e.args and e.args[0] == 1045:
            print(
                "\nAccess denied — wrong password or user.\n"
                "  • Use the same password as MySQL Workbench for root.\n"
                "  • Or set:  $env:DATABASE_URL = 'mysql+pymysql://root:YOURPASS@localhost:3306/bankdb'\n",
                file=sys.stderr,
            )
        raise
    try:
        for path in SEED_FILES:
            print(f"Applying {path.name} …")
            try:
                run_file(conn, path)
            except pymysql.err.MySQLError as e:
                print(f"Error in {path.name}: {e}", file=sys.stderr)
                return 1
            print(f"  OK: {path.name}")
        print("\nDone. Use the same password when starting the API, e.g.:")
        print('  $env:MYSQL_PASSWORD = "<same password>"')
        print("  python serve.py")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
