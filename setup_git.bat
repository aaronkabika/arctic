@echo off
echo ============================================
echo Arctic Project Git Setup Script
echo ============================================
echo.
echo This script will help you connect your project to GitHub.
echo.
echo Before running this script, make sure you have:
echo 1. Git installed on your system
echo 2. A GitHub account
echo 3. Created an empty repository at: https://github.com/aaronkabika/arctic.git
echo.
echo If you haven't installed Git yet, download it from:
echo https://git-scm.com/download/win
echo.
pause

echo.
echo Step 1: Checking Git installation...
git --version
if %errorlevel% neq 0 (
    echo Git is not installed or not in PATH.
    echo Please install Git first.
    pause
    exit /b 1
)

echo.
echo Step 2: Initializing Git repository...
git init
if %errorlevel% neq 0 (
    echo Failed to initialize Git repository.
    pause
    exit /b 1
)

echo.
echo Step 3: Adding all files to staging...
git add .
if %errorlevel% neq 0 (
    echo Failed to add files to staging.
    pause
    exit /b 1
)

echo.
echo Step 4: Making initial commit...
git commit -m "Initial commit: Arctic art gallery platform"
if %errorlevel% neq 0 (
    echo Failed to make initial commit.
    pause
    exit /b 1
)

echo.
echo Step 5: Adding remote repository...
git remote add origin https://github.com/aaronkabika/arctic.git
if %errorlevel% neq 0 (
    echo Failed to add remote repository.
    pause
    exit /b 1
)

echo.
echo Step 6: Pushing to GitHub...
echo Note: You may need to authenticate with GitHub.
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo If you get an error about "main" branch not existing, try:
    echo git push -u origin master
    echo.
    pause
)

echo.
echo ============================================
echo Git setup completed!
echo ============================================
echo.
echo Your project is now connected to GitHub.
echo Repository URL: https://github.com/aaronkabika/arctic.git
echo.
echo To make future updates:
echo 1. Make your changes
echo 2. git add .
echo 3. git commit -m "Your commit message"
echo 4. git push
echo.
pause