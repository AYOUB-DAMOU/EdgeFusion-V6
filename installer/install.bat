@echo off
chcp 65001 >nul
title Installation EdgeFusion v2.0

:: Vérifier droits administrateur
net session >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Ce script doit etre execute en tant qu'Administrateur.
    echo Clic droit sur install.bat ^> "Executer en tant qu'administrateur"
    pause & exit /b 1
)

echo.
echo ============================================================
echo   EdgeFusion v2.0 — Installation
echo   ManaTechnology
echo ============================================================
echo.

set INSTALL_DIR=C:\Program Files\EdgeFusion
set DATA_DIR=C:\ProgramData\EdgeFusion

:: ── 1. Copier les fichiers ────────────────────────────────────
echo [1/5] Copie des fichiers vers %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
xcopy /E /Y /Q "%~dp0EdgeFusion\*" "%INSTALL_DIR%\" >nul
echo       OK

:: ── 2. Créer dossier données ──────────────────────────────────
echo [2/5] Creation du dossier de donnees...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\logs" mkdir "%DATA_DIR%\logs"
icacls "%DATA_DIR%" /grant Everyone:(OI)(CI)F /T >nul 2>&1
echo       OK

:: ── 3. Installer le service Windows ──────────────────────────
echo [3/5] Installation du service Windows...
"%INSTALL_DIR%\EdgeFusion.exe" install
if errorlevel 1 (
    echo [ERREUR] Installation service echouee.
    pause & exit /b 1
)
echo       OK

:: ── 4. Configurer demarrage automatique + recovery ────────────
echo [4/5] Configuration demarrage automatique...
sc config EdgeFusionService start= auto >nul
sc failure EdgeFusionService reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul
echo       OK

:: ── 5. Démarrer le service ────────────────────────────────────
echo [5/5] Demarrage du service...
"%INSTALL_DIR%\EdgeFusion.exe" start
echo       OK

:: ── Raccourci Bureau ──────────────────────────────────────────
echo.
echo Creation du raccourci Bureau...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%PUBLIC%\Desktop\EdgeFusion.lnk');$s.TargetPath='%INSTALL_DIR%\EdgeFusion.exe';$s.IconLocation='%INSTALL_DIR%\appicon.ico';$s.Save()"

echo.
echo ============================================================
echo   Installation terminee !
echo.
echo   Service  : EdgeFusionService (demarrage automatique)
echo   Logs     : %DATA_DIR%\logs\edgefusion.log
echo   Config   : %DATA_DIR%\config.json
echo   GUI      : double-clic sur le raccourci Bureau
echo ============================================================
echo.
pause
