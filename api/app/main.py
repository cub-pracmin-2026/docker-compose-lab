"""CF Finder API: a search over the Codeforces problem set."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import problems, progress, store


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.load()
    progress.start(progress.checks_01(app))
    yield


app = FastAPI(title="CF Finder", lifespan=lifespan)
app.include_router(problems.router)


@app.get("/health")
def health():
    """200 when the API is ready to serve."""
    return {"status": "ok"}


@app.get("/stats")
def stats():
    """The number of problems and the time of the import."""
    return store.stats()


@app.get("/tags")
def tags():
    """All tags with the number of problems for each tag, the most used tags first."""
    return store.tags()
