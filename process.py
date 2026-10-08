import threading
import time
from datetime import datetime
from opcua import ua

from opc_client   import connect_opc, read_opc_tags
from mqtt_client  import connect_mqtt, build_payloads, publish_mqtt, build_meta
from operations   import apply_all_operations
from excel_reader import load_excel
from buffer       import buffer_load, buffer_save, buffer_clear, buffer_add
from logger       import get_logger
from _paths       import STATUS_FILE
import journal as _journal

_log = get_logger("process")

# ============================================================
#  ÉTAT GLOBAL DES SOURCES
# ============================================================
# Dict {source_id: {"opc": str, "mqtt": dict{broker_id: str},
#                   "buffer": str, "buffer_count": int, "last_data": str}}
sources_status   = {}
_threads         = {}   # {source_id: threading.Thread}
_running         = {}   # {source_id: bool}
_cert_rejected   = {}   # {source_id: bool}
_disconnect_since = {}  # {source_id: {"opc": float|None, "mqtt": {broker_id: float|None}}}

STABILITY_DELAY = 5

popup_callback = None

def _notify_popup(title, message):
    if popup_callback:
        popup_callback(title, message)


# ============================================================
#  BOUCLE D'UNE SOURCE  — MULTI-BROKERS
# ============================================================
def run_source(source_config, broker_configs, options):
    """
    Boucle principale pour une source OPC UA → plusieurs brokers MQTT.

    - source_config  : dict avec broker_ids (liste)
    - broker_configs : liste de dicts broker
    - options        : dict {refresh, reconnect, max_buffer}
    """
    source_id       = source_config["id"]
    refresh         = float(options.get("refresh",    2))
    reconnect_delay = float(options.get("reconnect",  5))
    max_buffer      = int(options.get("max_buffer",   1000))

    # Construire mqtt_config par broker
    mqtt_configs = {}
    for bc in broker_configs:
        bid = bc["id"]
        mqtt_configs[bid] = {
            "host":         bc["host"],
            "port":         bc.get("port", "1883"),
            "username":     source_config.get("mqtt_user",  ""),
            "password":     source_config.get("mqtt_pass",  ""),
            "client_id":    source_config.get("client_id",  "") + f"_{bid}",
            "qos":          source_config.get("qos", 1),
            "tls":          bc.get("tls", False),
            "ca_cert":      bc.get("ca_cert", ""),
            "client_cert":  bc.get("client_cert", ""),
            "client_key":   bc.get("client_key", ""),
            "tls_insecure": bc.get("tls_insecure", False),
        }

    opc_client          = None
    mqtt_clients        = {bid: None for bid in mqtt_configs}  # {broker_id: client|None}
    last_opc_attempt    = 0
    last_mqtt_attempts  = {bid: 0 for bid in mqtt_configs}
    buffers             = {bid: buffer_load(f"{source_id}_{bid}") for bid in mqtt_configs}

    # Charger Excel
    try:
        excel_data      = load_excel(source_config["excel_path"])
        tags            = excel_data["tags"]
        tag_topics      = excel_data["tag_topics"]
        tag_mapping     = excel_data["tag_mapping"]
        tag_operations  = excel_data["tag_operations"]
        _log.info(f"[SOURCE:{source_id}] Excel chargé : {excel_data['summary']}")
    except Exception as e:
        _log.error(f"[SOURCE:{source_id}] Erreur Excel : {e}")
        _update_status(source_id, opc="DISCONNECTED",
                       mqtt={bid: "DISCONNECTED" for bid in mqtt_configs})
        return

    # Init statut
    _update_status(source_id, opc="DISCONNECTED",
                   mqtt={bid: "DISCONNECTED" for bid in mqtt_configs})

    # ---- MQTT Callbacks (par broker) ----
    def _make_mqtt_callbacks(bid):
        def on_connect(rc):
            if rc == 0:
                _update_mqtt_status(source_id, bid, "CONNECTED")
                _log.info(f"[MQTT:{source_id}→{bid}] Connecté")
            else:
                _update_mqtt_status(source_id, bid, "DISCONNECTED")
                _log.warning(f"[MQTT:{source_id}→{bid}] Echec rc={rc}")

        def on_disconnect(rc):
            _update_mqtt_status(source_id, bid, "DISCONNECTED")
            _log.warning(f"[MQTT:{source_id}→{bid}] Déconnecté rc={rc}")

        return on_connect, on_disconnect

    # ---- Boucle principale ----
    while _running.get(source_id, False):
        now = time.time()

        # ===== RECONNEXION OPC =====
        if opc_client is None and (now - last_opc_attempt) >= reconnect_delay:
            last_opc_attempt = now
            try:
                opc_client = connect_opc(
                    source_config["opc_url"],
                    source_config.get("opc_user", ""),
                    source_config.get("opc_pass", "")
                )
                _update_status(source_id, opc="CONNECTED")
                _cert_rejected[source_id] = False
                _log.info(f"[OPC:{source_id}] Connecté à {source_config['opc_url']}")

            except ua.UaStatusCodeError as e:
                opc_client = None
                _update_status(source_id, opc="DISCONNECTED")
                err_str = str(e)
                if "BadCertificate" in err_str or "BadSecurityChecksFailed" in err_str:
                    if not _cert_rejected.get(source_id, False):
                        _cert_rejected[source_id] = True
                        _notify_popup(
                            "Certificat OPC UA",
                            f"Source : {source_config['name']}\n\n"
                            "Certificat non approuvé\npar le serveur ⚠️\n\n"
                            "L'administrateur doit approuver\n"
                            "client_cert.pem dans le serveur OPC."
                        )
                    _log.warning(f"[OPC:{source_id}] Certificat non approuvé")
                else:
                    _log.error(f"[OPC:{source_id}] Erreur UA : {e}")

            except Exception as e:
                opc_client = None
                _update_status(source_id, opc="DISCONNECTED")
                _log.error(f"[OPC:{source_id}] Erreur connexion : {e}")

        # ===== RECONNEXION MQTT — indépendante par broker =====
        for bid, mcfg in mqtt_configs.items():
            if mqtt_clients[bid] is None and (now - last_mqtt_attempts[bid]) >= reconnect_delay:
                last_mqtt_attempts[bid] = now
                on_conn, on_disc = _make_mqtt_callbacks(bid)
                try:
                    mqtt_clients[bid] = connect_mqtt(mcfg, on_connect_cb=on_conn, on_disconnect_cb=on_disc)
                except Exception as e:
                    mqtt_clients[bid] = None
                    _update_mqtt_status(source_id, bid, "DISCONNECTED")
                    _log.error(f"[MQTT:{source_id}→{bid}] Erreur connexion : {e}")

        # ===== LECTURE OPC =====
        data   = {}
        opc_ok = False

        if opc_client is not None:
            try:
                data, quality_info = read_opc_tags(opc_client, tags, tag_mapping)
                opc_ok = True

                if tag_operations:
                    apply_all_operations(data, tag_operations, tag_mapping)

                _journal.add_entries(source_config.get("name", source_id), data, quality_info)

                _update_status(
                    source_id, opc="CONNECTED",
                    last_data=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

            except Exception as e:
                _log.error(f"[OPC:{source_id}] Erreur lecture : {type(e).__name__} | {e}")
                _update_status(source_id, opc="DISCONNECTED")
                try:
                    opc_client.disconnect()
                except Exception:
                    pass
                opc_client       = None
                last_opc_attempt = time.time()

        # ===== BUILD PAYLOADS =====
        meta     = build_meta(opc_ok, source_config.get("client_id", source_config.get("mqtt_user", "")))
        messages = build_payloads(
            data if opc_ok else {},
            tag_topics, tag_mapping, meta,
            source_config["topic"]
        )

        # ===== PUBLISH MQTT — indépendant par broker =====
        total_buffered = 0
        any_connected  = False

        for bid, mcfg in mqtt_configs.items():
            client = mqtt_clients[bid]
            buf    = buffers[bid]
            buf_id = f"{source_id}_{bid}"
            qos    = mcfg.get("qos", 1)

            if client is not None:
                any_connected = True
                try:
                    # Renvoi buffer
                    if buf:
                        _log.info(f"[BUFFER:{source_id}→{bid}] Renvoi de {len(buf)} message(s)")
                        import paho.mqtt.client as _paho
                        sent = 0
                        skipped = 0
                        for item in list(buf):
                            t = item.get("topic", "")
                            if not t or not t.strip():
                                buf.remove(item)
                                skipped += 1
                                continue
                            result = client.publish(t, item["payload"], qos=qos)
                            if result.rc != _paho.MQTT_ERR_SUCCESS:
                                raise ConnectionError(f"Buffer publish échoué rc={result.rc}")
                            buf.remove(item)
                            sent += 1
                        buffer_clear(buf_id)
                        buffers[bid] = []
                        if skipped:
                            _log.warning(f"[BUFFER:{source_id}→{bid}] {skipped} message(s) ignoré(s) (topic vide)")
                        _log.info(f"[BUFFER:{source_id}→{bid}] {sent} message(s) renvoyés")

                    # Publish temps réel
                    publish_mqtt(client, messages, qos)
                    for topic, payload in messages:
                        try:
                            import json as _json
                            d = _json.loads(payload)
                            lines = [f"[ENVOI:{source_id}→{bid}] → topic={topic}"]
                            for k, v in d.items():
                                lines.append(f"    {k}: {v}")
                            _log.info("\n".join(lines))
                        except Exception:
                            _log.info(f"[ENVOI:{source_id}→{bid}] → topic={topic} | {payload}")

                except Exception as e:
                    _log.error(f"[MQTT:{source_id}→{bid}] Erreur publish : {e}")
                    _update_mqtt_status(source_id, bid, "DISCONNECTED")

                    for topic, payload in messages:
                        if not topic or not topic.strip():
                            continue
                        buffer_add(buf_id, topic, payload, max_buffer)
                    buffers[bid] = buffer_load(buf_id)
                    total_buffered += len(buffers[bid])
                    buffer_save(buf_id, buffers[bid])
                    _log.warning(f"[BUFFER:{source_id}→{bid}] {len(buffers[bid])} en attente")

                    try:
                        client.loop_stop()
                        client.disconnect()
                    except Exception:
                        pass
                    mqtt_clients[bid]       = None
                    last_mqtt_attempts[bid] = time.time()
            else:
                for topic, payload in messages:
                    if not topic or not topic.strip():
                        continue
                    buffer_add(buf_id, topic, payload, max_buffer)
                buffers[bid] = buffer_load(buf_id)
                total_buffered += len(buffers[bid])
                if buffers[bid]:
                    buffer_save(buf_id, buffers[bid])

        # Statut global buffer
        if total_buffered > 0:
            _update_status(source_id, buffer_status="OPERATIONNEL", buffer_count=total_buffered)
        elif any_connected:
            _update_status(source_id, buffer_status="INACTIF", buffer_count=0)

        # Heartbeat
        if _running.get(source_id, False):
            _write_status_file()
        time.sleep(refresh)

    # ===== CLEAN STOP =====
    _update_status(source_id, opc="DISCONNECTED",
                   mqtt={bid: "DISCONNECTED" for bid in mqtt_configs},
                   buffer_status="INACTIF")
    try:
        if opc_client:
            opc_client.disconnect()
        for bid, client in mqtt_clients.items():
            if client:
                client.loop_stop()
                client.disconnect()
    except Exception:
        pass
    print(f"[SOURCE:{source_id}] Arrêté")


# ============================================================
#  ORCHESTRATEUR  — MULTI-BROKERS
# ============================================================
def start_all_sources(sources, brokers, options):
    """Lance un thread par source OPC UA — chaque source peut publier vers N brokers."""
    brokers_map = {b["id"]: b for b in brokers}

    for source in sources:
        source_id = source["id"]

        if _running.get(source_id) and _threads.get(source_id) and _threads[source_id].is_alive():
            _log.warning(f"[ORCHESTRATEUR] Source '{source['name']}' déjà active — ignoré")
            continue

        # V6 : broker_ids (liste) avec rétro-compatibilité broker_id (single)
        bid_list = source.get("broker_ids", [])
        if not bid_list and source.get("broker_id"):
            bid_list = [source["broker_id"]]

        broker_list = [brokers_map[bid] for bid in bid_list if bid in brokers_map]
        if not broker_list:
            _log.error(f"[ORCHESTRATEUR] Source '{source_id}' : aucun broker trouvé")
            continue

        _running[source_id] = True
        t = threading.Thread(
            target=run_source,
            args=(source, broker_list, options),
            daemon=True
        )
        _threads[source_id] = t
        t.start()
        names = ", ".join(b["name"] for b in broker_list)
        _log.info(f"[ORCHESTRATEUR] Source '{source['name']}' → brokers [{names}]")

def stop_all_sources():
    for source_id in list(_running.keys()):
        _running[source_id] = False
        if source_id in sources_status:
            sources_status[source_id]["opc"]    = "DISCONNECTED"
            sources_status[source_id]["mqtt"]   = {}
            sources_status[source_id]["buffer"] = "INACTIF"
    _write_status_file()
    _log.info("[ORCHESTRATEUR] Arrêt de toutes les sources")

def restart_source(source_config, broker_configs, options):
    source_id = source_config["id"]
    _running[source_id] = False
    time.sleep(1)
    _running[source_id] = True
    t = threading.Thread(
        target=run_source,
        args=(source_config, broker_configs, options),
        daemon=True
    )
    _threads[source_id] = t
    t.start()
    print(f"[ORCHESTRATEUR] Source '{source_config['name']}' redémarrée")

def get_sources_status():
    return dict(sources_status)

def is_any_running():
    return any(_running.values())


# ============================================================
#  MISE À JOUR STATUT  — MULTI-BROKERS
# ============================================================
def _write_status_file():
    try:
        import json
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sources_status, f)
    except Exception:
        pass

