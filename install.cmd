@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ╔═══════════════════════════════════════════════════════════════════════════╗
:: ║  AcadLabs CLI Installer v1.0.1 - Windows (CMD)                          ║
:: ║  GitHub: https://github.com/Acadgacor/acadlabs-cli                      ║
:: ╚═══════════════════════════════════════════════════════════════════════════╝

set "REPO_URL=https://github.com/Acadgacor/acadlabs-cli.git"
set "INSTALLER_VERSION=1.0.1"
set "MIN_PYTHON_MAJOR=3"
set "MIN_PYTHON_MINOR=8"

:: ─── Parse Arguments ───────────────────────────────────────────────────────
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--version" (
    echo AcadLabs CLI Installer v%INSTALLER_VERSION%
    exit /b 0
)

:: ─── Banner ────────────────────────────────────────────────────────────────
cls
echo.
echo   ============================================================
echo   =                                                          =
echo   =       _                _ _         _                     =
echo   =      / \   ___ __ _ __^| ^| ^|   __ _^| ^|__  ___        =
echo   =     / _ \ / __/ _` / _` ^| ^|  / _` ^| '_ \/ __^|        =
echo   =    / ___ \ (_^| (_^| (_^| ^| ^| ^|_^| (_^| ^| ^|_) \__ \ =
echo   =   /_/   \_\___\__,_\__,_^|_^|__\__,_^|_.__/^|___/        =
echo   =                                                          =
echo   =       AcadLabs CLI Installer v%INSTALLER_VERSION%        =
echo   =       AI-Powered Coding Assistant                        =
echo   =                                                          =
echo   ============================================================
echo.

:: ─── Step 1: Check Python ──────────────────────────────────────────────────
echo   [1/4] Checking Python installation...

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERROR] Python is not installed or not in PATH!
    echo.
    echo   Please install Python %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%+ from:
    echo     https://www.python.org/downloads/
    echo.
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    exit /b 1
)

:: Get Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

:: Check minimum version
if %PY_MAJOR% LSS %MIN_PYTHON_MAJOR% goto :python_too_old
if %PY_MAJOR% EQU %MIN_PYTHON_MAJOR% (
    if %PY_MINOR% LSS %MIN_PYTHON_MINOR% goto :python_too_old
)

echo   [OK]    Python %PY_VERSION% detected

:: ─── Step 2: Check pip ─────────────────────────────────────────────────────
echo   [2/4] Checking pip...

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo   [WARN]  pip not found, attempting to install...
    python -m ensurepip --default-pip >nul 2>&1
    if errorlevel 1 (
        echo   [ERROR] Failed to install pip. Please install it manually.
        exit /b 1
    )
)
echo   [OK]    pip is available

:: ─── Step 3: Detect install method ─────────────────────────────────────────
echo   [3/4] Detecting best install method...

set "INSTALL_METHOD=pip"
where pipx >nul 2>&1
if not errorlevel 1 (
    set "INSTALL_METHOD=pipx"
    echo   [OK]    pipx detected - using isolated environment ^(recommended^)
) else (
    echo   [INFO]  pipx not found - using pip
)

:: ─── Step 4: Install ───────────────────────────────────────────────────────
echo   [4/4] Installing AcadLabs CLI via %INSTALL_METHOD%...
echo.

if "%INSTALL_METHOD%"=="pipx" (
    pipx install "git+%REPO_URL%" --force
) else (
    python -m pip install "git+%REPO_URL%" --force-reinstall --quiet
)

if errorlevel 1 (
    echo.
    echo   ============================================================
    echo   =  [ERROR] Installation failed!                            =
    echo   ============================================================
    echo.
    echo   Possible solutions:
    echo     1. Check your internet connection
    echo     2. Try running as Administrator
    echo     3. Install git if not installed: https://git-scm.com
    echo     4. Try manual install:
    echo        pip install git+%REPO_URL%
    echo.
    exit /b 1
)

:: ─── Step 5: Verify ────────────────────────────────────────────────────────
echo.

where acadlabs >nul 2>&1
if errorlevel 1 (
    echo   [WARN]  'acadlabs' command not found in PATH.
    echo           You may need to restart your terminal or add
    echo           Python Scripts to your PATH.
    echo.
    echo   Typical location:
    echo     %%APPDATA%%\Python\Python3x\Scripts
    echo.
) else (
    echo   [OK]    'acadlabs' command is ready!
)

:: ─── Success Banner ────────────────────────────────────────────────────────
echo.
echo   ============================================================
echo   =                                                          =
echo   =          Installation Complete!                          =
echo   =                                                          =
echo   ============================================================
echo.
echo   Quick Start:
echo   ──────────────────────────────────────────────────────────
echo     acadlabs --help             Show all commands and usage
echo     acadlabs login              Login with email/password
echo     acadlabs login-google       Login with Google OAuth
echo     acadlabs chat               Start AI chat session
echo     acadlabs config init        Setup API keys and config
echo.
echo   Command Groups:
echo   ──────────────────────────────────────────────────────────
echo     acadlabs auth --help        Auth commands (login, logout, status)
echo     acadlabs chat --help        Chat commands (start session)
echo     acadlabs config --help      Config commands (init, show)
echo.
echo   Resources:
echo   ──────────────────────────────────────────────────────────
echo     Web:    https://acadlabs.fun
echo     Docs:   https://acadlabs.fun/docs
echo     GitHub: https://github.com/Acadgacor/acadlabs-cli
echo.

exit /b 0

:: ─── Error Labels ──────────────────────────────────────────────────────────
:python_too_old
echo.
echo   [ERROR] Python %PY_VERSION% detected, but %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%+ is required.
echo   Please update Python: https://www.python.org/downloads/
echo.
exit /b 1

:show_help
echo.
echo   AcadLabs CLI Installer v%INSTALLER_VERSION%
echo.
echo   Usage:
echo     install.cmd [OPTIONS]
echo.
echo   Options:
echo     --help, -h       Show this help message
echo     --version        Show installer version
echo.
echo   Description:
echo     Installs the AcadLabs CLI tool on your system. The installer will:
echo       1. Check that Python 3.8+ is installed
echo       2. Verify pip is available
echo       3. Detect pipx for isolated install (falls back to pip)
echo       4. Install AcadLabs CLI from GitHub
echo       5. Verify the installation
echo.
echo   After installation, run 'acadlabs --help' for full usage information.
echo.
exit /b 0
