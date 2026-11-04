"""Similar problems: the nearest problems by tags and rating. Needs the Postgres extension pgvector."""
from typing import Annotated

import psycopg
from fastapi import APIRouter, HTTPException, Path, Query

from . import db
from .store import COLUMNS, with_url

router = APIRouter()

# The rating is one more coordinate next to the tags (0 or 1 each): 1 per 1000 points of rating.
RATING_SCALE = 1000
RATING_IF_NONE = 1500


def enable_pgvector(conn: psycopg.Connection) -> None:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()


def vectors_ready() -> bool:
    with db.connect() as conn:
        return conn.execute("SELECT 1 FROM pg_indexes WHERE indexname = 'problems_vector'").fetchone() is not None


def data_kept() -> bool:
    """The problems were imported before the vectors were added: the data came from the previous branch."""
    with db.connect() as conn:
        # The board asks before add_vectors creates the table; a query on a missing table is an ERROR in the db log.
        if conn.execute("SELECT to_regclass('vectors') IS NULL AS missing").fetchone()["missing"]:
            return False
        row = conn.execute(
            "SELECT (SELECT max(imported_at) FROM imports) < (SELECT max(added_at) FROM vectors) - interval '10 seconds'"
            " AS ok"
        ).fetchone()
    return bool(row["ok"])


def add_vectors(conn: psycopg.Connection) -> None:
    """Give every problem a vector: one coordinate per tag, plus the rating. Runs once, after the import."""
    if conn.execute("SELECT 1 FROM pg_indexes WHERE indexname = 'problems_vector'").fetchone():
        return
    print("Adding vectors for similar problems...", flush=True)
    problems = conn.execute("SELECT id, tags, rating FROM problems").fetchall()
    all_tags = sorted({t for p in problems for t in p["tags"]})
    conn.execute(f"ALTER TABLE problems ADD COLUMN IF NOT EXISTS vector vector({len(all_tags) + 1})")
    rows = []
    for p in problems:
        coordinates = [int(t in p["tags"]) for t in all_tags]
        coordinates.append((p["rating"] or RATING_IF_NONE) / RATING_SCALE)
        rows.append((str(coordinates), p["id"]))
    with conn.cursor() as cur:
        cur.executemany("UPDATE problems SET vector = %s WHERE id = %s", rows)
        cur.execute("CREATE INDEX problems_vector ON problems USING hnsw (vector vector_cosine_ops)")
        cur.execute("CREATE TABLE IF NOT EXISTS vectors (added_at timestamptz NOT NULL DEFAULT now())")
        cur.execute("INSERT INTO vectors DEFAULT VALUES")
    conn.commit()
    print(f"Added vectors for {len(rows)} problems", flush=True)


@router.get("/problems/{problem_id}/similar")
def similar_problems(
    problem_id: Annotated[str, Path(description="Contest id and problem index, for example `2277E`.")],
    limit: Annotated[int, Query(ge=1, le=50, description="How many problems to return.")] = 10,
):
    """The problems with the nearest tags and rating (cosine distance), the nearest first."""
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM problems WHERE id = %s", [problem_id]).fetchone() is None:
            raise HTTPException(404, f"No problem {problem_id}")
        similar = conn.execute(
            f"SELECT {COLUMNS} FROM problems WHERE id <> %(id)s"
            " ORDER BY vector <=> (SELECT vector FROM problems WHERE id = %(id)s) LIMIT %(limit)s",
            {"id": problem_id, "limit": limit},
        )
        return [with_url(p) for p in similar]
