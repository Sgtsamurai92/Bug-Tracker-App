import threading

import httpx
from werkzeug.serving import make_server

from app import create_app


class ServerThread(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.srv = make_server("127.0.0.1", 5001, app)

    def run(self):
        self.srv.serve_forever()

    def stop(self):
        self.srv.shutdown()


def test_api_crud(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "test.sqlite3")})
    server = ServerThread(app)
    server.start()

    try:
        base = "http://127.0.0.1:5001"
        # list empty
        r = httpx.get(f"{base}/api/todos")
        assert r.status_code == 200 and r.json() == []
        # create several with metadata
        r = httpx.post(
            f"{base}/api/todos", json={"title": "Write tests", "priority": "high"}
        )
        assert r.status_code == 201 and r.json()["priority"] == "high"
        r = httpx.post(
            f"{base}/api/todos",
            json={"title": "Do chores", "priority": "low", "due_date": "2099-01-01"},
        )
        assert r.status_code == 201
        r = httpx.post(
            f"{base}/api/todos", json={"title": "Buy milk", "priority": "medium"}
        )
        assert r.status_code == 201

        # list has three
        r = httpx.get(f"{base}/api/todos")
        data = r.json()
        assert len(data) == 3

        # filter by priority
        r = httpx.get(f"{base}/api/todos", params={"priority": "low"})
        low_items = r.json()
        assert all(it["priority"] == "low" for it in low_items)

        # search by q
        r = httpx.get(f"{base}/api/todos", params={"q": "milk"})
        milk_items = r.json()
        assert len(milk_items) == 1 and milk_items[0]["title"].lower().find("milk") >= 0

        # sort by due (soonest first), NULLs last
        r = httpx.get(f"{base}/api/todos", params={"sort": "due"})
        by_due = r.json()
        # first should have a due_date (the one we set), others can be None
        assert by_due[0]["due_date"] is not None
    finally:
        server.stop()
