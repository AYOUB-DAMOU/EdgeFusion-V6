import ctypes
import tkinter as tk
import os
import shutil

# ============================================================
#  ICÔNE TASKBAR WINDOWS
#  SetCurrentProcessExplicitAppUserModelID doit être appelé
#  AVANT la création de la fenêtre tkinter
# ============================================================
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "ManaTechnology.EdgeFusion.2.0"
    )
except Exception:
    pass

_DIR = os.path.dirname(os.path.abspath(__file__))

# Cherche l'icône dans le dossier V4 d'abord, puis dossier parent
def _find_icon():
    candidates = [
        os.path.join(_DIR, "appicon.ico"),
        os.path.join(_DIR, "téléchargement.ico"),
        os.path.join(os.path.dirname(_DIR), "appicon.ico"),
        os.path.join(os.path.dirname(_DIR), "téléchargement.ico"),
    ]
    for path in candidates:
        if os.path.exists(path):
            # Copier avec nom sans accent si nécessaire
            safe = os.path.join(_DIR, "appicon.ico")
            if path != safe:
                try:
                    shutil.copy2(path, safe)
                except Exception:
                    pass
            return safe
    return None

ICON_SAFE = _find_icon()

from certificate import generate_certificate
from gui         import build_gui, update_loop, show_popup_info
from tray        import build_tray


def main():
    """Point d'entrée principal de l'application."""

    # Créer la fenêtre principale
    root = tk.Tk()

    # Appliquer l'icône après affichage (200ms pour éviter erreur Windows)
    def apply_icon():
        try:
            if ICON_SAFE and os.path.exists(ICON_SAFE):
                root.iconbitmap(ICON_SAFE)
                print(f"[ICON] Logo appliqué : {ICON_SAFE}")
            else:
                print("[ICON] Fichier .ico introuvable")
        except Exception as e:
            print(f"[ICON] Erreur : {e}")

    root.after(200, apply_icon)

    # Construire l'interface
    build_gui(root, ICON_SAFE)

    # Démarrer le system tray
    build_tray(root)

    # Boucle de mise à jour statut (1s)
    root.after(1000, update_loop)

    # Générer certificat au démarrage si inexistant
    generate_certificate(
        on_success=lambda msg: root.after(
            500, lambda: show_popup_info("Certificat OPC UA", msg)
        )
    )

    # Lancer l'interface
    root.mainloop()


if __name__ == "__main__":
    main()
