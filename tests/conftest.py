import os

TEST_DB = "sqlite:///./test_concurso.db"
_path = TEST_DB.replace("sqlite:///", "")
if os.path.exists(_path):
    os.remove(_path)
os.environ["DATABASE_URL"] = TEST_DB

import app.models  # noqa: F401, E402
from app.db import Base, engine  # noqa: E402

Base.metadata.create_all(engine)
