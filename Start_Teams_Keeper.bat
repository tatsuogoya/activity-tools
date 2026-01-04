@echo off
:: Change directory to the folder containing this script
cd /d "%~dp0"

:: Set window title
title Teams Activity Keeper

:: Force Python to print immediately (no buffering)
set PYTHONUNBUFFERED=1

:: Run the script using the local virtual environment Python
echo Starting Teams Activity Keeper...
echo.
".venv\Scripts\python.exe" activity_keeper.py

:: If the script crashes or closes unexpectedly, pause so you can see the error
pause