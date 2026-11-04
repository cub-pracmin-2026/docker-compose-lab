"""The table of problems and the import of the Codeforces snapshot into it."""
import psycopg

from . import db, snapshot

SCHEMA = """
CREATE TABLE IF NOT EXISTS problems (
    id            text PRIMARY KEY,
    contest_id    integer NOT NULL,
    problem_index text NOT NULL,
    name          text NOT NULL,
    rating        integer,
    tags          text[] NOT NULL,
    solved_count  integer NOT NULL
);
CREATE TABLE IF NOT EXISTS imports (
    imported_at timestamptz NOT NULL DEFAULT now()
);
"""


def create_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def imported_at(conn: psycopg.Connection):
    row = conn.execute("SELECT max(imported_at) AS t FROM imports").fetchone()
    return row["t"]


def survived_restart() -> bool:
    """The problems are older than the running Postgres server: the data outlived a restart of db."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT max(imported_at) < pg_postmaster_start_time() - interval '5 seconds' AS ok FROM imports"
        ).fetchone()
    return bool(row["ok"])


def import_if_empty(conn: psycopg.Connection) -> None:
    """Import the snapshot only into an empty table: a restart keeps the data."""
    if t := imported_at(conn):
        print(f"Problems were imported at {t}, skipping the import", flush=True)
        return
    print(f"Importing problems from {snapshot.SNAPSHOT.name}...", flush=True)
    rows = snapshot.read_problems()
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO problems (id, contest_id, problem_index, name, rating, tags, solved_count)"
            " VALUES (%(id)s, %(contest_id)s, %(problem_index)s, %(name)s, %(rating)s, %(tags)s, %(solved_count)s)"
            " ON CONFLICT (id) DO NOTHING",
            rows,
        )
        cur.execute("INSERT INTO imports DEFAULT VALUES")
    conn.commit()
    print(f"Imported {len(rows)} problems", flush=True)
