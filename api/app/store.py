"""The problems in Postgres."""
from . import db, importer

PAGE_SIZE = 50
COLUMNS = "id, contest_id, problem_index, name, rating, tags, solved_count"


def with_url(problem: dict) -> dict:
    url = f"https://codeforces.com/problemset/problem/{problem['contest_id']}/{problem['problem_index']}"
    return problem | {"url": url}


def search(q: str | None, tag: str | None, min_rating: int | None, max_rating: int | None) -> list[dict]:
    conditions = ["TRUE"]
    if q:
        conditions.append("strpos(lower(name), lower(%(q)s)) > 0")
    if tag:
        conditions.append("%(tag)s = ANY(tags)")
    if min_rating is not None:
        conditions.append("rating >= %(min_rating)s")
    if max_rating is not None:
        conditions.append("rating <= %(max_rating)s")
    sql = (
        f"SELECT {COLUMNS} FROM problems WHERE {' AND '.join(conditions)}"
        f" ORDER BY contest_id DESC, problem_index DESC LIMIT {PAGE_SIZE}"
    )
    params = {"q": q, "tag": tag, "min_rating": min_rating, "max_rating": max_rating}
    with db.connect() as conn:
        return [with_url(p) for p in conn.execute(sql, params)]


def get(problem_id: str) -> dict | None:
    with db.connect() as conn:
        problem = conn.execute(f"SELECT {COLUMNS} FROM problems WHERE id = %s", [problem_id]).fetchone()
    return with_url(problem) if problem else None


def tags() -> list[dict]:
    with db.connect() as conn:
        return conn.execute(
            "SELECT tag, count(*) AS count FROM problems, unnest(tags) AS tag"
            " GROUP BY tag ORDER BY count DESC, tag"
        ).fetchall()


def stats() -> dict:
    with db.connect() as conn:
        count = conn.execute("SELECT count(*) AS n FROM problems").fetchone()["n"]
        return {"count": count, "imported_at": importer.imported_at(conn)}
