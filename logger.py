"""
Logs EdgeFusion — fichier uniquement, aucun affichage dans l'interface.

Emplacement : C:\\ProgramData\\EdgeFusion\\logs\\edgefusion_YYYY-MM-DD.log
Rotation     : un fichier par jour, jamais supprimé
Format       : [2026-01-15 14:32:01] [INFO    ] [module] message
"""
import logging
import logging.handlers
import os
import time
from datetime import datetime
from _paths import DATA_DIR

LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FMT  = "[%(asctime)s] [%(levelname)-8s] %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"


def _get_log_file():
    return os.path.join(LOG_DIR, f"edgefusion_{datetime.now().strftime('%Y-%m-%d')}.log")


class DailyFileHandler(logging.FileHandler):
    """Un fichier par jour, jamais supprimé, résistant au verrouillage."""

    def __init__(self):
        self._current_date = datetime.now().strftime('%Y-%m-%d')
        super().__init__(_get_log_file(), encoding="utf-8")

    def emit(self, record):
        today = datetime.now().strftime('%Y-%m-%d')
        if today != self._current_date:
            self._current_date = today
            try:
                self.close()
                self.baseFilename = _get_log_file()
                self.stream = self._open()
            except Exception:
                pass
        try:
            super().emit(record)
        except (PermissionError, OSError):
            try:
                self.close()
                time.sleep(0.1)
                self.stream = self._open()
                super().emit(record)
            except Exception:
                pass


def _build_root_logger():
    logger = logging.getLogger("EdgeFusion")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FMT, datefmt=_DATE)

    fh = DailyFileHandler()
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
    return _get_log_file()
