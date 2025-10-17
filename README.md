# Flask Todo App

Minimal Flask + SQLAlchemy Todo app with unit/API/E2E tests and CI. Uses an app factory, SQLite, and Playwright for browser tests.
# Flask Todo App

[![CI](https://github.com/sgtsamurai92/Bug-Tracker-App/actions/workflows/ci.yml/badge.svg)](https://github.com/sgtsamurai92/Bug-Tracker-App/actions)



![App Looks like](test-results\Screenshots\applooks.png)


## Features
- Add, edit, toggle, and delete todos; server-rendered UI (Jinja2)
- Metadata on todos: priority (low/medium/high), optional due date, created_at (UTC)
- Filter/search/sort in UI and API:
  - Search by text (q)
  - Filter by status (all/active/done)
  - Filter by priority (all/low/medium/high)
  - Sort by newest/oldest and due soon/latest
- SQLite persistence (SQLAlchemy ORM)
- JSON API
- Health check: `GET /health`
- Tests: pytest (unit+API) and Playwright (E2E)
- Dockerfile for containerized run
- GitHub Actions workflow for CI

## Architecture
- `app/__init__.py` — `create_app(test_config=None)` app factory; sets config from env with defaults:
  - `SECRET_KEY` (default "dev")
  - `DATABASE` from `TODO_DB` (default `todo.sqlite3`)
  - `TEST_RESET` enables a test-only reset endpoint
- `app/db.py` — global SQLAlchemy `engine` + `SessionLocal`; `get_db()` provides a per-request session via `flask.g` and closes on teardown
- `app/models.py` — `Base(DeclarativeBase)` and `Todo` with fields:
  - `id`, `title[200]`, `done=False`
  - `priority` (default `"medium"`), `due_date` (nullable), `created_at` (timezone-aware UTC)
- `app/routes.py` — blueprint with:
  - HTML: `GET /` (list with filters), `POST /add`, `POST /edit/<id>`, `POST /toggle/<id>`, `POST /delete/<id>`
  - API: `GET /api/todos` (supports q/status/priority/sort), `POST /api/todos`
  - Test-only: `POST /api/_reset` (requires `TEST_RESET=1`)
- `app/templates/index.html` — page with add form and a separate filters form (no nesting), plus `data-testid` attrs used by Playwright

## Run locally (Windows PowerShell)
```powershell
# Create venv and install deps
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run Flask via factory
$env:FLASK_APP = "app:create_app"; $env:FLASK_DEBUG = "1"; python -m flask run
```
App runs at http://127.0.0.1:5000. SQLite DB is `todo.sqlite3` in repo root unless `TODO_DB` is set.

## Run with Docker
```powershell
# Build image
docker build -t flask-todo-app .
# Run container mapping port 5000
docker run -e FLASK_APP=app:create_app -p 5000:5000 flask-todo-app
```

## Tests
### Python (pytest)
```powershell
. .venv\Scripts\Activate.ps1
pytest -q
```

### Playwright (E2E)
Install Node deps and browsers once:
```powershell
npm ci
npx playwright install
```
Run tests (webServer is configured in `playwright.config.ts` and uses the Flask factory):
```powershell
npx playwright test
```
If you need a clean slate across tests, set `TEST_RESET=1`:
```powershell
$env:TEST_RESET = "1"; npx playwright test
```

E2E covers add/toggle, inline edit/delete, and filter/sort behavior.

## CI (GitHub Actions)
Workflow: `.github/workflows/ci.yml`
- Sets up Python 3.11 and installs `requirements.txt`
- Sets up Node 20, runs `npm ci`, then `npx playwright install --with-deps`
- Runs Playwright tests; environment variables used:
  - `FLASK_APP: app:create_app`
  - `TEST_RESET: "1"`
  - `TODO_DB: "todo-e2e.sqlite3"`

## Useful env vars
- `SECRET_KEY` — Flask secret key (default `dev`)
- `TODO_DB` — path to SQLite DB file (default `todo.sqlite3`)
- `TEST_RESET` — when `1`, enables `POST /api/_reset` to clear all todos (used by E2E tests)

## API quick reference
- `GET /api/todos` — list todos, supports query params:
  - `q`: text search in title (case-insensitive)
  - `status`: `all` (default) | `active` | `done`
  - `priority`: `all` (default) | `low` | `medium` | `high`
  - `sort`: `-created` (newest, default) | `created` (oldest) | `due` (soonest) | `-due` (latest)
  - Response items: `{ id, title, done, priority, due_date|null }`
- `POST /api/todos` with JSON `{ "title": "...", "priority?": "low|medium|high", "due_date?": "YYYY-MM-DD" }`
  - Returns `201 { id, title, done, priority, due_date|null }`
- `POST /api/_reset` (only when `TEST_RESET=1`) → `{ ok: true }`

HTML routes
- `GET /` — list and inline edit/delete controls
- `POST /add`, `POST /toggle/<id>`, `POST /edit/<id>`, `POST /delete/<id>`

## Project structure (key files)
- `app/__init__.py` — app factory and `/health`
- `app/db.py` — engine/session lifecycle
- `app/models.py` — ORM models (`Todo`)
- `app/routes.py` — routes + API + reset endpoint
- `app/templates/index.html` — UI (with data-testids)
- `tests/` — unit (`tests/unit`), API (`tests/api`), E2E (`tests/e2e`)
- `playwright.config.ts` — webServer + baseURL + env
- `Dockerfile` — container entrypoint

## Formatting & linting (optional)
Tools in `requirements.txt`: Black, isort, Flake8, MyPy, pre-commit. Example usage:
```powershell
black .; isort .; flake8 .; mypy app
```

## Notes on schema/migrations
- SQLite columns for `priority`, `due_date`, and `created_at` are ensured at startup.
- `created_at` is timezone-aware UTC and assigned by the ORM default on insert. Existing rows are backfilled on startup.
- If you previously had an old `todo.sqlite3` schema and encounter issues, remove the file and restart, or set a different `TODO_DB` path while testing.
