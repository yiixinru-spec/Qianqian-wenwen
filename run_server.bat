@echo off
title Qianqian Server
set PYTHONUTF8=1
cd /d "%~dp0"
python -u server.py
pause
