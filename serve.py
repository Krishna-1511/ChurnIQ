"""Run the ChurnIQ API locally. Set MYSQL_PASSWORD or DATABASE_URL (see db_config.py)."""
import os

from db_config import get_database_url

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = get_database_url()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
