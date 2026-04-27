@echo off
echo ============================================
echo    DEPLOYING INVOICE APP TO HEROKU
echo ============================================
echo.

echo Step 1: Installing Heroku CLI (if needed)
echo Please install Heroku CLI from: https://devcenter.heroku.com/articles/heroku-cli
echo Press any key after installing Heroku CLI...
pause

echo.
echo Step 2: Login to Heroku
heroku login

echo.
echo Step 3: Creating Heroku app
set /p APP_NAME="Enter your app name (e.g., my-invoice-app): "
heroku create %APP_NAME%

echo.
echo Step 4: Adding PostgreSQL database
heroku addons:create heroku-postgresql:hobby-dev --app %APP_NAME%

echo.
echo Step 5: Setting environment variables
heroku config:set SECRET_KEY=%RANDOM%%RANDOM%%RANDOM% --app %APP_NAME%
heroku config:set FLASK_ENV=production --app %APP_NAME%

echo.
echo Step 6: Adding files to git
git add .
git commit -m "Initial deployment to Heroku"

echo.
echo Step 7: Deploying to Heroku
git push heroku main

echo.
echo ============================================
echo    DEPLOYMENT COMPLETE!
echo ============================================
echo.
echo Your app is now live at: https://%APP_NAME%.herokuapp.com
echo.
echo Next steps:
echo 1. Visit your app and create an admin account
echo 2. Set up Stripe for payments
echo 3. Add your custom domain
echo 4. Start marketing to customers!
echo.
pause 