def _clear_status_file():
    try:
        import os
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)
    except Exception:
        pass

def _update_mqtt_status(source_id, broker_id, status):
    """Met à jour le statut MQTT d'un broker spécifique pour une source."""
    if source_id not in sources_status:
        sources_status[source_id] = {
            "opc": "DISCONNECTED", "mqtt": {},
            "buffer": "INACTIF", "buffer_count": 0, "last_data": None
        }
    mqtt_dict = sources_status[source_id].get("mqtt", {})
    if not isinstance(mqtt_dict, dict):
        mqtt_dict = {}
    _disconnect_since.setdefault(source_id, {"opc": None, "mqtt": {}})
    mqtt_disc = _disconnect_since[source_id].setdefault("mqtt", {})

    now = time.time()
    if status == "DISCONNECTED":
        if mqtt_disc.get(broker_id) is None:
            mqtt_disc[broker_id] = now
        if now - mqtt_disc[broker_id] >= STABILITY_DELAY:
            mqtt_dict[broker_id] = "DISCONNECTED"
    elif status == "CONNECTED":
        mqtt_disc[broker_id] = None
        mqtt_dict[broker_id] = "CONNECTED"

    sources_status[source_id]["mqtt"] = mqtt_dict

    # Statut MQTT agrégé pour l'affichage
    if any(v == "CONNECTED" for v in mqtt_dict.values()):
        sources_status[source_id]["mqtt_global"] = "CONNECTED"
    else:
        sources_status[source_id]["mqtt_global"] = "DISCONNECTED"

    _write_status_file()

