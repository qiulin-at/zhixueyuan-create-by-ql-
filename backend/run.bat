@echo off
cd /d "%~dp0"

if not exist "..\.venv\Scripts\python.exe" goto no_venv

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if not errorlevel 1 goto port_busy

echo ============================================
echo   ZhiXueYun backend
echo   API : http://127.0.0.1:8000
echo   Docs: http://127.0.0.1:8000/docs
echo   Stop: Ctrl+C
echo ============================================
echo.

"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo Server stopped. Press any key to close this window.
pause >nul
exit /b 0

:port_busy
echo [ERROR] Port 8000 is already in use.
echo Close the other backend window first (press Ctrl+C there), then run this again.
echo.
netstat -ano | findstr ":8000" | findstr "LISTENING"
echo.
pause
exit /b 1

:no_venv
echo [ERROR] venv not found: ..\.venv\Scripts\python.exe
echo Create it from the project root:
echo     python -m venv .venv
echo     .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
echo.
pause
exit /b 1
