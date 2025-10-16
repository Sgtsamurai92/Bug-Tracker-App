"""Unit tests for the ORM model layer.

This module verifies the default values and construction-time state of the
`Todo` model without touching the database. Keeping these tests focused on
in-memory behavior makes them fast and reliable.
"""

from app.models import Todo


def test_todo_defaults():
    """Newly constructed Todo should have sane defaults before persistence."""
    t = Todo(title="Test")
    # Title is set from constructor
    assert t.title == "Test"
    # New items are not done by default
    assert t.done is False
    # Priority defaults to "medium" unless specified
    assert t.priority == "medium"
    # created_at is assigned at insert time (via ORM default), so None before persisting
    assert t.created_at is None
    # due_date defaults to None
    assert t.due_date is None
