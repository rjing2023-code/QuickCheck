@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python labeling_app.py
pause
