@echo off
cd /d "%~dp0"
echo Starting Job Hunt Agent...
echo Open your browser at http://localhost:8501 or http://localhost:8502
echo Press Ctrl+C to stop.
"%~dp0venv\Scripts\streamlit.exe" run app.py
pause