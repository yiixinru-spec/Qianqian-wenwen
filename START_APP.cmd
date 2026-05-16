@echo off
title Qianqian Local Starter
cd /d "%~dp0"

echo.
echo ================================
echo   Qianqian Local Starter
echo ================================
echo.
echo Current directory:
cd
echo.
echo Checking Python...
where python
python --version
echo.
echo After the server starts, open:
echo http://127.0.0.1:8000/
echo.
echo Keep this window open while using the app.
echo.
pause

python -u server.py

echo.
echo Server stopped. If there is an error above, send it to the assistant.
pause
