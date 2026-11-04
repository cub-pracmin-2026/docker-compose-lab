// HTML pages. `html` escapes every inserted value, except the HTML made by `html` itself.

class Html {
  constructor(text) {
    this.text = text;
  }
}

function render(value) {
  if (value instanceof Html) return value.text;
  if (Array.isArray(value)) return value.map(render).join("");
  if (value === null || value === undefined || value === false) return "";
  return String(value).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

export function html(strings, ...values) {
  return new Html(strings.reduce((out, s, i) => out + render(values[i - 1]) + s));
}

function layout(title, body) {
  return render(html`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  <style>
    body { font: 16px/1.5 system-ui, sans-serif; max-width: 860px; margin: 0 auto; padding: 16px; }
    a { color: #1a5fb4; }
    form { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    input, select, button { font: inherit; padding: 4px 8px; }
    input[type=number] { width: 7em; }
    table { border-collapse: collapse; width: 100%; }
    td, th { text-align: left; padding: 4px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
    .tag { display: inline-block; background: #eef; border-radius: 4px; padding: 0 6px; margin: 2px; font-size: 14px; }
    .muted { color: #666; }
  </style>
</head>
<body>
  <p><a href="/"><b>CF Finder</b></a> <span class="muted">· a search over the Codeforces problem set</span></p>
  ${body}
</body>
</html>`);
}

function tagLinks(tags) {
  return tags.map((t) => html`<a class="tag" href="/?tag=${encodeURIComponent(t)}">${t}</a> `);
}

export function searchPage(query, tags, problems) {
  const options = tags.map(
    (t) => html`<option value="${t.tag}" ${t.tag === query.tag ? html`selected` : ""}>${t.tag} (${t.count})</option>`,
  );
  const rows = problems.map(
    (p) => html`<tr>
      <td><a href="/problem/${p.id}">${p.id}</a></td>
      <td>${p.name}</td>
      <td>${p.rating ?? html`<span class="muted">none</span>`}</td>
      <td>${tagLinks(p.tags)}</td>
    </tr>`,
  );
  return layout("CF Finder", html`
  <form method="get" action="/">
    <input name="q" placeholder="Name" value="${query.q}" autofocus>
    <select name="tag"><option value="">Any tag</option>${options}</select>
    <input name="min_rating" type="number" placeholder="Min rating" value="${query.min_rating}">
    <input name="max_rating" type="number" placeholder="Max rating" value="${query.max_rating}">
    <button>Search</button>
  </form>
  <p class="muted">${problems.length === 50 ? "First 50 problems" : `${problems.length} problems`}, the newest first.</p>
  <table>
    <tr><th>Id</th><th>Name</th><th>Rating</th><th>Tags</th></tr>
    ${rows}
  </table>`);
}

export function problemPage(p, similar) {
  const rows = similar.map(
    (s) => html`<tr>
      <td><a href="/problem/${s.id}">${s.id}</a></td>
      <td>${s.name}</td>
      <td>${s.rating ?? html`<span class="muted">none</span>`}</td>
      <td>${tagLinks(s.tags)}</td>
    </tr>`,
  );
  return layout(`${p.id}. ${p.name}`, html`
  <h1>${p.id}. ${p.name}</h1>
  <p>Rating: ${p.rating ?? "none"} · Solved by ${p.solved_count} people</p>
  <p>${tagLinks(p.tags)}</p>
  <p><a href="${p.url}">Open on Codeforces</a></p>
  <h2>Similar problems</h2>
  <table>${rows}</table>`);
}

export function errorPage(message) {
  return layout("Error", html`<h1>Error</h1><p>${message}</p>`);
}
