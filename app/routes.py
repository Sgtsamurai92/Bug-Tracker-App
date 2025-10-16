from __future__ import annotations

import sqlalchemy as sa
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select

from .db import engine, get_db
from .models import Base, Todo

bp = Blueprint("routes", __name__)


@bp.before_app_request
def ensure_tables() -> None:
    # Create tables once (safe to call repeatedly)
    if engine is not None:
        Base.metadata.create_all(bind=engine)


@bp.get("/")
def index():
    db = get_db()
    todos = db.scalars(select(Todo)).all()
    return render_template("index.html", todos=todos)


@bp.post("/add")
def add():
    title = request.form.get("title", "").strip()
    if title:
        db = get_db()
        db.add(Todo(title=title))
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
    title = (request.form.get("title") or "").strip()
    if not (1 <= len(title) <= 200):
        # Simple flash could be added; for now, ignore invalid edits
        return redirect(url_for("routes.index"))
    db = get_db()
    todo = db.get(Todo, todo_id)
    if todo:
        todo.title = title
        db.commit()
    return redirect(url_for("routes.index"))


@bp.post("/delete/<int:todo_id>")
def delete_todo(todo_id: int):
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
    todos = db.scalars(select(Todo)).all()
    return jsonify([{"id": t.id, "title": t.title, "done": t.done} for t in todos])


@bp.post("/api/todos")
def api_create():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    if not (1 <= len(title) <= 200):
        return {"error": "title required"}, 400
    db = get_db()
    todo = Todo(title=title)
    db.add(todo)
    db.commit()
    return {"id": todo.id, "title": todo.title, "done": todo.done}, 201


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
    db.execute(sa.delete(Todo))
    db.commit()
    return {"ok": True}
