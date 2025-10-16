from app.models import Todo


def test_todo_defaults():
    t = Todo(title="Test")
    assert t.title == "Test"
    assert t.done is False
    assert t.priority == "medium"
    # created_at is assigned at insert time (via ORM default), so None before persisting
    assert t.created_at is None
    # due_date defaults to None
    assert t.due_date is None
