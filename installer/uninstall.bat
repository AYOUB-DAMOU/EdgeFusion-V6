@echo off
chcp 65001 >nul
title Desinstallation EdgeFusion v2.0

net session >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Ce script doit etre execute en tant qu'Administrateur.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   EdgeFusion v2.0 — Desinstallation
echo ============================================================
echo.

set INSTALL_DIR=C:\Program Files\EdgeFusion
set DATA_DIR=C:\ProgramData\EdgeFusion

echo [1/4] Arret du service...
"%INSTALL_DIR%\EdgeFusion.exe" stop >nul 2>&1
timeout /t 2 /nobreak >nul
echo       OK

echo [2/4] Suppression du service...
"%INSTALL_DIR%\EdgeFusion.exe" remove >nul 2>&1
echo       OK

echo [3/4] Suppression des fichiers d'installation...
rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
del /F /Q "%PUBLIC%\Desktop\EdgeFusion.lnk" >nul 2>&1
echo       OK

echo [4/4] Nettoyage des donnees temporaires...
del /F /Q "%DATA_DIR%\buffer_*.json" >nul 2>&1
del /F /Q "%DATA_DIR%\status.json"   >nul 2>&1
echo       OK (config.json conserve)

echo.
echo ============================================================
echo   Desinstallation terminee.
echo   Note : config.json conserve dans %DATA_DIR%
echo ============================================================
echo.
pause
