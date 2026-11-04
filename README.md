# CF Finder

A search over the Codeforces problem set. You are going to set up Docker Compose for this app, one branch at a
time: `01-api`, `02-db`, `03-web`, `04-similar`. The `README.md` of each branch has the task of this branch.

## Task 03

Switch to the branch `03-web` and merge `02-db` into it.

This branch adds the third service: the web app in `web/`.

Your goal: run all three services with one command, and keep the data of the running app of `02-db`.

Do these steps in order:

1. Write `web/Dockerfile`.
2. Add the service `web` to `compose.yaml`. Publish port 3000. Give it the env variables that [`web`](#web) lists.
   Then update the running app of `02-db` with `docker compose up -d --build`.

   **Check:** http://localhost:3000/?q=tree shows search results. If it shows an error, read
   `docker compose logs web`. `GET /stats` shows the same `imported_at` as in `02-db`.
3. Commit your changes and push the branch `03-web`.

   **Check:** on GitHub, the branch `03-web` has your commit.

**Done when:**

1. http://localhost:3000 shows search results.
2. `/stats` shows the same import time as in `02-db`.

## How the app works

| Service | Folder | Stack | Port |
|---|---|---|---|
| `db` | — | Postgres 18 | 5432 |
| `api` | `api/` | Python 3.12, FastAPI, psycopg 3 | 8000 |
| `web` | `web/` | Node 22, Express | 3000 |

### `db`

The official image `postgres:18`. The API uses the default user and database `postgres`.

The [docs of the image](https://hub.docker.com/_/postgres) say how to set it up:

- The password: [`POSTGRES_PASSWORD`](https://github.com/docker-library/docs/blob/master/postgres/README.md#postgres_password),
  or a file with the password: [Docker Secrets](https://github.com/docker-library/docs/blob/master/postgres/README.md#docker-secrets).
- Where to mount the volume: the section [`PGDATA`](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)
  says where the image keeps the data.
- How to check that Postgres is ready: the image has the program
  [`pg_isready`](https://www.postgresql.org/docs/current/app-pg-isready.html).

### `api`

On start, the API creates its tables. If there are no problems yet, it imports them from
`api/data/problems.json.gz`: a snapshot of the [Codeforces API](https://codeforces.com/apiHelp/methods#problemset.problems)
of 2026-10-30, 11481 problems.

When the API runs in Compose, it reports your progress to the
[class board](https://pracmin2026.web.app/compose-board) until the end of 2026. `BOARD: off` in
its environment turns the reports off.

Endpoints (API Docs: http://localhost:8000/docs):

| Endpoint | What it returns |
|---|---|
| `GET /problems?q=&tag=&min_rating=&max_rating=` | Search results, at most 50 |
| `GET /problems/{id}` | One problem, for example `/problems/2277E` |
| `GET /tags` | All tags with the number of problems |
| `GET /stats` | The number of problems and the time of the import |
| `GET /health` | 200 when the API is ready, 503 while the import runs |

Env variables:

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_HOST` | `localhost` | Host name of Postgres |
| `DATABASE_NAME` | `postgres` | Database name |
| `DATABASE_USER` | `postgres` | User name |
| `DATABASE_PASSWORD` | — | Password |
| `DATABASE_PASSWORD_FILE` | — | A file with the password; used instead of `DATABASE_PASSWORD` |

Run from the folder `api/`:

```bash
pip install -r requirements.txt   # install the libraries that requirements.txt lists
fastapi run app/main.py           # start the API; it listens on 0.0.0.0:8000
```

### `web`

Pages rendered on the server: a search form with results, and a page for each problem with a link to
Codeforces. The web app gets all data from the API. Open http://localhost:3000.

Env variables:

| Variable | Default | Meaning |
|---|---|---|
| `API_URL` | `http://localhost:8000` | The address of the API, as seen from the web app |

The web app is written in JavaScript. It runs on [Node.js](https://nodejs.org/): a program that runs JavaScript
outside the browser, as `python` runs Python code. Node.js comes with `npm`, its package manager, as Python comes
with `pip`. `package.json` lists the libraries of the app, and `package-lock.json` fixes their exact versions.

Run from the folder `web/`:

```bash
npm ci           # install the exact versions from package-lock.json into node_modules/
node server.js   # start the web app; it listens on port 3000
```
