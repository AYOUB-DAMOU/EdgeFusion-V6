import json
import os
from _paths import DATA_DIR

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Structure par défaut
DEFAULT_CONFIG = {
    "sources": [],   # liste des sources OPC UA
    "brokers": [],   # liste des brokers MQTT
    "options": {
        "refresh":    2,
        "reconnect":  5,
        "max_buffer": 1000
    },
    "stop_login":    "",
    "stop_password": ""
}

def config_load():
    """Charge config.json — retourne DEFAULT_CONFIG si absent/corrompu."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Fusionner avec défaut pour clés manquantes
                for key, val in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception as e:
            print(f"[CONFIG] Erreur lecture : {e}")
    return dict(DEFAULT_CONFIG)

def config_save(data):
    """Sauvegarde config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[CONFIG] Erreur sauvegarde : {e}")

def config_get_brokers():
    """Retourne la liste des brokers."""
    return config_load().get("brokers", [])

def config_get_sources():
    """Retourne la liste des sources OPC."""
    return config_load().get("sources", [])

def config_get_options():
    """Retourne les options globales."""
    return config_load().get("options", DEFAULT_CONFIG["options"])

def config_add_broker(broker):
    """Ajoute un broker et sauvegarde."""
    cfg = config_load()
    cfg["brokers"].append(broker)
    config_save(cfg)

def config_update_broker(broker_id, broker):
    """Met à jour un broker existant."""
    cfg = config_load()
    cfg["brokers"] = [b if b["id"] != broker_id else broker for b in cfg["brokers"]]
    config_save(cfg)

def config_remove_broker(broker_id):
    """Supprime un broker."""
    cfg = config_load()
    cfg["brokers"] = [b for b in cfg["brokers"] if b["id"] != broker_id]
    config_save(cfg)

def config_add_source(source):
    """Ajoute une source OPC et sauvegarde."""
    cfg = config_load()
    cfg["sources"].append(source)
    config_save(cfg)

def config_update_source(source_id, source):
    """Met à jour une source OPC existante."""
    cfg = config_load()
    cfg["sources"] = [s if s["id"] != source_id else source for s in cfg["sources"]]
    config_save(cfg)

def config_remove_source(source_id):
    """Supprime une source OPC."""
    cfg = config_load()
    cfg["sources"] = [s for s in cfg["sources"] if s["id"] != source_id]
    config_save(cfg)
