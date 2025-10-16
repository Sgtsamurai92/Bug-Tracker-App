from __future__ import annotations

from datetime import datetime
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import asc, delete, desc, func, select

from .db import engine, get_db
from .models import Base, Todo

bp = Blueprint("routes", __name__)


@bp.before_app_request
def ensure_tables() -> None:
    # Create tables once (safe to call repeatedly)
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """Ensure new columns for metadata exist on SQLite installs.
    Adds: priority (TEXT NOT NULL DEFAULT 'medium'), due_date (DATE),
    created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
    """
    if engine is None:
        return
    with engine.begin() as conn:
        try:
            cols = {
                row[1]
                for row in conn.exec_driver_sql("PRAGMA table_info('todos')").fetchall()
            }
        except Exception:
            return
        if "priority" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE todos ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'medium'"
            )
        if "due_date" not in cols:
            conn.exec_driver_sql("ALTER TABLE todos ADD COLUMN due_date DATE NULL")
        if "created_at" not in cols:
            # SQLite cannot add a column with a non-constant default in ALTER TABLE.
            # Add as NULLable, then backfill with CURRENT_TIMESTAMP; ORM default handles new rows.
            conn.exec_driver_sql(
                "ALTER TABLE todos ADD COLUMN created_at DATETIME NULL"
            )
            conn.exec_driver_sql(
                "UPDATE todos SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
            )


@bp.get("/")
def index():
    db = get_db()
    query = select(Todo)

    # Filters
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "all").lower()
    prio = (request.args.get("p") or "all").lower()
    sort = (request.args.get("sort") or "-created").lower()

    if q:
        query = query.where(func.lower(Todo.title).like(f"%{q.lower()}%"))
    if status in {"active", "done"}:
        query = query.where(Todo.done.is_(status == "done"))
    if prio in {"low", "medium", "high"}:
        query = query.where(Todo.priority == prio)

    # Sorting (nulls last for due_date)
    if sort == "due":
        query = query.order_by(asc(Todo.due_date.is_(None)), asc(Todo.due_date))
    elif sort == "-due":
        query = query.order_by(desc(Todo.due_date.is_(None)), desc(Todo.due_date))
    elif sort == "created":
        query = query.order_by(asc(Todo.created_at))
    else:
        query = query.order_by(desc(Todo.created_at))

    todos = db.scalars(query).all()
    return render_template(
        "index.html", todos=todos, q=q, status=status, p=prio, sort=sort
    )


@bp.post("/add")
def add():
    title = request.form.get("title", "").strip()
    priority = (request.form.get("priority") or "medium").lower()
    due_str = (request.form.get("due_date") or "").strip()
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except ValueError:
            due_date = None
    if title and priority in {"low", "medium", "high"}:
        db = get_db()
        db.add(Todo(title=title, priority=priority, due_date=due_date))
        db.commit()
    return redirect(url_for("routes.index"))


@bp.post("/toggle/<int:todo_id>")
def toggle(todo_id: int):
    db = get_db()
    todo = db.get(Todo, todo_id)
    if todo:
        todo.done = not todo.done
        db.commit()
    return redirect(url_for("routes.index"))


@bp.post("/edit/<int:todo_id>")
def edit(todo_id: int):
    """Edit a todo's title/priority/due_date via HTML form.
    Validation: title 1..200, priority in {low, medium, high},
    due_date YYYY-MM-DD or empty.
    """
    db = get_db()
    todo = db.get(Todo, todo_id)
    if not todo:
        return redirect(url_for("routes.index"))

    title = (request.form.get("title") or "").strip()
    priority = (request.form.get("priority") or "medium").lower()
    due_str = (request.form.get("due_date") or "").strip()

    # Parse due date
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except ValueError:
            # Invalid date -> ignore update for date
            due_date = todo.due_date

    # Validate inputs
    if not (1 <= len(title) <= 200) or priority not in {"low", "medium", "high"}:
        return redirect(url_for("routes.index"))

    # Apply updates
    todo.title = title
    todo.priority = priority
    todo.due_date = due_date
    db.commit()
    return redirect(url_for("routes.index"))


@bp.post("/delete/<int:todo_id>")
def delete_todo(todo_id: int):
    """Delete a todo via HTML form. Named delete_todo to avoid clashing with sqlalchemy.delete."""
    db = get_db()
    todo = db.get(Todo, todo_id)
    if todo:
        db.delete(todo)
        db.commit()
    return redirect(url_for("routes.index"))


# --- JSON API ---
@bp.get("/api/todos")
def api_list():
    db = get_db()
    query = select(Todo)
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "all").lower()
    prio = (request.args.get("priority") or "all").lower()
    sort = (request.args.get("sort") or "-created").lower()

    if q:
        query = query.where(func.lower(Todo.title).like(f"%{q.lower()}%"))
    if status in {"active", "done"}:
        query = query.where(Todo.done.is_(status == "done"))
    if prio in {"low", "medium", "high"}:
        query = query.where(Todo.priority == prio)

    if sort == "due":
        query = query.order_by(asc(Todo.due_date.is_(None)), asc(Todo.due_date))
    elif sort == "-due":
        query = query.order_by(desc(Todo.due_date.is_(None)), desc(Todo.due_date))
    elif sort == "created":
        query = query.order_by(asc(Todo.created_at))
    else:
        query = query.order_by(desc(Todo.created_at))

    todos = db.scalars(query).all()
    return jsonify(
        [
            {
                "id": t.id,
                "title": t.title,
                "done": t.done,
                "priority": getattr(t, "priority", "medium"),
                "due_date": (
                    t.due_date.isoformat() if getattr(t, "due_date", None) else None
                ),
            }
            for t in todos
        ]
    )


@bp.post("/api/todos")
def api_create():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    priority = (data.get("priority") or "medium").lower()
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        except ValueError:
            return {"error": "invalid due_date"}, 400
    if not (1 <= len(title) <= 200):
        return {"error": "title required"}, 400
    if priority not in {"low", "medium", "high"}:
        return {"error": "invalid priority"}, 400
    db = get_db()
    todo = Todo(title=title, priority=priority, due_date=due_date)
    db.add(todo)
    db.commit()
    return {
        "id": todo.id,
        "title": todo.title,
        "done": todo.done,
        "priority": todo.priority,
        "due_date": (todo.due_date.isoformat() if todo.due_date else None),
    }, 201


@bp.patch("/api/todos/<int:todo_id>")
def api_update(todo_id: int):
    data = request.get_json(force=True) or {}
    db = get_db()
    todo = db.get(Todo, todo_id)
    if not todo:
        return {"error": "not found"}, 404
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not (1 <= len(title) <= 200):
            return {"error": "invalid title"}, 400
        todo.title = title
    if "done" in data:
        done = data.get("done")
        if not isinstance(done, bool):
            return {"error": "invalid done"}, 400
        todo.done = done
    db.commit()
    return {"id": todo.id, "title": todo.title, "done": todo.done}


@bp.delete("/api/todos/<int:todo_id>")
def api_delete(todo_id: int):
    db = get_db()
    todo = db.get(Todo, todo_id)
    if not todo:
        return {"error": "not found"}, 404
    db.delete(todo)
    db.commit()
    return {}, 204


@bp.post("/api/_reset")
def api_reset():
    if not current_app.config.get("TEST_RESET"):
        return {"error": "forbidden"}, 403
    db = get_db()
    db.execute(delete(Todo))
    db.commit()
    return {"ok": True}
