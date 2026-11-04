# CF Finder

A search over the Codeforces problem set. You are going to set up Docker Compose for this app, one branch at a
time: `01-api`, `02-db`, `03-web`, `04-similar`. The `README.md` of each branch has the task of this branch.

## Task 04

Switch to the branch `04-similar` and merge `03-web` into it.

In this branch, the API finds similar problems for each problem: the problems with the nearest tags and rating.
For this search, the API needs the Postgres extension pgvector.

Your goal: bring the running app of `03-web` to this branch and keep its data.

Do these steps in order:

1. Start this branch as it is: `docker compose up -d --build`.

   **Check:** `api` stops. `docker compose logs api` shows why.
2. Write `db/Dockerfile`: `postgres:18` with the package `postgresql-18-pgvector`.
   In `compose.yaml`, build `db` from it. The section [`db`](#db) below has the command that installs the package.

   **Check:** `docker compose build db` ends with no errors. `docker compose run --rm db dpkg -s postgresql-18-pgvector`
   shows `Status: install ok installed`.
3. Apply your changes to the running app: recreate its containers, so that `db` runs from your new image.
   Do not delete the volume: it has the data of `03-web`.

   **Check:** in API Docs, `GET /problems/2277E/similar` returns problems. `GET /stats` shows the same
   `imported_at` as in `03-web`.
4. Commit your changes and push the branch `04-similar`.

   **Check:** on GitHub, the branch `04-similar` has your commit.

**Done when:**

1. The problem page at http://localhost:3000 shows "Similar problems".
2. `/stats` shows the same import time as in `03-web`.

## Optional: go deeper, no points

- **Fast rebuilds, small images.** Make the images smaller, and make a code change not reinstall the dependencies.
  Try `.dockerignore`, a slim base image, a multi-stage build. Compare the sizes in `docker images`.

  **Check:** change a line in `api/app/`, then `docker compose build api`: the step with `pip install` is `CACHED`.
- **Watch the API calls live.** Put `mitmweb` (image `mitmproxy/mitmproxy`) in front of `api` as a reverse proxy,
  in the [profile](https://docs.docker.com/compose/how-tos/profiles/) `debug`. Find the slowest search.

  **Check:** `docker compose up -d` starts no `mitmweb`. With `--profile debug`, the page of `mitmweb` lists each
  call of the web app to the API.
- **Upgrade Postgres and keep the data.** Start `02-db` on `postgres:17`, then move it to `postgres:18` with no new
  import: `pg_dump` and `pg_restore`, or `pg_upgrade`.

  **Check:** on `postgres:18`, `GET /stats` shows the `imported_at` of the start on `postgres:17`.

## How the app works

| Service | Folder | Stack | Port |
|---|---|---|---|
| `db` | — | Postgres 18 with pgvector | 5432 |
| `api` | `api/` | Python 3.12, FastAPI, psycopg 3 | 8000 |
| `web` | `web/` | Node 22, Express | 3000 |

### `db`

The official image `postgres:18` with the extension [pgvector](https://github.com/pgvector/pgvector).
The API uses the default user and database `postgres`.

To install pgvector:

```bash
apt-get update && apt-get install -y postgresql-18-pgvector
```

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
of 2026-10-30, 11481 problems. Then it gives each problem a vector of its tags and rating, once.

When the API runs in Compose, it reports your progress to the
[class board](https://pracmin2026.web.app/compose-board) until the end of 2026. `BOARD: off` in
its environment turns the reports off.

Endpoints (API Docs: http://localhost:8000/docs):

| Endpoint | What it returns |
|---|---|
| `GET /problems?q=&tag=&min_rating=&max_rating=` | Search results, at most 50 |
| `GET /problems/{id}` | One problem, for example `/problems/2277E` |
| `GET /problems/{id}/similar` | The problems with the nearest tags and rating |
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
Codeforces and a list of similar problems. The web app gets all data from the API. Open http://localhost:3000.

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
