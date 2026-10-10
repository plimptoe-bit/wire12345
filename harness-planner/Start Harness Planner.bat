@echo off
rem Double-click me (Windows). Starts the Harness Planner XP interface in
rem your browser. Needs Python 3.11+ from python.org ("Add to PATH" ticked).
cd /d "%~dp0"
where py >nul 2>nul && (py -3 -m harness_planner gui & goto end)
where python >nul 2>nul && (python -m harness_planner gui & goto end)
echo Python was not found. Install it from https://www.python.org/downloads/
echo and tick "Add Python to PATH" during setup, then double-click me again.
pause
:end
