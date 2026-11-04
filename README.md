# CF Finder

A search over the Codeforces problem set. You are going to set up Docker Compose for this app, one branch at a
time: `01-api`, `02-db`, `03-web`, `04-similar`. The `README.md` of each branch has the task of this branch.

## Task 02

Switch to the branch `02-db` and merge `01-api` into it.

In this branch, the API keeps the problems in Postgres: on the first start, it imports them into the database.

Your goal: add the database to `compose.yaml` and keep its data.

Do these steps in order:

1. Add the service `db` (Postgres 18) to `compose.yaml`: see [`db`](#db). Give `api` the env variables that it
   needs: see [`api`](#api). For now, you can put the password into `environment`: step 4 moves it out.

   **Check:** `docker compose up --build`. The log of `api` shows the import, then search works in API Docs.
   If `api` stops because `db` is not ready yet, run `up` again: step 3 fixes this.
2. Keep the data of `db` in a volume, so that the API does not import the problems again after
   a restart.

   **Check:** note `imported_at` in `GET /stats`. Run `docker compose down`, then `docker compose up`:
   `imported_at` is the same.
3. `api` must start only when `db` is ready: a healthcheck in `db` and `service_healthy`
   in `api`. See [Control startup order](https://docs.docker.com/compose/how-tos/startup-order/).

   **Check:** `docker compose ps` shows `db` as `healthy`. After `docker compose down -v` and `up --build`, `api`
   starts on the first try.
4. Keep the password out of git: write it into a file, for example `db_password.txt`, and add
   this file to `.gitignore`. Give the password from this file to `db` and `api` as one top-level secret, and
   remove it from `environment`. See [Manage secrets](https://docs.docker.com/compose/how-tos/use-secrets/).

   **Check:** `git status` does not show the password file. The app starts, and search works. Postgres keeps the
   password of its first start in the volume: if you changed the password, run `docker compose down -v` once.
5. Commit your changes and push the branch `02-db`.

   **Check:** on GitHub, the branch `02-db` has your commit.

**Done when:**

1. In a fresh clone with the password file, `docker compose up --build --wait` starts the app. Search works at
   http://localhost:8000/docs.
2. After `docker compose down` and `up`, `/stats` shows the same import time.
3. `api` waits for `db` to be healthy.
4. No password in git or in `environment`.

## How the app works

| Service | Folder | Stack | Port |
|---|---|---|---|
| `db` | — | Postgres 18 | 5432 |
| `api` | `api/` | Python 3.12, FastAPI, psycopg 3 | 8000 |

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
