@echo off
cd /d "%~dp0"

echo Installiere Abhaengigkeiten...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Baue HookCutter.exe...
pyinstaller hookcutter.spec

echo.
if exist "dist\HookCutter.exe" (
    echo Fertig! Die exe liegt in dist\HookCutter.exe
) else (
    echo Es ist ein Fehler aufgetreten - siehe Meldungen oben.
)
pause
