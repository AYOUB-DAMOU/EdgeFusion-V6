import json
import os
from _paths import DATA_DIR

def _buffer_path(source_id):
    """Retourne le chemin du fichier buffer pour une source donnée."""
    return os.path.join(DATA_DIR, f"buffer_{source_id}.json")

def buffer_load(source_id):
    """Charge le buffer persistant depuis fichier pour une source."""
    path = _buffer_path(source_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[BUFFER:{source_id}] {len(data)} message(s) récupéré(s)")
                return data
        except Exception as e:
            print(f"[BUFFER:{source_id}] Erreur lecture : {e}")
    return []

def buffer_save(source_id, buffer):
    """Sauvegarde le buffer dans fichier pour une source."""
    path = _buffer_path(source_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(buffer, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[BUFFER:{source_id}] Erreur sauvegarde : {e}")

def buffer_clear(source_id):
    """Supprime le fichier buffer d'une source."""
    path = _buffer_path(source_id)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"[BUFFER:{source_id}] Erreur suppression : {e}")

def buffer_count(source_id):
    """Retourne le nombre de messages en buffer pour une source."""
    path = _buffer_path(source_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return len(json.load(f))
        except Exception:
            return 0
    return 0

def buffer_add(source_id, topic, payload, max_buffer):
    """
    Ajoute un message au buffer d'une source.
    Retourne True si ajouté, False si buffer plein.
    """
    buf = buffer_load(source_id)
    if len(buf) < max_buffer:
        buf.append({"topic": topic, "payload": payload})
        buffer_save(source_id, buf)
        print(f"[BUFFER:{source_id}] Stocké ({len(buf)}/{max_buffer})")
        return True
    else:
        print(f"[BUFFER:{source_id}] Plein ({max_buffer}), message ignoré")
        return False
