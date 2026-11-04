"""The snapshot of the Codeforces problem set in api/data/."""
import gzip
import json
from pathlib import Path

SNAPSHOT = Path(__file__).parent.parent / "data" / "problems.json.gz"


def read_problems() -> list[dict]:
    """Every problem of the snapshot, with the number of people who solved it."""
    result = json.loads(gzip.decompress(SNAPSHOT.read_bytes()))["result"]
    solved = {(s["contestId"], s["index"]): s["solvedCount"] for s in result["problemStatistics"]}
    return [
        {
            "id": f"{p['contestId']}{p['index']}",
            "contest_id": p["contestId"],
            "problem_index": p["index"],
            "name": p["name"],
            "rating": p.get("rating"),
            "tags": p["tags"],
            "solved_count": solved.get((p["contestId"], p["index"]), 0),
        }
        for p in result["problems"]
    ]
