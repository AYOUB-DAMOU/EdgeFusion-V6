#!/bin/bash
# =============================================================
#  BUILD EdgeFusion V4  --  Linux
#  Testé sur Ubuntu 22.04 / Debian 12 / Raspberry Pi OS
# =============================================================

set -e
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  BUILD EdgeFusion V4  --  Linux"
echo "============================================================"
echo ""

# ── 1. Dépendances système ────────────────────────────────────
echo "[1/4] Installation des dépendances système..."
sudo apt-get install -y \
    python3-tk \
    python3-pip \
    libgtk-3-0 \
    libappindicator3-1 \
    gir1.2-appindicator3-0.1 \
    > /dev/null 2>&1
echo "      OK"

# ── 2. Dépendances Python ─────────────────────────────────────
echo "[2/4] Installation des dépendances Python..."
pip3 install --upgrade \
    pyinstaller \
    opcua \
    paho-mqtt \
    pystray \
    pillow \
    cryptography \
    openpyxl \
    > /dev/null 2>&1
echo "      OK"

# ── 3. Nettoyage ──────────────────────────────────────────────
echo "[3/4] Nettoyage..."
rm -rf build dist
echo "      OK"

# ── 4. Build PyInstaller ──────────────────────────────────────
echo "[4/4] Compilation PyInstaller (2-5 minutes)..."
pyinstaller EdgeFusion_Linux.spec --noconfirm
echo "      OK"

echo ""
echo "============================================================"
echo "  BUILD TERMINE"
echo "============================================================"
echo ""
echo "  Executable : dist/EdgeFusion/edgefusion"
echo ""
echo "  Etape suivante : lancer install_linux.sh (sudo)"
echo "    sudo bash install_linux.sh"
echo ""
