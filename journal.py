"""
Journal des données OPC UA remontées par EdgeFusion.
Stocke les dernières 500 entrées en mémoire ET dans un fichier CSV persistant.

Fichier : C:\\ProgramData\\EdgeFusion\\logs\\journal.csv
Alimenté par process.py après chaque cycle de lecture OPC.
Consulté par gui.py pour affichage en temps réel.
"""
from collections import deque
import datetime
import threading
import csv
import os

from _paths import DATA_DIR

JOURNAL_FILE = os.path.join(DATA_DIR, "logs", "journal.csv")
_CSV_FIELDS  = ["ts", "source", "tag", "node_id", "value", "ok", "reason"]

_lock       = threading.Lock()
_entries    = deque(maxlen=500)
_prev_state = {}   # {(source, tag): (value_str, ok_bool)}


def _ensure_file():
    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    if not os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=_CSV_FIELDS).writeheader()


def _append_to_csv(entries):
    """Ajoute les nouvelles entrées au fichier CSV (sans réécrire tout le fichier)."""
    try:
        _ensure_file()
        with open(JOURNAL_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            for e in entries:
                writer.writerow({k: e.get(k, "") for k in _CSV_FIELDS})
    except Exception:
        pass


def _load_from_csv():
    """Charge les 500 dernières entrées depuis le CSV au démarrage."""
    try:
        if not os.path.exists(JOURNAL_FILE):
            return []
        with open(JOURNAL_FILE, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        # Convertir ok de str vers bool
        for r in rows:
            r["ok"] = r.get("ok", "True") in ("True", "1", "true")
        return rows[-500:]
    except Exception:
        return []


def _init():
    """Initialise le journal depuis le CSV existant."""
    rows = _load_from_csv()
    with _lock:
        _entries.extend(rows)


def add_entries(source_name, data, quality_info):
    """
    Ajoute au journal les lectures OPC d'un cycle.

    Journalise uniquement quand quelque chose change :
      - Premiere lecture d'un tag
      - La valeur a change depuis la derniere lecture
      - La qualite a change (bonne -> mauvaise ou inverse)
    """
    ts          = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entries = []

    for mqtt_key, value in data.items():
        q        = quality_info.get(mqtt_key, {"ok": True, "reason": ""})
        ok       = q["ok"]
        val_str  = str(value)
        key      = (source_name, mqtt_key)
        prev     = _prev_state.get(key)
        current  = (val_str, ok)

        if prev is None or prev != current:
            new_entries.append({
                "ts":      ts,
                "source":  source_name,
                "tag":     mqtt_key,
                "node_id": q.get("node_id", ""),
                "value":   val_str,
                "ok":      ok,
                "reason":  q.get("reason", ""),
            })

        _prev_state[key] = current

    if new_entries:
        with _lock:
            _entries.extend(new_entries)
        _append_to_csv(new_entries)


def get_entries(only_bad=False):
    """Retourne une copie de la liste des entrées (récentes en dernier)."""
    with _lock:
        if only_bad:
            return [e for e in _entries if not e["ok"]]
        return list(_entries)


def clear():
    """Vide le journal en mémoire et efface le fichier CSV."""
    global _prev_state
    with _lock:
        _entries.clear()
    _prev_state = {}
    try:
        _ensure_file()
        with open(JOURNAL_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=_CSV_FIELDS).writeheader()
    except Exception:
        pass


# Chargement automatique au démarrage
_init()
