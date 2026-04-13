"""
SQLite en archivo bajo tests/ para que `import app` no use convivencia.db del desarrollo.
"""
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_TEST_DB = _ROOT / "tests" / "_pytest_convivencia.db"


def pytest_configure(config):
    os.environ["DATABASE_URL"] = ""
    import ce_db

    ce_db.DATABASE_FILE = str(_TEST_DB)
    if _TEST_DB.exists():
        try:
            _TEST_DB.unlink()
        except OSError:
            pass


def pytest_sessionfinish(session, exitstatus):
    if _TEST_DB.exists():
        try:
            _TEST_DB.unlink()
        except OSError:
            pass


import pytest


@pytest.fixture(scope="session")
def flask_app():
    from ce_db import init_db
    from app import app as application

    init_db()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()
