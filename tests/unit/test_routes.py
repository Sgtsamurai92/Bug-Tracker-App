"""Unit tests for lightweight Flask routes.

These tests exercise request/response behavior using Flask's built-in
`test_client`. They intentionally avoid starting a real HTTP server for
speed and determinism.
"""

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    """Create an isolated Flask test client per test.

    - Sets TESTING=True to enable better error reporting.
    - Points the app to a temporary SQLite file so each test has a fresh DB.
    """
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite3"),
        }
    )
    return app.test_client()


def test_health(client):
    """The /health endpoint should report a 200 OK JSON payload."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"
