"""Connection to Postgres. The settings come from env variables (see README.md)."""
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def password() -> str:
    if "DATABASE_PASSWORD_FILE" in os.environ:
        return Path(os.environ["DATABASE_PASSWORD_FILE"]).read_text().strip()
    if "DATABASE_PASSWORD" in os.environ:
        return os.environ["DATABASE_PASSWORD"]
    raise RuntimeError("Set DATABASE_PASSWORD or DATABASE_PASSWORD_FILE")


def password_from_secret() -> bool:
    """The password comes as a file of a Compose secret, not as an env variable."""
    return os.environ.get("DATABASE_PASSWORD_FILE", "").startswith("/run/secrets/") and "DATABASE_PASSWORD" not in os.environ


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        dbname=os.environ.get("DATABASE_NAME", "postgres"),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=password(),
        row_factory=dict_row,
    )
