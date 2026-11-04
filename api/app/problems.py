"""Search and view problems."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from . import store

router = APIRouter()


@router.get("/problems")
def search_problems(
    q: str | None = None,
    tag: str | None = None,
    min_rating: int | None = None,
    max_rating: int | None = None,
):
    """TODO: describe the search"""
    return store.search(q, tag, min_rating, max_rating)


@router.get("/problems/{problem_id}")
def get_problem(
    problem_id: Annotated[str, Path(description="Contest id and problem index, for example `2277E`.")],
):
    """One problem with a link to its statement on Codeforces."""
    problem = store.get(problem_id)
    if problem is None:
        raise HTTPException(404, f"No problem {problem_id}")
    return problem
