@echo off
echo Starting AI Image Generator locally...

REM Start backend
echo Starting backend API on http://localhost:8000
start /B cmd /c "cd backend && pip install -r requirements.txt && python main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo Starting frontend on http://localhost:3000
cd frontend
start /B python -m http.server 3000

echo.
echo Services started!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo.
echo Close this window to stop all services
pause