#!/bin/bash
# =============================================================
#  DÉSINSTALLATION EdgeFusion V4  --  Linux
#  Usage : sudo bash uninstall_linux.sh
# =============================================================

if [ "$EUID" -ne 0 ]; then
    echo "[ERREUR] Ce script doit être exécuté avec sudo"
    exit 1
fi

echo ""
echo "============================================================"
echo "  DÉSINSTALLATION EdgeFusion V4"
echo "============================================================"
echo ""

# Arrêter et désactiver le service
systemctl stop    edgefusion 2>/dev/null || true
systemctl disable edgefusion 2>/dev/null || true

# Supprimer les fichiers
rm -f  /etc/systemd/system/edgefusion.service
rm -f  /usr/share/applications/edgefusion.desktop
rm -rf /opt/edgefusion

systemctl daemon-reload

echo "  Service et fichiers supprimés."
echo "  Les données ($DATA_DIR) sont conservées."
echo "  Pour les supprimer : sudo rm -rf /var/lib/edgefusion"
echo ""
