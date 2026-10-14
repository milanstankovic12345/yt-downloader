@echo off
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv || goto :err
    .venv\Scripts\python -m pip install -r requirements.txt || goto :err
)
.venv\Scripts\python main.py
exit /b 0
:err
echo Setup failed.
pause
