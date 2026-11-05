# Git Setup Guide for Arctic Project

This guide will help you connect your Arctic project to the GitHub repository at:
**https://github.com/aaronkabika/arctic.git**

## Prerequisites

Before you begin, ensure you have:
1. **Git installed** on your system
2. A **GitHub account**
3. **GitHub credentials** configured

## Option 1: Automated Setup (Recommended)

### Using PowerShell (Recommended for Windows):
1. Open PowerShell in the project directory
2. Run the setup script:
   ```powershell
   .\setup_git.ps1
   ```

### Using Command Prompt:
1. Open Command Prompt in the project directory
2. Run the setup script:
   ```cmd
   setup_git.bat
   ```

## Option 2: Manual Setup

Follow these steps if you prefer to set up Git manually:

### Step 1: Install Git
If Git is not installed, download it from: https://git-scm.com/download/win

### Step 2: Configure Git (First Time Only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Initialize Git Repository
```bash
git init
```

### Step 4: Add All Files
```bash
git add .
```

### Step 5: Create Initial Commit
```bash
git commit -m "Initial commit: Arctic art gallery platform"
```

### Step 6: Add Remote Repository
```bash
git remote add origin https://github.com/aaronkabika/arctic.git
```

### Step 7: Create Main Branch (if needed)
```bash
git branch -M main
```

### Step 8: Push to GitHub
```bash
git push -u origin main
```

## Authentication

You may be prompted to authenticate with GitHub. Choose one of these methods:

### Method 1: Personal Access Token (Recommended)
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Use the token as your password when prompted

### Method 2: GitHub CLI
```bash
gh auth login
```

### Method 3: SSH Keys
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your.email@example.com"`
2. Add key to SSH agent: `ssh-add ~/.ssh/id_ed25519`
3. Add public key to GitHub: Settings → SSH and GPG keys
4. Use SSH URL: `git remote set-url origin git@github.com:aaronkabika/arctic.git`

## Common Issues & Solutions

### Issue: "Git is not recognized"
**Solution:** Git is not installed or not in PATH. Install Git and restart your terminal.

### Issue: "Authentication failed"
**Solution:** Use a Personal Access Token instead of your GitHub password.

### Issue: "Repository not found"
**Solution:** Ensure the repository exists at https://github.com/aaronkabika/arctic.git

### Issue: "Permission denied"
**Solution:** Check that you have access to the repository and your credentials are correct.

### Issue: "Branch 'main' not found"
**Solution:** Try using `master` instead: `git push -u origin master`

## Daily Git Workflow

Once set up, use these commands for regular development:

### 1. Check Status
```bash
git status
```

### 2. Add Changes
```bash
git add .
# or add specific files
git add filename.py
```

### 3. Commit Changes
```bash
git commit -m "Describe your changes"
```

### 4. Push to GitHub
```bash
git push
```

### 5. Pull Latest Changes
```bash
git pull
```

## Useful Git Commands

### View Commit History
```bash
git log
```

### View Remote URL
```bash
git remote -v
```

### Create New Branch
```bash
git checkout -b feature-name
```

### Switch Branch
```bash
git checkout branch-name
```

### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1
```

### Discard Local Changes
```bash
git checkout -- filename
```

## Files Already Configured

Your project already includes:
- ✅ `.gitignore` - Prevents sensitive files from being committed
- ✅ `README.md` - Project documentation
- ✅ `requirements.txt` - Python dependencies
- ✅ `setup_git.bat` - Automated setup script (Windows CMD)
- ✅ `setup_git.ps1` - Automated setup script (PowerShell)

## What Gets Ignored

The following files/folders are ignored by Git (see `.gitignore`):
- Virtual environment (`.venv/`)
- Database files (`*.db`, `arctic.db`)
- Uploaded files (`uploads/` except `.gitkeep`)
- Python cache (`__pycache__/`)
- IDE settings (`.idea/`, `.vscode/`)
- Environment variables (`.env`)

## Next Steps After Setup

1. **Verify Connection:**
   ```bash
   git remote -v
   ```

2. **Check Repository Status:**
   ```bash
   git status
   ```

3. **View on GitHub:**
   Visit https://github.com/aaronkabika/arctic

4. **Clone on Another Machine:**
   ```bash
   git clone https://github.com/aaronkabika/arctic.git
   ```

## Support

If you encounter issues:
1. Check this guide for common solutions
2. Review Git documentation: https://git-scm.com/doc
3. Check GitHub documentation: https://docs.github.com

---

**Repository URL:** https://github.com/aaronkabika/arctic.git
**Created:** 2026-10-31
