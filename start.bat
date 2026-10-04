@echo off
cd /d "%~dp0"
set PY=
py -3 --version >nul 2>&1 && set PY=py -3
if not defined PY (python --version >nul 2>&1 && set PY=python)
if not defined PY (
  echo ERROR: Python 3 not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" in the installer.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo First start: installing - needs internet, takes a minute...
  %PY% -m venv .venv
  if errorlevel 1 goto fail
  .venv\Scripts\python -m pip install -q -r requirements.txt
  if errorlevel 1 goto fail
)
start "" http://localhost:5050
echo Inventory Tracker running at http://localhost:5050 - close this window to stop
.venv\Scripts\python app.py
echo.
echo The app stopped. If it says the address is in use, it is already running: open http://localhost:5050
pause
exit /b 0
:fail
echo.
echo ERROR: install failed. Check your internet connection, then delete the .venv folder and try again.
rmdir /s /q .venv 2>nul
pause
exit /b 1
