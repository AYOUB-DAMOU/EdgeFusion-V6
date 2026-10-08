# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — EdgeFusion V4  ▸  Linux

from PyInstaller.utils.hooks import collect_all

block_cipher = None

pandas_datas,   pandas_bins,   pandas_hiddens   = collect_all('pandas')
numpy_datas,    numpy_bins,    numpy_hiddens    = collect_all('numpy')
openpyxl_datas, openpyxl_bins, openpyxl_hiddens = collect_all('openpyxl')

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[] + pandas_bins + numpy_bins + openpyxl_bins,
    datas=[
        ('appicon.ico', '.'),
    ] + pandas_datas + numpy_datas + openpyxl_datas,
    hiddenimports=[
        # OPC UA
        'opcua', 'opcua.ua', 'opcua.ua.uatypes', 'opcua.ua.object_ids',
        'opcua.client', 'opcua.client.client',
        'opcua.common', 'opcua.common.node', 'opcua.common.manage_nodes',
        'opcua.crypto', 'opcua.crypto.security_policies',
        'opcua.crypto.uacrypto',
        # MQTT
        'paho', 'paho.mqtt', 'paho.mqtt.client', 'paho.mqtt.publish',
        # System tray (Linux : AppIndicator ou gtk)
        'pystray', 'pystray._appindicator', 'pystray._gtk',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        # Cryptographie
        'cryptography',
        'cryptography.x509', 'cryptography.x509.oid',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.serialization',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'cryptography.hazmat.primitives.asymmetric.padding',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        # Tkinter
        'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk',
        # Journal
        'journal',
        # Stdlib
        'json', 'threading', 'datetime', 'uuid', 'logging', 'collections', 'csv',
    ] + pandas_hiddens + numpy_hiddens + openpyxl_hiddens,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy',
        'PyQt5', 'PyQt6', 'wx',
        'IPython', 'notebook', 'jupyter',
        'test', 'unittest',
        # Windows-only — exclure explicitement
        'win32api', 'win32service', 'win32serviceutil',
        'win32event', 'win32con', 'servicemanager',
        'pystray._win32',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='edgefusion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,       # False = pas de terminal (GUI mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Pas d'icon .ico sur Linux — utiliser .png si nécessaire
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='EdgeFusion',
)
