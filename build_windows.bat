@echo off
cd /d "%~dp0"
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name StellarisGuide --icon "static\assets\stellaris-guide.ico" --add-data "static;static" --add-data "stellaris_guide\playbooks.json;stellaris_guide" --distpath "dist\release-1.6.4" --workpath "build\StellarisGuide-1.6.4" app.py
if errorlevel 1 exit /b 1
py -3 scripts\package_windows_release.py
if errorlevel 1 exit /b 1
echo Portable app ready: dist\StellarisGuide-Windows-1.6.4.zip

