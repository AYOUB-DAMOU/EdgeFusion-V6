# EdgeFusion V6

**Pont OPC UA → MQTT / MQTTS | Multi-Sources Multi-Brokers Gateway**

Développé par **ManaTechnology** — Casablanca, Maroc

---

## Description

EdgeFusion V6 est la dernière version de l'application de pont (bridge) industrielle qui lit les données en temps réel depuis des serveurs OPC UA et les publie vers **plusieurs brokers MQTT/MQTTS simultanément**.

### Nouveautés V6 par rapport à V5
- **Multi-Brokers par source** : chaque source OPC UA peut publier vers 1, 2 ou N brokers MQTT/MQTTS en même temps
- **Reconnexion indépendante** : si un broker tombe, les autres continuent normalement — pas d'interruption
- **Buffer par broker** : chaque broker a son propre buffer Store & Forward indépendant
- **Sélection par checkboxes** : l'interface permet de cocher plusieurs brokers pour une même source
- **Rétro-compatibilité** : les configurations V5 (`broker_id` unique) sont automatiquement prises en charge

### Fonctionnalités héritées de V5
- **MQTT et MQTTS** : support TLS/SSL (port 8883), mTLS, option TLS insecure
- **Port automatique** : basculement 1883 ↔ 8883 lors de l'activation MQTTS
- **Correction TLS** : `ssl.SSLContext` + `client.tls_set_context()`

## Fonctionnalités

- **Multi-sources** : connexion simultanée à plusieurs serveurs OPC UA
- **Multi-brokers** : chaque source publie vers N brokers MQTT/MQTTS indépendants
- **MQTT et MQTTS** : support des connexions chiffrées TLS/SSL (port 8883)
- **Store & Forward** : buffer local par broker en cas de déconnexion
- **Reconnexion indépendante** : chaque broker se reconnecte individuellement
- **Journal des données** : suivi en temps réel des changements de valeurs
- **Démarrage automatique** : lancement au démarrage de Windows
- **Fichier Excel de tags** : configuration flexible des tags OPC UA
- **Opérations mathématiques** : calculs sur les valeurs (somme, multiplication, etc.)
- **Authentification** : protection par login/mot de passe pour les actions critiques
- **Certificat OPC UA** : génération automatique du certificat client

## Architecture

```
main.py              → Point d'entrée de l'application
gui.py               → Interface graphique (Tkinter) — multi-brokers UI
config.py            → Gestion de la configuration (JSON)
opc_client.py        → Client OPC UA (opcua)
mqtt_client.py       → Client MQTT/MQTTS (paho-mqtt + ssl)
excel_reader.py      → Lecture du fichier Excel de tags
operations.py        → Opérations mathématiques sur les tags
process.py           → Orchestration multi-sources multi-brokers (threads)
buffer.py            → Store & Forward (buffer JSON local, un par broker)
journal.py           → Journal des données (CSV)
certificate.py       → Génération du certificat OPC UA
logger.py            → Logging applicatif
launcher.py          → Lanceur Windows (Planificateur de tâches)
service.py           → Service Windows (optionnel)
tray.py              → Icône système (System Tray)
_paths.py            → Chemins des fichiers de données
```

## Installation

### Depuis l'installeur (recommandé)
1. Exécuter `EdgeFusion_Setup.exe` ou `install.bat` en tant qu'administrateur
2. L'application s'installe dans `C:\Program Files\EdgeFusion`
3. Les données sont stockées dans `C:\ProgramData\EdgeFusion`

### Depuis les sources
```bash
pip install opcua paho-mqtt openpyxl
python main.py
```

## Configuration

### Brokers MQTT
- **MQTT** : port 1883 (non chiffré, réseau interne)
- **MQTTS** : port 8883 (chiffré TLS/SSL, réseau public)
- Certificats : CA cert (obligatoire), Client cert + Key (optionnel, mTLS)

### Source OPC UA — Multi-Brokers
Chaque source nécessite :
- Adresse IP et port du serveur OPC UA
- Topic MQTT, Client ID, credentials MQTT
- Fichier Excel de tags (.xlsx)
- **Sélection d'un ou plusieurs brokers** (checkboxes)

### Structure config.json (V6)
```json
{
  "sources": [
    {
      "id": "abc123",
      "name": "Usine",
      "opc_url": "opc.tcp://192.168.1.100:4840",
      "broker_ids": ["broker1", "broker2"],
      "excel_path": "tags_usine.xlsx",
      "topic": "usine/data"
    }
  ],
  "brokers": [
    {"id": "broker1", "name": "Local", "host": "192.168.1.10", "port": "1883"},
    {"id": "broker2", "name": "Cloud", "host": "cloud.example.com", "port": "8883", "tls": true}
  ]
}
```

### Fichier Excel de Tags
| Colonne | Obligatoire | Description |
|---------|------------|-------------|
| Tag | Oui | Node ID OPC UA (ex: `ns=2;s=Temperature`) |
| Mapping | Non | Clé MQTT personnalisée |
| Topic | Non | Sous-topic MQTT spécifique |
| Operation | Non | Opération mathématique (+, -, ×, ÷) |
| Value | Non | Valeur ou Node ID pour l'opération |

## Multi-Brokers : comment ça marche

```
                    ┌──── Broker A (MQTT local)
Source OPC UA ──────┤
                    └──── Broker B (MQTTS cloud)
```

- Une seule connexion OPC UA par source (pas de duplication)
- Les données sont lues une fois, puis publiées vers tous les brokers sélectionnés
- Si Broker A tombe, Broker B continue sans interruption
- Chaque broker a son propre buffer : `buffer_sourceId_brokerId.json`
- La reconnexion de chaque broker est indépendante

## Répertoires de données

| Répertoire | Contenu |
|-----------|---------|
| `C:\ProgramData\EdgeFusion\config.json` | Configuration |
| `C:\ProgramData\EdgeFusion\buffer_*_*.json` | Buffer Store & Forward (par source × broker) |
| `C:\ProgramData\EdgeFusion\logs\` | Journal et logs |
| `C:\ProgramData\EdgeFusion\cert\` | Certificat OPC UA |

## Dépendances

- Python 3.10+
- opcua (python-opcua)
- paho-mqtt
- openpyxl
- tkinter (inclus avec Python)

## Licence

© 2026 ManaTechnology. Tous droits réservés.
