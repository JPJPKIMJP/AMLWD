@echo off
echo ===================================
echo   Deploying AMLWD to Firebase
echo ===================================
echo.

echo Deploying Functions and Hosting...
firebase deploy

echo.
echo ===================================
echo    Deployment Complete!
echo ===================================
echo.
echo Your app is now live at:
echo https://amlwd-image-gen.web.app
echo.
echo API Endpoint:
echo https://amlwd-image-gen.web.app/api/generate
echo.
pause