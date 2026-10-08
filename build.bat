@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   BUILD EdgeFusion V4  —  Standalone Installer
echo ============================================================
echo.

cd /d "%~dp0"

:: ── 1. Vérifier Python ──────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou pas dans le PATH
    pause & exit /b 1
)

:: ── 2. Installer/mettre à jour PyInstaller ──────────────────
echo [1/4] Installation PyInstaller...
python -m pip install --upgrade pyinstaller >nul 2>&1
echo       OK

:: ── 3. Vérifier les dépendances ─────────────────────────────
echo [2/4] Vérification des dépendances...
python -m pip install --upgrade ^
    opcua paho-mqtt pystray pillow cryptography ^
    openpyxl pywin32 >nul 2>&1
echo       OK

:: ── 4. Nettoyer les anciens builds ──────────────────────────
echo [3/4] Nettoyage...
if exist "build"       rmdir /s /q "build"
if exist "dist"        rmdir /s /q "dist"
if exist "..\installer" mkdir "..\installer" >nul 2>&1
echo       OK

:: ── 5. Build PyInstaller ────────────────────────────────────
echo [4/4] Compilation PyInstaller (peut prendre 2-5 minutes)...
pyinstaller EdgeFusion.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERREUR] PyInstaller a echoue. Voir les erreurs ci-dessus.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   BUILD TERMINE
echo ============================================================
echo.
echo   Executable : dist\EdgeFusion\EdgeFusion.exe
echo.
echo ── Etape suivante : créer l'installeur ──────────────────────
echo.
echo   Option A - Inno Setup (recommandé) :
echo     1. Télécharger : https://jrsoftware.org/isdl.php
echo     2. Ouvrir : EdgeFusion_Setup.iss
echo     3. Compiler : Build ^> Compile  (ou Ctrl+F9)
echo     4. Résultat : ..\installer\EdgeFusion_Setup_v2.0.exe
echo.
echo   Option B - Test direct :
echo     dist\EdgeFusion\EdgeFusion.exe
echo.
pause
