@echo off
echo ============================================================
echo CSG Sprint Reporter - Installation
echo ============================================================
echo.
echo Installing required packages...
echo This may take 1-2 minutes.
echo.

cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements-sprint-reporter.txt

echo.
echo ============================================================
echo INSTALLATION COMPLETE!
echo ============================================================
echo.
echo Next step: Run SETUP.bat to configure your credentials
echo.
pause
