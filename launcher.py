"""
Point d'entrée unique EdgeFusion — cross-platform (Windows & Linux).

  EdgeFusion[.exe]               → Interface graphique (GUI)
  EdgeFusion[.exe] --background  → Mode arrière-plan (OPC→MQTT, sans GUI)
  EdgeFusion[.exe] install       → Enregistre le démarrage automatique au boot
  EdgeFusion[.exe] remove        → Supprime l'enregistrement
  EdgeFusion[.exe] start         → Lance EdgeFusion en arrière-plan
  EdgeFusion[.exe] stop          → Arrête EdgeFusion en arrière-plan
"""
import sys
import os
import time

# Ajouter le dossier de l'exe au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(
    sys.executable if getattr(sys, "frozen", False) else __file__
)))

# En mode frozen sans console : neutraliser stdout/stderr
if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

from _paths import STOP_SIGNAL, DATA_DIR

_TASK_CMDS = {"install", "remove", "start", "stop"}

if __name__ == "__main__":
    arg1 = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    # ── Mode arrière-plan (lancé au boot par le planificateur / systemd) ─
    if arg1 == "--background":
        # Effacer tout signal d'arrêt résiduel
        if os.path.exists(STOP_SIGNAL):
            try:
                os.remove(STOP_SIGNAL)
            except Exception:
                pass

        # Petite pause pour laisser le réseau démarrer après le boot
        time.sleep(8)

        from config      import config_get_sources, config_get_brokers, config_get_options
        from process     import start_all_sources, stop_all_sources
        from certificate import generate_certificate

        generate_certificate()
        start_all_sources(
            config_get_sources(),
            config_get_brokers(),
            config_get_options()
        )

        # Boucle principale — attendre le signal d'arrêt
        while not os.path.exists(STOP_SIGNAL):
            time.sleep(1)

        stop_all_sources()
        try:
            os.remove(STOP_SIGNAL)
        except Exception:
            pass

    # ── Commandes de gestion (install / remove / start / stop) ───────────
    elif arg1 in _TASK_CMDS:
        from service import service_install, service_uninstall, service_start, service_stop
        if arg1 == "install":
            service_install()
        elif arg1 == "remove":
            service_uninstall()
        elif arg1 == "start":
            service_start()
        elif arg1 == "stop":
            service_stop()

    # ── Interface graphique (double-clic ou sans argument) ────────────────
    else:
        from main import main
        main()
