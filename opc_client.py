from opcua import Client, ua
from certificate import CERT_FILE, KEY_FILE, check_certificate
from urllib.parse import urlparse
import os


def _prepare_client(opc_url, opc_user="", opc_pass=""):
    """Crée un client OPC UA avec timeout et endpoint fix."""
    client = Client(opc_url, timeout=15)
    client.session_timeout = 30000
    if opc_user:
        client.set_user(opc_user)
        client.set_password(opc_pass)
    return client


def _force_endpoint_url(client, opc_url):
    """
    Force le client à utiliser l'URL d'origine après get_endpoints().
    Corrige le problème où le serveur retourne un hostname interne
    non résolvable (ex: opc.tcp://WIN-SERVERNAME:4863 au lieu de l'IP).
    """
    try:
        parsed = urlparse(opc_url)
        original_host = parsed.hostname
        original_port = parsed.port

        endpoints = client.connect_and_get_server_endpoints()
        for ep in endpoints:
            ep_parsed = urlparse(ep.EndpointUrl)
            if ep_parsed.hostname != original_host:
                ep.EndpointUrl = opc_url
        client.disconnect()
    except Exception:
        pass


def connect_opc(opc_url, opc_user="", opc_pass=""):
    """
    Connexion OPC UA avec fallback automatique :
    1. Tente avec certificat SignAndEncrypt (si cert existe)
    2. Si échec → retente sans sécurité (mode None)
    3. Login/Password appliqué si username rempli
    4. Force l'URL d'origine pour éviter les problèmes de hostname
    Retourne opc_client connecté ou lève une exception.
    """
    client = _prepare_client(opc_url, opc_user, opc_pass)
    has_cert = check_certificate()
    security_applied = False

    if has_cert:
        try:
            from opcua.crypto import security_policies
            client.set_security(
                security_policies.SecurityPolicyBasic256Sha256,
                certificate_path=CERT_FILE,
                private_key_path=KEY_FILE,
                mode=ua.MessageSecurityMode.SignAndEncrypt
            )
            security_applied = True
        except Exception as e:
            print(f"[OPC] Erreur chargement certificat : {e}")

    try:
        client.connect()
        return client
    except Exception as e:
        print(f"[OPC] Connexion échouée ({e}), tentative sans sécurité...")
        try:
            client.disconnect()
        except Exception:
            pass
        client = _prepare_client(opc_url, opc_user, opc_pass)
        try:
            client.connect()
            return client
        except Exception:
            pass

        # Dernière tentative : forcer l'URL d'origine (fix hostname)
        print(f"[OPC] Tentative avec endpoint URL forcé...")
        client = _prepare_client(opc_url, opc_user, opc_pass)
        client.server_url = urlparse(opc_url)
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
