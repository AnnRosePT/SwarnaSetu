@echo off
setlocal
cd /d "%~dp0"
echo.
echo  SwarnaSetu - starting...
echo.
where python >nul 2>nul || (
  echo  Python 3.10 or newer is needed. Get it from https://www.python.org/downloads/
  echo  and tick "Add python.exe to PATH" while installing.
  pause
  exit /b 1
)
if not exist "backend\.venv\Scripts\python.exe" (
  echo  Creating the Python environment ^(first run only^)...
  python -m venv backend\.venv || (pause & exit /b 1)
)
call backend\.venv\Scripts\activate.bat
echo  Installing Python packages...
python -m pip install --quiet --disable-pip-version-check -r backend\requirements.txt || (pause & exit /b 1)
if not exist "frontend\dist\index.html" (
  where npm >nul 2>nul || (
    echo  The web app is not built yet and Node.js is not installed.
    echo  Install Node.js 18 or newer from https://nodejs.org and run this again.
    pause
    exit /b 1
  )
  echo  Building the web app ^(first run only^)...
  pushd frontend
  call npm install --no-audit --no-fund || (popd & pause & exit /b 1)
  call npm run build || (popd & pause & exit /b 1)
  popd
)
cd backend
echo.
echo  Open http://localhost:8000 in your browser. Press Ctrl+C here to stop.
echo.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
