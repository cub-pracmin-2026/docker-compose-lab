// CF Finder web: renders pages on the server with the data from the CF Finder API.
import express from "express";
import { errorPage, problemPage, searchPage } from "./views.js";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const PORT = 3000;

class ApiError extends Error {}

async function api(path) {
  let response;
  try {
    response = await fetch(API_URL + path, { headers: { "X-Client": "cf-finder-web" } });
  } catch (e) {
    throw new ApiError(`Cannot reach the API at ${API_URL}: ${e.cause?.code ?? e.message}`);
  }
  if (!response.ok) throw new ApiError(`The API answered ${response.status} to ${API_URL}${path}`);
  return response.json();
}

const app = express();

app.get("/", async (req, res, next) => {
  try {
    const query = {};
    for (const key of ["q", "tag", "min_rating", "max_rating"]) {
      if (req.query[key]) query[key] = String(req.query[key]);
    }
    const [tags, problems] = await Promise.all([api("/tags"), api("/problems?" + new URLSearchParams(query))]);
    res.send(searchPage(query, tags, problems));
  } catch (e) {
    next(e);
  }
});

app.get("/problem/:id", async (req, res, next) => {
  try {
    const problem = await api(`/problems/${encodeURIComponent(req.params.id)}`);
    res.send(problemPage(problem));
  } catch (e) {
    next(e);
  }
});

app.use((err, req, res, next) => {
  console.error(err.message);
  res.status(err instanceof ApiError ? 502 : 500).send(errorPage(err.message));
});

app.listen(PORT, () => console.log(`CF Finder web on port ${PORT}, API at ${API_URL}`));