def _update_status(source_id, opc=None, mqtt=None,
                   buffer_status=None, buffer_count=None, last_data=None):
    if source_id not in sources_status:
        sources_status[source_id] = {
            "opc": "DISCONNECTED", "mqtt": {},
            "mqtt_global": "DISCONNECTED",
            "buffer": "INACTIF", "buffer_count": 0, "last_data": None
        }
    _disconnect_since.setdefault(source_id, {"opc": None, "mqtt": {}})

    now = time.time()
    s   = sources_status[source_id]

    if opc == "DISCONNECTED":
        if _disconnect_since[source_id]["opc"] is None:
            _disconnect_since[source_id]["opc"] = now
        if now - _disconnect_since[source_id]["opc"] >= STABILITY_DELAY:
            s["opc"] = "DISCONNECTED"
    elif opc == "CONNECTED":
        _disconnect_since[source_id]["opc"] = None
        s["opc"] = "CONNECTED"

    if isinstance(mqtt, dict):
        s["mqtt"] = mqtt
        if any(v == "CONNECTED" for v in mqtt.values()):
            s["mqtt_global"] = "CONNECTED"
        else:
            s["mqtt_global"] = "DISCONNECTED"

    if buffer_status is not None: s["buffer"]       = buffer_status
    if buffer_count  is not None: s["buffer_count"] = buffer_count
    if last_data     is not None: s["last_data"]    = last_data
    _write_status_file()
