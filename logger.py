"""
Logs EdgeFusion — fichier uniquement, aucun affichage dans l'interface.

Emplacement : C:\\ProgramData\\EdgeFusion\\logs\\edgefusion.log
Rotation     : 5 MB max par fichier, 5 fichiers conservés
Format       : [2026-01-15 14:32:01] [INFO    ] [module] message
"""
import logging
import logging.handlers
import os
from _paths import DATA_DIR

LOG_DIR  = os.path.join(DATA_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "edgefusion.log")
os.makedirs(LOG_DIR, exist_ok=True)

_FMT  = "[%(asctime)s] [%(levelname)-8s] %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"


def _build_root_logger():
    logger = logging.getLogger("EdgeFusion")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FMT, datefmt=_DATE)

    # Fichier rotatif (5 MB × 5 fichiers)
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024,
        backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


_build_root_logger()


def get_logger(name: str = "") -> logging.Logger:
    """Retourne un logger enfant sous EdgeFusion.<name>."""
    return logging.getLogger(f"EdgeFusion.{name}" if name else "EdgeFusion")


def get_log_file() -> str:
    """Retourne le chemin absolu du fichier log courant."""
    return LOG_FILE
