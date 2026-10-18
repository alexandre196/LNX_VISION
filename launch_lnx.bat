@echo off
chcp 65001 > nul
title LNX VISION - Lancement
color 0B
cls

echo.
echo  ================================
echo   LNX VISION - Intelligence Platform
echo   Cybersecurite . Intelligence Artificielle
echo  ================================
echo.

cd /d "%~dp0"

echo  [1/3] Demarrage du serveur API...
start "LNX-API" /MIN venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo  Attente du serveur (10 secondes)...
timeout /t 10 /nobreak > nul

echo  [2/3] Ouverture de LNX VISION dans le navigateur...
start "" "%~dp0lnx_vision.html"

echo.
echo  ================================
echo   LNX VISION tourne sur le port 8000
echo  ================================
echo.
echo  Appuie sur une touche pour arreter...
pause > nul

taskkill /F /IM python.exe > nul 2>&1
echo  LNX VISION arrete.
timeout /t 2 /nobreak > nul
