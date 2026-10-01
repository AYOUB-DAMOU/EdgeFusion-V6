import threading
import os
import time
import json
import process
from _paths import STATUS_FILE

_tray_icon = None
_root      = None

def build_tray(root_window):
    """Crée et démarre l'icône system tray."""
    global _root
    _root = root_window
    threading.Thread(target=_run_tray,        daemon=True).start()
    threading.Thread(target=_update_tray_tip, daemon=True).start()

def _update_tray_tip():
    """Met à jour le menu et tooltip du tray toutes les 3 secondes."""
    while True:
        time.sleep(3)
        if _tray_icon is None:
            continue
        try:
            statuses = _get_tray_statuses()
            if not statuses:
                _tray_icon.title = "EdgeFusion — Inactif"
            else:
                parts = []
                for sid, st in statuses.items():
                    opc  = "OK" if st.get("opc")  == "CONNECTED" else "--"
                    mqtt = "OK" if st.get("mqtt") == "CONNECTED" else "--"
                    parts.append(f"OPC:{opc} MQTT:{mqtt}")
                _tray_icon.title = "EdgeFusion — " + " | ".join(parts)
            _tray_icon.update_menu()
        except Exception:
            pass

def _load_tray_icon():
    """Charge l'icône pour le tray — utilise appicon.ico si disponible."""
    from PIL import Image, ImageDraw
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appicon.ico")
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path).convert("RGBA").resize((64, 64))
        except Exception:
            pass
    # Fallback : cercle bleu généré
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill="#1E3A8A", outline="#90CAF9", width=3)
    d.text((16, 20), "EF", fill="#90CAF9")
    return img


def _build_menu():
    """Construit dynamiquement le menu tray complet."""
    import pystray
    items = [
        pystray.MenuItem("Edge Fusion", None, enabled=False),
        pystray.Menu.SEPARATOR,
    ]
    try:
        items += list(_status_items())
    except Exception:
        items.append(pystray.MenuItem("Statut indisponible", None, enabled=False))
    items += [
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("📂 Ouvrir",     _tray_open),
        pystray.MenuItem("🔄 Redémarrer", _tray_restart),
        pystray.MenuItem("⏹  Arrêter",    _tray_stop),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Quitter",     _tray_quit),
    ]
    return items

def _run_tray():
    global _tray_icon
    try:
        import pystray

        img = _load_tray_icon()

        _tray_icon = pystray.Icon(
            "EdgeFusion",
            img,
            "EdgeFusion",
            menu=pystray.Menu(_build_menu)
        )
        _tray_icon.run()

    except ImportError:
        print("[TRAY] pystray ou Pillow non installé — tray désactivé")
        print("[TRAY] pip install pystray pillow")
    except Exception as e:
        print(f"[TRAY] Erreur démarrage tray : {e}")

def _get_tray_statuses():
    """Retourne le statut des sources.
    - Mémoire locale en priorité (tray = même processus que GUI)
    - Fichier status.json si mémoire vide (service externe actif)
    """
    statuses = process.get_sources_status()
    if statuses:
        return statuses
    # Fallback : service Windows séparé → lire fichier partagé
    try:
        if os.path.exists(STATUS_FILE):
            if time.time() - os.path.getmtime(STATUS_FILE) < 20:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception:
        pass
    return {}

def _status_items():
    """Génère un item de menu par source avec nom + OPC + MQTT + broker."""
    import pystray
    from config import config_get_sources, config_get_brokers

    try:
        sources  = config_get_sources()
        brokers  = {b["id"]: b for b in config_get_brokers()}
        statuses = _get_tray_statuses()

        if not sources:
            yield pystray.MenuItem("Aucune source configurée", None, enabled=False)
            return

        for source in sources:
            sid   = source["id"]
            sname = source.get("name", sid[:8])
            bid   = source.get("broker_id", "")
            bhost = brokers.get(bid, {}).get("host", "?")
            st    = statuses.get(sid, {})
            opc   = "OK" if st.get("opc")  == "CONNECTED" else "--"
            mqtt  = "OK" if st.get("mqtt") == "CONNECTED" else "--"
            yield pystray.MenuItem(
                f"{sname}   OPC:{opc}  MQTT:{mqtt}   [{bhost}]",
                None, enabled=False
            )
    except Exception:
        yield pystray.MenuItem("Statut indisponible", None, enabled=False)

def _tray_open(icon, item):
    """Ouvre la fenêtre principale."""
    if _root:
        _root.after(0, _root.deiconify)

def _tray_stop(icon, item):
    """Arrête toutes les sources — avec authentification si configurée."""
    def _do_stop():
        try:
            from service import service_status, service_stop
            if service_status() in ("RUNNING",):
                service_stop()
                return
        except Exception:
            pass
        process.stop_all_sources()

    if _root:
        _root.after(0, _root.deiconify)
        from gui import open_stop_auth_popup
        _root.after(100, lambda: open_stop_auth_popup(_do_stop))

def _tray_restart(icon, item):
    """Redémarre toutes les sources — service-aware."""
    try:
        from service import service_status, service_stop, service_start
        if service_status() in ("RUNNING", "STOPPED"):
            service_stop()
            time.sleep(2)
            service_start()
            return
    except Exception:
        pass
    # Mode standalone : threads locaux
    from config import config_get_sources, config_get_brokers, config_get_options
    process.stop_all_sources()
    time.sleep(1)
    process.start_all_sources(
        config_get_sources(),
        config_get_brokers(),
        config_get_options()
    )

def _tray_quit(icon, item):
    """Quitte complètement l'application — avec authentification si configurée."""
    if _root:
        # Ouvrir fenêtre d'abord pour afficher la popup
        _root.after(0, _root.deiconify)

        def _launch_quit_popup():
            from gui import open_quit_auth_popup
            # On passe un callback qui stoppe aussi l'icône tray
            def _on_quit_confirmed():
                try:
                    icon.stop()
                except Exception:
                    pass
                import process
                process.stop_all_sources()
                _root.destroy()

            from gui import _auth_popup, RED_BG, RED_BD, RED
            _auth_popup(
                title        = "QUITTER L'APPLICATION",
                subtitle     = "Cette action arrêtera tous les bridges OPC→MQTT",
                btn_text     = "❌  Quitter",
                btn_bg       = RED_BG,
                btn_bd       = RED_BD,
                btn_fg       = RED,
                on_confirmed = _on_quit_confirmed
            )

        _root.after(100, _launch_quit_popup)

def tray_notify(title, message):
    """Affiche une notification depuis le tray."""
    if _tray_icon:
        try:
            _tray_icon.notify(message, title)
        except Exception:
            pass
