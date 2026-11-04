"""The problems in memory: the API reads them from the snapshot on each start."""
from collections import Counter
from datetime import datetime, timezone

from . import snapshot

PAGE_SIZE = 50

problems: dict[str, dict] = {}
loaded_at: datetime | None = None


def with_url(problem: dict) -> dict:
    url = f"https://codeforces.com/problemset/problem/{problem['contest_id']}/{problem['problem_index']}"
    return problem | {"url": url}


def load() -> None:
    global loaded_at
    problems.clear()
    problems.update((p["id"], p) for p in snapshot.read_problems())
    loaded_at = datetime.now(timezone.utc)
    print(f"Loaded {len(problems)} problems into memory", flush=True)


def matches(p: dict, q: str | None, tag: str | None, min_rating: int | None, max_rating: int | None) -> bool:
    # A problem with no rating does not match a rating filter.
    return (
        (not q or q.lower() in p["name"].lower())
        and (not tag or tag in p["tags"])
        and (min_rating is None or (p["rating"] is not None and p["rating"] >= min_rating))
        and (max_rating is None or (p["rating"] is not None and p["rating"] <= max_rating))
    )


def search(q: str | None, tag: str | None, min_rating: int | None, max_rating: int | None) -> list[dict]:
    found = [p for p in problems.values() if matches(p, q, tag, min_rating, max_rating)]
    found.sort(key=lambda p: (p["contest_id"], p["problem_index"]), reverse=True)
    return [with_url(p) for p in found[:PAGE_SIZE]]


def get(problem_id: str) -> dict | None:
    problem = problems.get(problem_id)
    return with_url(problem) if problem else None


def tags() -> list[dict]:
    counts = Counter(t for p in problems.values() for t in p["tags"])
    return [{"tag": t, "count": n} for t, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def stats() -> dict:
    return {"count": len(problems), "imported_at": loaded_at}
