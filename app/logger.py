import logging
import sys


def get_logger(name: str = "app"):
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log
