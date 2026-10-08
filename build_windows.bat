@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   BUILD EdgeFusion V4  --  Windows
echo ============================================================
echo.

cd /d "%~dp0"

:: ── 1. Vérifier Python ──────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou pas dans le PATH
    pause & exit /b 1
)

:: ── 2. Installer/mettre à jour les dépendances ───────────────
echo [1/4] Installation des dépendances...
python -m pip install --upgrade pyinstaller ^
    opcua paho-mqtt pystray pillow cryptography ^
    openpyxl pywin32 >nul 2>&1
echo       OK

:: ── 3. Nettoyer les anciens builds ──────────────────────────
echo [2/4] Nettoyage...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
echo       OK

:: ── 4. Build PyInstaller ────────────────────────────────────
echo [3/4] Compilation PyInstaller (2-5 minutes)...
pyinstaller EdgeFusion_Windows.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERREUR] PyInstaller a echoue.
    pause & exit /b 1
)
echo       OK

echo.
echo ============================================================
echo   BUILD TERMINE
echo ============================================================
echo.
echo   Executable : dist\EdgeFusion\EdgeFusion.exe
echo.
echo ── Etape suivante : créer l'installeur ──────────────────────
echo   1. Ouvrir EdgeFusion_Setup.iss dans Inno Setup
echo   2. Compiler : Build ^> Compile  (Ctrl+F9)
echo.
pause
