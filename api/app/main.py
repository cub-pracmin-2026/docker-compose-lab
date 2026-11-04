"""CF Finder API: a search over the Codeforces problem set."""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from . import db, importer, problems, progress, store

data_ready = threading.Event()
web_seen = threading.Event()  # a request from the web part: it sends the header X-Client


def prepare_data():
    with db.connect() as conn:
        importer.import_if_empty(conn)
    data_ready.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect before the server starts: without the database the API exits with an error.
    with db.connect() as conn:
        importer.create_schema(conn)
    threading.Thread(target=prepare_data, daemon=True).start()
    progress.start(checks(app))
    yield


def checks(app: FastAPI) -> dict[str, progress.Check]:
    return progress.checks_01(app) | {
        "02-postgres": data_ready.is_set,
        "02-secret": db.password_from_secret,
        "02-restart": importer.survived_restart,
        "03-web": web_seen.is_set,
    }


app = FastAPI(title="CF Finder", lifespan=lifespan)
app.include_router(problems.router)


@app.middleware("http")
async def notice_web(request: Request, call_next):
    if request.headers.get("x-client") == "cf-finder-web":
        web_seen.set()
    return await call_next(request)


@app.get("/health")
def health(response: Response):
    """200 when the API is ready to serve, 503 while the import runs."""
    if not data_ready.is_set():
        response.status_code = 503
        return {"status": "importing"}
    return {"status": "ok"}


@app.get("/stats")
def stats():
    """The number of problems and the time of the import."""
    return store.stats()


@app.get("/tags")
def tags():
    """All tags with the number of problems for each tag, the most used tags first."""
    return store.tags()
