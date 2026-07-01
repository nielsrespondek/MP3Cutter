@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
    goto :check
)

where py >nul 2>nul
if %errorlevel%==0 (
    py app.py
    goto :check
)

echo Python wurde nicht gefunden. Bitte Python von https://python.org installieren
echo und beim Setup "Add python.exe to PATH" ankreuzen.
pause
exit /b 1

:check
if %errorlevel% neq 0 (
    echo.
    echo Es ist ein Fehler aufgetreten. Fenster bleibt offen, um die Meldung zu lesen.
    pause
)
