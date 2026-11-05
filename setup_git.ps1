Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Arctic Project Git Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will help you connect your project to GitHub."
Write-Host ""
Write-Host "Before running this script, make sure you have:"
Write-Host "1. Git installed on your system"
Write-Host "2. A GitHub account"
Write-Host "3. Created an empty repository at: https://github.com/aaronkabika/arctic.git"
Write-Host ""
Write-Host "If you haven't installed Git yet, download it from:"
Write-Host "https://git-scm.com/download/win"
Write-Host ""
Read-Host "Press Enter to continue"

Write-Host ""
Write-Host "Step 1: Checking Git installation..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "Git version: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Git first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 2: Initializing Git repository..." -ForegroundColor Yellow
try {
    git init
    Write-Host "Git repository initialized successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to initialize Git repository." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 3: Adding all files to staging..." -ForegroundColor Yellow
try {
    git add .
    Write-Host "Files added to staging successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to add files to staging." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 4: Making initial commit..." -ForegroundColor Yellow
try {
    git commit -m "Initial commit: Arctic art gallery platform"
    Write-Host "Initial commit created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to make initial commit." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 5: Adding remote repository..." -ForegroundColor Yellow
try {
    git remote add origin https://github.com/aaronkabika/arctic.git
    Write-Host "Remote repository added successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to add remote repository." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 6: Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Note: You may need to authenticate with GitHub." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "If you get an error about 'main' branch not existing, try:" -ForegroundColor Yellow
    Write-Host "git push -u origin master" -ForegroundColor Yellow
    Write-Host ""
    try {
        git push -u origin master
        Write-Host "Successfully pushed to GitHub using 'master' branch!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to push to GitHub." -ForegroundColor Red
        Write-Host "You may need to configure your GitHub credentials." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Git setup completed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your project is now connected to GitHub." -ForegroundColor Green
Write-Host "Repository URL: https://github.com/aaronkabika/arctic.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "To make future updates:" -ForegroundColor Yellow
Write-Host "1. Make your changes"
Write-Host "2. git add ."
Write-Host "3. git commit -m 'Your commit message'"
Write-Host "4. git push"
Write-Host ""
Read-Host "Press Enter to exit"