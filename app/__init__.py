from flask import Flask
from .db import init_db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev",
        DATABASE="todo.sqlite3",
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
