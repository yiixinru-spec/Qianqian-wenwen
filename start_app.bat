@echo off
cd /d "%~dp0"
start "Qianqian Server" cmd /k call "%~dp0run_server.bat"
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8000/"
