from app.db import Base, engine
import app.models  # noqa: F401


def test_tables_registered():
    assert "questions" in Base.metadata.tables
    assert "attempts" in Base.metadata.tables


def test_db_connect():
    with engine.connect() as conn:
        assert conn is not None
