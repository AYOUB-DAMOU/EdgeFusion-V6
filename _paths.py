"""
Chemins de l'application EdgeFusion — cross-platform (Windows & Linux).

Mode développement  (script Python)   : dossier du fichier .py
Mode production Windows (PyInstaller) : C:\\ProgramData\\EdgeFusion\\
Mode production Linux   (PyInstaller) : /var/lib/edgefusion/
"""
import os
import sys


def get_app_dir():
    """Dossier de l'exécutable (lecture seule en prod)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir():
    """
    Dossier de données persistantes : config, buffer, certificats, journal.
    Toujours accessible en écriture, même sans droits admin.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            path = os.path.join(
                os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "EdgeFusion"
            )
        else:
            path = "/var/lib/edgefusion"
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(path, exist_ok=True)
    return path


APP_DIR     = get_app_dir()
DATA_DIR    = get_data_dir()
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
STOP_SIGNAL = os.path.join(DATA_DIR, "stop.signal")
