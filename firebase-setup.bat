@echo off
echo ===================================
echo    AMLWD Firebase Setup
echo ===================================
echo.

echo Step 1: Installing Firebase CLI...
call npm install -g firebase-tools

echo.
echo Step 2: Login to Firebase
call firebase login

echo.
echo Step 3: Navigate to firebase directory
cd firebase

echo.
echo Step 4: Initialize Firebase
echo When prompted:
echo - Choose Functions and Hosting
echo - Select your project: amlwd-image-gen
echo - Choose JavaScript
echo - Don't use ESLint
echo - Install dependencies
echo.
pause
call firebase init

echo.
echo Step 5: Setting RunPod credentials...

REM Check for environment variables
if "%RUNPOD_API_KEY%"=="" (
    echo Error: RUNPOD_API_KEY environment variable not set!
    echo Please set it using: set RUNPOD_API_KEY=your-api-key
    pause
    exit /b 1
)
if "%RUNPOD_ENDPOINT_ID%"=="" (
    echo Error: RUNPOD_ENDPOINT_ID environment variable not set!
    echo Please set it using: set RUNPOD_ENDPOINT_ID=your-endpoint-id
    pause
    exit /b 1
)

call firebase functions:config:set runpod.api_key="%RUNPOD_API_KEY%"
call firebase functions:config:set runpod.endpoint_id="%RUNPOD_ENDPOINT_ID%"

echo.
echo Step 6: Installing dependencies...
cd functions
call npm install
cd ..

echo.
echo Step 7: Deploying to Firebase...
call firebase deploy

echo.
echo ===================================
echo    Setup Complete!
echo ===================================
echo.
echo Your app should be available at:
echo https://amlwd-image-gen.web.app
echo.
echo Don't forget to update index-firebase.html with your URL!
echo.
pause