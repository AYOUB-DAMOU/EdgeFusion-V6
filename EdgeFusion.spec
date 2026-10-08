# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — EdgeFusion V4

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collecter pandas + numpy complètement (binaires + données + modules)
pandas_datas,    pandas_bins,    pandas_hiddens    = collect_all('pandas')
numpy_datas,     numpy_bins,     numpy_hiddens     = collect_all('numpy')
openpyxl_datas,  openpyxl_bins,  openpyxl_hiddens  = collect_all('openpyxl')

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[] + pandas_bins + numpy_bins + openpyxl_bins,
    datas=[
        ('appicon.ico', '.'),
    ] + pandas_datas + numpy_datas + openpyxl_datas,
    hiddenimports=[
        # OPC UA (freeopcua)
        'opcua', 'opcua.ua', 'opcua.ua.uatypes', 'opcua.ua.object_ids',
        'opcua.client', 'opcua.client.client',
        'opcua.common', 'opcua.common.node', 'opcua.common.manage_nodes',
        'opcua.crypto', 'opcua.crypto.security_policies',
        'opcua.crypto.uacrypto',
        # MQTT (paho)
        'paho', 'paho.mqtt', 'paho.mqtt.client', 'paho.mqtt.publish',
        # System tray
        'pystray', 'pystray._win32',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        # Cryptographie (certificats OPC UA)
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
        # Windows Service (pywin32)
        'win32service', 'win32serviceutil', 'win32event',
        'win32con', 'win32api', 'servicemanager',
        # Tkinter (GUI)
        'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk',
        # Journal
        'journal',
        # Stdlib
        'json', 'threading', 'datetime', 'uuid', 'logging', 'collections',
    ] + pandas_hiddens + numpy_hiddens + openpyxl_hiddens,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy',
        'PyQt5', 'PyQt6', 'wx', 'gi',
        'IPython', 'notebook', 'jupyter',
        'test', 'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EdgeFusion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='appicon.ico',
    uac_admin=True,
    version_file=None,
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
