"""
Gestion du démarrage automatique EdgeFusion — cross-platform.

Windows : Planificateur de tâches (schtasks) — pas de timeout SCM
Linux   : systemd (crée l'unité dans /etc/systemd/system/)

Commandes :
  install  → enregistre le démarrage automatique au boot
  remove   → supprime l'enregistrement
  start    → démarre EdgeFusion en arrière-plan maintenant
  stop     → arrête EdgeFusion en arrière-plan
"""
import sys
import os
import time
import subprocess

from _paths import STOP_SIGNAL, DATA_DIR

# ── Constantes ─────────────────────────────────────────────────────────────
_TASK_NAME = "EdgeFusion"                                     # Windows Task Scheduler
_UNIT_NAME = "edgefusion"                                     # Linux systemd
_UNIT_FILE = f"/etc/systemd/system/{_UNIT_NAME}.service"     # Linux unit path

_NO_WIN = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _exe():
    return sys.executable


# ══════════════════════════════════════════════════════════════════════════
#  WINDOWS — Task Scheduler
# ══════════════════════════════════════════════════════════════════════════

def _win_install():
    result = subprocess.run([
        "schtasks", "/create",
        "/tn",  _TASK_NAME,
        "/tr",  f'"{_exe()}" --background',
        "/sc",  "onstart",
        "/ru",  "SYSTEM",
        "/rl",  "HIGHEST",
        "/f"
    ], capture_output=True, text=True, creationflags=_NO_WIN)
    if result.returncode != 0:
        print(f"[TASK] Erreur création : {result.stderr}")
    else:
        print("[TASK] Tâche planifiée créée")


def _win_uninstall():
    _win_stop()
    subprocess.run(
        ["schtasks", "/delete", "/tn", _TASK_NAME, "/f"],
        capture_output=True, text=True, creationflags=_NO_WIN
    )
    print("[TASK] Tâche supprimée")


def _win_start():
    if os.path.exists(STOP_SIGNAL):
        try:
            os.remove(STOP_SIGNAL)
        except Exception:
            pass
    subprocess.run(
        ["schtasks", "/run", "/tn", _TASK_NAME],
        capture_output=True, text=True, creationflags=_NO_WIN
    )


def _win_stop():
    try:
        os.makedirs(os.path.dirname(STOP_SIGNAL), exist_ok=True)
        open(STOP_SIGNAL, 'w').close()
    except Exception:
        pass
    time.sleep(2)
    subprocess.run(
        ["schtasks", "/end", "/tn", _TASK_NAME],
        capture_output=True, text=True, creationflags=_NO_WIN
    )


def _win_status():
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", _TASK_NAME, "/fo", "LIST"],
            capture_output=True, text=True, encoding="cp850",
            errors="replace", creationflags=_NO_WIN
        )
        if result.returncode != 0:
            return "NOT_INSTALLED"
        out = result.stdout
        if "En cours" in out or "Running" in out:
            return "RUNNING"
        return "STOPPED"
    except Exception:
        return "NOT_INSTALLED"


# ══════════════════════════════════════════════════════════════════════════
#  LINUX — systemd
# ══════════════════════════════════════════════════════════════════════════

def _linux_unit_content():
    exe = _exe()
    return f"""[Unit]
Description=EdgeFusion OPC UA to MQTT Bridge
After=network-online.target
Wants=network-online.target

[Service]
ExecStart={exe} --background
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""


def _linux_install():
    try:
        with open(_UNIT_FILE, 'w') as f:
            f.write(_linux_unit_content())
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", _UNIT_NAME])
        print(f"[SYSTEMD] Unité {_UNIT_NAME} installée et activée")
    except PermissionError:
        print("[SYSTEMD] Droits insuffisants — relancer avec sudo")
    except Exception as e:
        print(f"[SYSTEMD] Erreur installation : {e}")


def _linux_uninstall():
    _linux_stop()
    try:
        subprocess.run(["systemctl", "disable", _UNIT_NAME])
        if os.path.exists(_UNIT_FILE):
            os.remove(_UNIT_FILE)
        subprocess.run(["systemctl", "daemon-reload"])
        print(f"[SYSTEMD] Unité {_UNIT_NAME} supprimée")
    except PermissionError:
        print("[SYSTEMD] Droits insuffisants — relancer avec sudo")
    except Exception as e:
        print(f"[SYSTEMD] Erreur suppression : {e}")


def _linux_start():
    if os.path.exists(STOP_SIGNAL):
        try:
            os.remove(STOP_SIGNAL)
        except Exception:
            pass
    subprocess.run(["systemctl", "start", _UNIT_NAME])


def _linux_stop():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        open(STOP_SIGNAL, 'w').close()
    except Exception:
        pass
    time.sleep(2)
    subprocess.run(["systemctl", "stop", _UNIT_NAME])


def _linux_status():
    try:
        r = subprocess.run(
            ["systemctl", "is-active", _UNIT_NAME],
            capture_output=True, text=True
        )
        if r.stdout.strip() == "active":
            return "RUNNING"
        if os.path.exists(_UNIT_FILE):
            return "STOPPED"
        return "NOT_INSTALLED"
    except Exception:
        return "NOT_INSTALLED"


# ══════════════════════════════════════════════════════════════════════════
#  API PUBLIQUE — dispatch selon la plateforme
# ══════════════════════════════════════════════════════════════════════════

def service_install():
    if sys.platform == "win32":
        _win_install()
    else:
        _linux_install()


def service_uninstall():
    if sys.platform == "win32":
        _win_uninstall()
    else:
        _linux_uninstall()


def service_start():
    if sys.platform == "win32":
        _win_start()
    else:
        _linux_start()


def service_stop():
    if sys.platform == "win32":
        _win_stop()
    else:
        _linux_stop()


def service_status():
    if sys.platform == "win32":
        return _win_status()
    else:
        return _linux_status()
