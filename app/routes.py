from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from sqlalchemy import select, delete
from .db import get_db, engine
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
    if not title:
        return {"error": "title required"}, 400
    db = get_db()
    todo = Todo(title=title)
    db.add(todo)
    db.commit()
    return {"id": todo.id, "title": todo.title, "done": todo.done}, 201


@bp.post("/api/_reset")
def api_reset():
    if not current_app.config.get("TEST_RESET"):
        return {"error": "forbidden"}, 403
    db = get_db()
    db.execute(delete(Todo))
    db.commit()
    return {"ok": True}