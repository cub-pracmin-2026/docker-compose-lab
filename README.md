# CF Finder

A search over the Codeforces problem set. You are going to set up Docker Compose for this app, one branch at a
time: `01-api`, `02-db`, `03-web`, `04-similar`. The `README.md` of each branch has the task of this branch.

## Task 01

Switch to the branch `01-api`.

In this branch, the app has one service: the API. The API keeps the problems in memory.

[How the app works](#how-the-app-works) says how to run the API by hand. Your goal: run the API in a container
with Compose, with live reload.

Do these steps in order:

1. Write `api/Dockerfile`.
2. Write `compose.yaml` with the service `api`, built from `api/Dockerfile`. Publish port 8000.

   **Check:** `docker compose up --build` starts the API. Open API Docs (Swagger) at
   http://localhost:8000/docs. `GET /problems` with `q=tree` returns problems.
3. Set up live reload: when you edit the code in `api/app/` on your computer, the change shows in the API after a
   refresh of the page, with no manual restart.
4. In API Docs, expand `GET /problems`: its description is `TODO: describe the search`. In `api/app/problems.py`,
   replace this `TODO` with a short description of the search.

   **Check:** refresh the API Docs page: it shows your text. If it does not, live reload does not work yet.
5. Commit your changes and push the branch `01-api`.

   **Check:** on GitHub, the branch `01-api` has your commit.

**Done when:**

1. In a fresh clone, `docker compose up --build --wait` starts the API. Search works at
   http://localhost:8000/docs.
2. An edit of the code in `api/app/` shows in API Docs after a refresh, with no manual restart.

**Troubleshooting:**

- On Windows, `docker compose` stops with `additional privileges requested: pass "--allow=fs.read=..."`? This is a
  Docker bug when the drive letter of the current folder is lowercase (`c:\`). Go to the same folder with a capital
  letter: `cd /d C:\path\to\repo` in cmd, `cd C:\path\to\repo` in PowerShell. Then run the command again.
- On Windows, live reload does not work? Clone the repo into your home folder in WSL (`~/`) and work there.

## How the app works

| Service | Folder | Stack | Port |
|---|---|---|---|
| `api` | `api/` | Python 3.12, FastAPI | 8000 |

### `api`

On start, the API reads the problems into memory from `api/data/problems.json.gz`: a snapshot of the
[Codeforces API](https://codeforces.com/apiHelp/methods#problemset.problems) of 2026-10-30, 11481 problems.

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
| `GET /health` | 200 when the API is ready |

Run from the folder `api/`:

```bash
pip install -r requirements.txt   # install the libraries that requirements.txt lists
fastapi run app/main.py           # start the API; it listens on 0.0.0.0:8000
```
