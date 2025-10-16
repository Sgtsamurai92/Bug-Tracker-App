import os

from flask import Flask

from .db import init_db


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory for the Flask app.

    - Reads basic config from environment with sensible defaults
    - Initializes the SQLAlchemy engine/session lifecycle
    - Registers the blueprint with routes and APIs
    - Exposes a simple /health endpoint for monitoring/tests
    """
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.environ.get("TODO_DB", "todo.sqlite3"),
        TEST_RESET=os.environ.get("TEST_RESET", "0") == "1",
    )

    if test_config:
        app.config.update(test_config)

    init_db(app)

    from .routes import bp as routes_bp

    app.register_blueprint(routes_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
