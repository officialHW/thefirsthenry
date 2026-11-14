@echo off
rem Double-click this file (Windows) to start Henry.
cd /d "%~dp0"
set "HERMES_HOME=%~dp0hermes"
set "PY=python"
for /d %%D in ("%HERMES_HOME%\tools\python-*") do if exist "%%D\python.exe" set "PY=%%D\python.exe"
"%PY%" -I app\launch.py
pause
