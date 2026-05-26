@echo off
cd /d "c:\Users\USER\openwave"
if exist .venv\Scripts\python.exe (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

start "OpenWave Telegram Bot" %PYTHON_EXE% bot.py
start "OpenWave Citizen App" %PYTHON_EXE% app_citizen.py
start "OpenWave Admin App" %PYTHON_EXE% app_admin.py

echo All services started successfully.
