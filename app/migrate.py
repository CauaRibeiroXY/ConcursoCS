from app.db import Base, engine
from app.logger import get_logger

log = get_logger(__name__)


def init_db() -> None:
    import app.models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(engine)
    log.info("database initialized")


if __name__ == "__main__":
    init_db()
