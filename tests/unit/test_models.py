from app.models import Todo


def test_todo_defaults():
    t = Todo(title="Test")
    assert t.title == "Test"
    assert t.done is False
