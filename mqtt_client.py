import paho.mqtt.client as mqtt
import ssl
import json
import os
from datetime import datetime


def connect_mqtt(broker_config, on_connect_cb=None, on_disconnect_cb=None):
    """
    Connexion à un broker MQTT ou MQTTS (TLS).
    - broker_config : dict {host, port, username, password, client_id, qos,
                            tls, ca_cert, client_cert, client_key, tls_insecure}
    - on_connect_cb    : callback(rc) appelé à la connexion
    - on_disconnect_cb : callback(rc) appelé à la déconnexion
    Retourne mqtt_client ou lève une exception.
    """
    client = mqtt.Client(client_id=broker_config["client_id"])

    def _on_connect(c, userdata, flags, rc):
        if on_connect_cb:
            on_connect_cb(rc)

    def _on_disconnect(c, userdata, rc):
        if on_disconnect_cb:
            on_disconnect_cb(rc)

    client.on_connect    = _on_connect
    client.on_disconnect = _on_disconnect

    if broker_config.get("username"):
        client.username_pw_set(
            broker_config["username"],
            broker_config["password"]
        )

    # ── TLS / MQTTS ──
    if broker_config.get("tls"):
        ca_certs     = broker_config.get("ca_cert", "")    or None
        certfile     = broker_config.get("client_cert", "") or None
        keyfile      = broker_config.get("client_key", "")  or None
        tls_insecure = broker_config.get("tls_insecure", False)

        if ca_certs and not os.path.isfile(ca_certs):
            ca_certs = None
        if certfile and not os.path.isfile(certfile):
            certfile = None
            keyfile = None
        if keyfile and not os.path.isfile(keyfile):
            certfile = None
            keyfile = None

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if ca_certs:
            ctx.load_verify_locations(ca_certs)
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if certfile and keyfile:
            ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        if tls_insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        client.tls_set_context(ctx)

    client.connect(broker_config["host"], int(broker_config["port"]), keepalive=60)
    client.loop_start()
    return client


def build_payloads(data, tag_topics, tag_mapping, meta, general_topic):
    """
    Construit les payloads MQTT à publier.

    - data          : dict {mqtt_key: valeur}
    - tag_topics    : dict {node_id: sous_topic}
    - tag_mapping   : dict {node_id: mqtt_key}
    - meta          : dict {opc_statut, timestamp, serial}
    - general_topic : topic principal

    Retourne liste de (topic, payload_json).
    """
    messages = []

    # Payload général (toutes les données)
    general_payload = json.dumps({**data, **meta} if data else meta)
    messages.append((general_topic, general_payload))

    # Payloads sous-topics : regrouper les tags qui partagent le même sous-topic
    if data and tag_topics:
        grouped = {}  # {sous_topic: {mqtt_key: valeur}}
        for tag, specific_topic in tag_topics.items():
            mqtt_key  = tag_mapping.get(tag, f"s={tag.split('=')[-1]}")
            tag_value = data.get(mqtt_key, -255)
            grouped.setdefault(specific_topic, {})[mqtt_key] = tag_value
        for specific_topic, tag_data in grouped.items():
            specific_payload = json.dumps({**tag_data, **meta})
            messages.append((specific_topic, specific_payload))

    return messages


def publish_mqtt(mqtt_client, messages, qos):
    """
    Publie une liste de (topic, payload) sur le broker.
    Lève ConnectionError si une publication échoue.
    """
    for topic, payload in messages:
        if not topic or not topic.strip():
            raise ValueError(f"Topic MQTT vide — vérifiez la configuration de la source")
        result = mqtt_client.publish(topic, payload, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(
                f"MQTT publish échoué sur '{topic}', rc={result.rc}"
            )


def build_meta(opc_ok, serial):
    """Construit le dictionnaire de métadonnées."""
    return {
        "opc_statut": "CONNECTER" if opc_ok else "DECONNECTER",
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "serial":     serial
    }
