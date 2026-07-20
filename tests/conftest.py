import os

TEST_DB = "sqlite:///./test_concurso.db"
_path = TEST_DB.replace("sqlite:///", "")
if os.path.exists(_path):
    os.remove(_path)
os.environ["DATABASE_URL"] = TEST_DB

from app.db import Base, engine  # noqa: E402

import app.models  # noqa: F401

Base.metadata.create_all(engine)
