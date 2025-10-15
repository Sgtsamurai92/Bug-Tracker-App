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
        # create
        r = httpx.post(f"{base}/api/todos", json={"title": "Write tests"})
        assert r.status_code == 201 and r.json()["title"] == "Write tests"
        # list has one
        r = httpx.get(f"{base}/api/todos")
        data = r.json()
        assert len(data) == 1 and data[0]["done"] is False
    finally:
        server.stop()
