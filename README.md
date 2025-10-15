# Flask Todo App

Minimal Flask + SQLAlchemy Todo app with unit/API/E2E tests and CI. Uses an app factory, SQLite, and Playwright for browser tests.

## Features
- Add/toggle todos; server-rendered UI (Jinja2)
- SQLite persistence (SQLAlchemy ORM)
- JSON API: `GET/POST /api/todos`
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
- `app/models.py` — `Base(DeclarativeBase)` and `Todo(id, title[200], done=False)`
- `app/routes.py` — blueprint with:
  - HTML: `GET /` (list), `POST /add`, `POST /toggle/<id>`
  - API: `GET /api/todos`, `POST /api/todos`
  - Test-only: `POST /api/_reset` (requires `TEST_RESET=1`)
- `app/templates/index.html` — minimal page with `data-testid` attrs used by Playwright

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
- `GET /api/todos` → `[{ id, title, done }]`
- `POST /api/todos` with JSON `{ "title": "..." }` → `201 { id, title, done }`
- `POST /api/_reset` (only when `TEST_RESET=1`) → `{ ok: true }`

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
