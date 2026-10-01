from opcua import Client, ua
from certificate import CERT_FILE, KEY_FILE, check_certificate
import os


def connect_opc(opc_url, opc_user="", opc_pass=""):
    """
    Connexion OPC UA avec adaptation automatique du mode :
    - Certificat    : si client_cert.pem + client_key.pem existent
    - Login/Password: si username rempli
    - Anonyme       : si rien de tout ça
    Retourne opc_client connecté ou lève une exception.
    """
    client = Client(opc_url)

    if check_certificate():
        try:
            from opcua.crypto import security_policies
            client.set_security(
                security_policies.SecurityPolicyBasic256Sha256,
                certificate_path=CERT_FILE,
                private_key_path=KEY_FILE,
                mode=ua.MessageSecurityMode.SignAndEncrypt
            )
        except Exception as e:
            print(f"[OPC] Erreur chargement certificat : {e}")

    if opc_user:
        client.set_user(opc_user)
        client.set_password(opc_pass)

    client.connect()
    return client


def read_opc_tags(opc_client, tags, tag_mapping):
    """
    Lit tous les tags OPC UA depuis le serveur.

    Retourne :
    - data         : {mqtt_key: valeur}   — 0 si erreur tag
    - quality_info : {mqtt_key: {"ok": bool, "reason": str}}
    """
    data         = {}
    quality_info = {}

    nodes = {tag: opc_client.get_node(tag) for tag in tags}

    for tag, node in nodes.items():
        tag_name = tag.split("=")[-1]
        mqtt_key = tag_mapping.get(tag, f"s={tag_name}")
        try:
            dv     = node.get_data_value()
            value  = dv.Value.Value
            status = dv.StatusCode.name

            if isinstance(value, bool):
                value = "True" if value else "False"

            if status != "Good":
                data[mqtt_key]         = 0
                quality_info[mqtt_key] = {"ok": False, "reason": f"Qualité OPC: {status}", "node_id": tag}
            else:
                val = value if value is not None else 0
                data[mqtt_key]         = val
                quality_info[mqtt_key] = {"ok": True, "reason": "", "node_id": tag}

        except ua.UaStatusCodeError as e:
            err_str = str(e)
            if any(x in err_str for x in ("BadSession", "BadConnection",
                                           "BadSecure", "BadCommunication",
                                           "BadServerNotConnected")):
                raise
            data[mqtt_key]         = 0
            quality_info[mqtt_key] = {"ok": False, "reason": f"Tag erreur: {err_str}", "node_id": tag}
        except (ConnectionError, OSError, TimeoutError):
            raise
        except Exception as e:
            data[mqtt_key]         = 0
            quality_info[mqtt_key] = {"ok": False, "reason": f"Erreur: {type(e).__name__}", "node_id": tag}

    return data, quality_info
