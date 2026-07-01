@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python isn't installed on this computer yet. Here's how to get it:
    echo.
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Click the yellow "Download Python" button.
    echo   3. Run the installer. On the FIRST screen, check the box that
    echo      says "Add python.exe to PATH" before clicking Install.
    echo   4. Once it finishes, double-click this file again.
    echo.
    pause
    exit /b 1
)

if not exist venv (
    echo Setting things up for the first time, this can take a minute or two...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo Something went wrong creating the Python environment. Copy the
        echo error above and share it so it can be fixed.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Installing/checking required packages...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo Something went wrong installing packages. Copy the error above
    echo and share it so it can be fixed.
    pause
    exit /b 1
)

if not exist credentials.json (
    echo.
    echo NOTE: credentials.json is missing. You'll need it before the
    echo Google Drive upload step will work - see README.md, section
    echo "Create a Google OAuth client". You can still start the app
    echo and test pasting a link; only the final upload needs this file.
    echo.
)

echo.
echo Starting the app... your browser will open automatically in a
echo couple of seconds.
echo Keep this black window open while you use the app.
echo Close this window when you're done.
echo.

start /b "" cmd /c "timeout /t 2 /nobreak >nul && start "" http://127.0.0.1:5000"
python app.py

pause
