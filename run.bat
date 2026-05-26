@echo off
cd /d "c:\Users\USER\openwave"
if exist .venv\Scripts\python.exe (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

:loop
%PYTHON_EXE% bot.py
echo Bot dayandi, 3 saniye sonra yeniden bashlayir...
timeout /t 3
goto loop