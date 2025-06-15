from psycopg2.pool import SimpleConnectionPool
from psycopg2.extensions import connection
from flask import current_app, g

__all__ = ["get_db", "init_app"]

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=current_app.config["DATABASE_URL"],
        )
    return _pool

def _close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        _get_pool().putconn(db)

def get_db() -> connection:
    if "db" not in g:
        g.db = _get_pool().getconn()
    return g.db

def init_app(app):
    app.teardown_appcontext(_close_db)