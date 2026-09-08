@echo off
cd /d "%~dp0"
echo.
echo === Deep Bridge ===
echo Fermez toute ancienne fenetre Deep Bridge avant de continuer.
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Creation du venv + install...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  ".venv\Scripts\python.exe" scripts\generate_demo_data.py
)
echo Lancement...
".venv\Scripts\python.exe" -m app.main
echo.
if errorlevel 1 (
  echo ERREUR au lancement. Relancez et notez le message ci-dessus.
)
pause
