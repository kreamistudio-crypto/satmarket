@echo off
title SatMarket - Server
cd /d "%~dp0"
echo ============================================
echo   SatMarket - avvio del server...
echo   Per fermarlo: CTRL+C (o chiudi la finestra)
echo ============================================
echo.
python -m uvicorn server:app --host 0.0.0.0 --port 8080
echo.
echo Il server si e' fermato.
pause
