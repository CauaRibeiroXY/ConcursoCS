import datetime
import os
import shutil

from app.config import DATABASE_URL
from app.logger import get_logger

log = get_logger(__name__)
BACKUP_DIR = "backups"
KEEP = 7


def backup() -> str | None:
    if not DATABASE_URL.startswith("sqlite"):
        log.warning("backup automático disponível apenas para SQLite")
        return None
    src = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(src):
        log.warning("banco de origem não encontrado: %s", src)
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"concurso_{stamp}.db")
    shutil.copyfile(src, dst)
    _prune()
    log.info("backup criado: %s", dst)
    return dst


def _prune() -> None:
    files = sorted(
        f for f in os.listdir(BACKUP_DIR) if f.startswith("concurso_") and f.endswith(".db")
    )
    for old in files[:-KEEP]:
        os.remove(os.path.join(BACKUP_DIR, old))


if __name__ == "__main__":
    backup()
