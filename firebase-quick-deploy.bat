@echo off
echo ===================================
echo   AMLWD Quick Firebase Deploy
echo ===================================
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Install Firebase CLI if not installed
where firebase >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Firebase CLI...
    call npm install -g firebase-tools
)

REM Login check
echo Checking Firebase login...
call firebase login

REM Navigate to firebase directory
cd firebase

REM Set RunPod credentials
echo.
echo Setting RunPod credentials...

REM Check for environment variables
if "%RUNPOD_API_KEY%"=="" (
    echo ERROR: RUNPOD_API_KEY environment variable not set!
    echo Please set it using: set RUNPOD_API_KEY=your-api-key
    pause
    exit /b 1
)
if "%RUNPOD_ENDPOINT_ID%"=="" (
    echo ERROR: RUNPOD_ENDPOINT_ID environment variable not set!
    echo Please set it using: set RUNPOD_ENDPOINT_ID=your-endpoint-id
    pause
    exit /b 1
)

call firebase functions:config:set runpod.api_key="%RUNPOD_API_KEY%"
call firebase functions:config:set runpod.endpoint_id="%RUNPOD_ENDPOINT_ID%"

REM Install dependencies
echo.
echo Installing dependencies...
cd functions
call npm install
cd ..

REM Update the frontend with correct URL
echo.
echo Updating frontend configuration...
cd ..
powershell -Command "(Get-Content index-firebase.html) -replace 'YOUR-FIREBASE-PROJECT', 'amlwd-image-gen' | Set-Content index-firebase.html"
cd firebase

REM Deploy
echo.
echo Deploying to Firebase...
call firebase deploy

echo.
echo ===================================
echo    Deployment Complete!
echo ===================================
echo.
echo Your app is live at:
echo https://amlwd-image-gen.web.app/index-firebase.html
echo.
echo Test it now!
echo.
pause