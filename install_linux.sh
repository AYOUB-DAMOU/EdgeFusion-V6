#!/bin/bash
# =============================================================
#  INSTALL EdgeFusion V4  --  Linux
#  Doit être exécuté avec sudo
#  Usage : sudo bash install_linux.sh
# =============================================================

set -e

INSTALL_DIR="/opt/edgefusion"
DATA_DIR="/var/lib/edgefusion"
UNIT_FILE="/etc/systemd/system/edgefusion.service"
DESKTOP_FILE="/usr/share/applications/edgefusion.desktop"
SRC_DIR="$(dirname "$0")/dist/EdgeFusion"

# ── Vérifier les droits ───────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "[ERREUR] Ce script doit être exécuté avec sudo"
    echo "  Usage : sudo bash install_linux.sh"
    exit 1
fi

# ── Vérifier que le build existe ─────────────────────────────
if [ ! -f "$SRC_DIR/edgefusion" ]; then
    echo "[ERREUR] Exécutable non trouvé : $SRC_DIR/edgefusion"
    echo "  Lancez d'abord : bash build_linux.sh"
    exit 1
fi

echo ""
echo "============================================================"
echo "  INSTALLATION EdgeFusion V4  --  Linux"
echo "============================================================"
echo ""

# ── 1. Copier les fichiers ────────────────────────────────────
echo "[1/5] Installation dans $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
cp -r "$SRC_DIR" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/edgefusion"
echo "      OK"

# ── 2. Créer les dossiers de données ─────────────────────────
echo "[2/5] Création des dossiers de données..."
mkdir -p "$DATA_DIR/logs"
# Copier config.json initial s'il n'existe pas encore
if [ ! -f "$DATA_DIR/config.json" ]; then
    if [ -f "$(dirname "$0")/config.json" ]; then
        cp "$(dirname "$0")/config.json" "$DATA_DIR/config.json"
    fi
fi
chmod -R 777 "$DATA_DIR"
echo "      OK"

# ── 3. Créer l'unité systemd ──────────────────────────────────
echo "[3/5] Installation du service systemd..."
cat > "$UNIT_FILE" << EOF
[Unit]
Description=EdgeFusion OPC UA to MQTT Bridge
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$INSTALL_DIR/edgefusion --background
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable edgefusion
echo "      OK"

# ── 4. Raccourci bureau (optionnel) ───────────────────────────
echo "[4/5] Création du raccourci bureau..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=EdgeFusion
Comment=OPC UA to MQTT Bridge
Exec=$INSTALL_DIR/edgefusion
Icon=$INSTALL_DIR/appicon.ico
Terminal=false
Type=Application
Categories=Utility;
EOF
echo "      OK"

# ── 5. Démarrer le service ────────────────────────────────────
echo "[5/5] Démarrage du service..."
systemctl start edgefusion
sleep 2
STATUS=$(systemctl is-active edgefusion 2>/dev/null || echo "unknown")
echo "      Statut : $STATUS"

echo ""
echo "============================================================"
echo "  INSTALLATION TERMINEE"
echo "============================================================"
echo ""
echo "  Exécutable    : $INSTALL_DIR/edgefusion"
echo "  Données       : $DATA_DIR/"
echo "  Journal CSV   : $DATA_DIR/logs/journal.csv"
echo "  Logs systemd  : journalctl -u edgefusion -f"
echo ""
echo "  Commandes utiles :"
echo "    systemctl status edgefusion"
echo "    systemctl stop   edgefusion"
echo "    systemctl start  edgefusion"
echo ""
