#Requires -Version 5.1
<#
╔═══════════════════════════════════════════════════════════════════════════╗
║  AcadLabs CLI Installer v1.0.1 - Windows (PowerShell)                   ║
║  GitHub: https://github.com/Acadgacor/acadlabs-cli                     ║
║  Docs:   https://acadlabs.fun/docs                                     ║
╚═══════════════════════════════════════════════════════════════════════════╝
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage = "Installation method: auto, pipx, or pip")]
    [ValidateSet("auto", "pipx", "pip")]
    [string]$Method = "auto",

    [Parameter(HelpMessage = "Skip all interactive prompts")]
    [switch]$NoPrompt,

    [Parameter(HelpMessage = "Show what would be done without executing")]
    [switch]$DryRun,

    [Parameter(HelpMessage = "Show detailed output")]
    [switch]$Verbose,

    [Parameter(HelpMessage = "Show version")]
    [switch]$Version
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
$Script:REPO_URL = "https://github.com/Acadgacor/acadlabs-cli.git"
$Script:DOCS_URL = "https://acadlabs.fun/docs"
$Script:WEB_UI = "https://acadlabs.fun"
$Script:INSTALLER_VER = "1.0.1"
$Script:MIN_PY_MAJOR = 3
$Script:MIN_PY_MINOR = 8

$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

function Write-Step {
    param([string]$Step, [string]$Message)
    Write-Host "  [$Step] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK]    " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [WARN]  " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO]  " -ForegroundColor DarkGray -NoNewline
    Write-Host $Message
}

function Write-Banner {
    $banner = @"

  ╔════════════════════════════════════════════════════════════╗
  ║                                                            ║
  ║       _                _ _         _                       ║
  ║      / \   ___ __ _ __| | |   __ _| |__  ___               ║
  ║     / _ \ / __/ _`` / _`` | |  / _`` | '_ \/ __|           ║
  ║    / ___ \ (_| (_| (_| | | |_| (_| | |_) \__ \             ║
  ║   /_/   \_\___\__,_\__,_|_|__\__,_|_.__/|___/              ║
  ║                                                            ║
  ║       AcadLabs CLI Installer v$($Script:INSTALLER_VER)     ║
  ║       AI-Powered Coding Assistant                          ║
  ║                                                            ║
  ╚════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Write-SuccessBanner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║                                                            ║" -ForegroundColor Green
    Write-Host "  ║           ✅ Installation Complete!                         ║" -ForegroundColor Green
    Write-Host "  ║                                                            ║" -ForegroundColor Green
    Write-Host "  ╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""

    Write-Host "  Quick Start:" -ForegroundColor White
    Write-Host "  ──────────────────────────────────────────────────────────"
    Write-Host "    acadlabs --help           " -ForegroundColor Cyan -NoNewline
    Write-Host "  Show all commands and usage"
    Write-Host "    acadlabs login            " -ForegroundColor Cyan -NoNewline
    Write-Host "  Login with email/password"
    Write-Host "    acadlabs login-google     " -ForegroundColor Cyan -NoNewline
    Write-Host "  Login with Google OAuth"
    Write-Host "    acadlabs chat             " -ForegroundColor Cyan -NoNewline
    Write-Host "  Start AI chat session"
    Write-Host "    acadlabs config init      " -ForegroundColor Cyan -NoNewline
    Write-Host "  Setup API keys and config"
    Write-Host ""

    Write-Host "  Command Groups:" -ForegroundColor White
    Write-Host "  ──────────────────────────────────────────────────────────"
    Write-Host "    acadlabs auth --help      " -ForegroundColor Cyan -NoNewline
    Write-Host "  Auth commands (login, logout, status)"
    Write-Host "    acadlabs chat --help      " -ForegroundColor Cyan -NoNewline
    Write-Host "  Chat commands (start session)"
    Write-Host "    acadlabs config --help    " -ForegroundColor Cyan -NoNewline
    Write-Host "  Config commands (init, show)"
    Write-Host ""

    Write-Host "  Resources:" -ForegroundColor White
    Write-Host "  ──────────────────────────────────────────────────────────"
    Write-Host "    Web:    " -ForegroundColor DarkGray -NoNewline
    Write-Host $Script:WEB_UI -ForegroundColor Cyan
    Write-Host "    Docs:   " -ForegroundColor DarkGray -NoNewline
    Write-Host $Script:DOCS_URL -ForegroundColor Cyan
    Write-Host "    GitHub: " -ForegroundColor DarkGray -NoNewline
    Write-Host "https://github.com/Acadgacor/acadlabs-cli" -ForegroundColor Cyan
    Write-Host ""
}

function Write-FailBanner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "  ║           ❌ Installation Failed!                          ║" -ForegroundColor Red
    Write-Host "  ╚════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Possible solutions:" -ForegroundColor Yellow
    Write-Host "    1. Check your internet connection"
    Write-Host "    2. Run PowerShell as Administrator"
    Write-Host "    3. Install git if not installed: " -NoNewline
    Write-Host "https://git-scm.com" -ForegroundColor Cyan
    Write-Host "    4. Try manual install:"
    Write-Host "       pip install git+$($Script:REPO_URL)" -ForegroundColor DarkGray
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════

function Test-PythonInstalled {
    Write-Step "1/4" "Checking Python installation..."

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Err "Python is not installed or not in PATH!"
        Write-Host ""
        Write-Host "  Please install Python $($Script:MIN_PY_MAJOR).$($Script:MIN_PY_MINOR)+ from:" -ForegroundColor Yellow
        Write-Host "    https://www.python.org/downloads/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
        Write-Host ""
        return $false
    }

    $versionOutput = & python --version 2>&1
    if ($versionOutput -match "(\d+)\.(\d+)\.(\d+)") {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
        $pyPatch = [int]$Matches[3]
        $pyVersion = "$pyMajor.$pyMinor.$pyPatch"

        if (($pyMajor -lt $Script:MIN_PY_MAJOR) -or
            ($pyMajor -eq $Script:MIN_PY_MAJOR -and $pyMinor -lt $Script:MIN_PY_MINOR)) {
            Write-Err "Python $pyVersion detected, but $($Script:MIN_PY_MAJOR).$($Script:MIN_PY_MINOR)+ is required."
            Write-Host "  Please update: https://www.python.org/downloads/" -ForegroundColor Yellow
            return $false
        }

        Write-Ok "Python $pyVersion detected"
    }
    else {
        Write-Warn "Could not parse Python version, continuing..."
    }

    return $true
}

function Test-PipInstalled {
    Write-Step "2/4" "Checking pip..."

    try {
        $null = & python -m pip --version 2>&1
        Write-Ok "pip is available"
        return $true
    }
    catch {
        Write-Warn "pip not found, attempting to bootstrap..."
        try {
            & python -m ensurepip --default-pip 2>&1 | Out-Null
            Write-Ok "pip installed successfully"
            return $true
        }
        catch {
            Write-Err "Failed to install pip. Please install it manually."
            return $false
        }
    }
}

function Get-InstallMethod {
    Write-Step "3/4" "Detecting best install method..."

    $selected = $Method

    if ($selected -eq "auto") {
        $pipxCmd = Get-Command pipx -ErrorAction SilentlyContinue
        if ($pipxCmd) {
            Write-Ok "pipx detected - using isolated environment (recommended)"
            $selected = "pipx"
        }
        else {
            Write-Info "pipx not found - using pip"
            $selected = "pip"
        }
    }
    else {
        Write-Info "Using specified method: $selected"
    }

    return $selected
}

# ═══════════════════════════════════════════════════════════════════════════
# INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════

function Install-AcadLabsCLI {
    param([string]$InstallMethod)

    Write-Step "4/4" "Installing AcadLabs CLI via $InstallMethod..."
    Write-Host ""

    if ($DryRun) {
        Write-Info "[DRY RUN] Would execute installation via $InstallMethod"
        return $true
    }

    try {
        if ($InstallMethod -eq "pipx") {
            & pipx install "git+$($Script:REPO_URL)" --force 2>&1 | ForEach-Object {
                if ($Verbose) { Write-Host "    $_" -ForegroundColor DarkGray }
            }
        }
        else {
            & python -m pip install "git+$($Script:REPO_URL)" --force-reinstall --quiet 2>&1 | ForEach-Object {
                if ($Verbose) { Write-Host "    $_" -ForegroundColor DarkGray }
            }
        }

        if ($LASTEXITCODE -ne 0) {
            return $false
        }

        return $true
    }
    catch {
        Write-Err "Installation threw an exception: $_"
        return $false
    }
}

function Test-Installation {
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    $acadlabsCmd = Get-Command acadlabs -ErrorAction SilentlyContinue
    if ($acadlabsCmd) {
        try {
            $ver = & acadlabs --version 2>&1
            Write-Ok "'acadlabs' command is ready! ($ver)"
        }
        catch {
            Write-Ok "'acadlabs' command is available"
        }
        return $true
    }
    else {
        Write-Warn "'acadlabs' not found in PATH."
        Write-Host "  You may need to:" -ForegroundColor Yellow
        Write-Host "    1. Restart your terminal"
        Write-Host "    2. Or add Python Scripts to PATH"
        Write-Host ""

        # Try to find it
        $possiblePaths = @(
            "$env:APPDATA\Python\Scripts",
            "$env:LOCALAPPDATA\Programs\Python\Python*\Scripts",
            "$env:USERPROFILE\.local\bin"
        )
        foreach ($p in $possiblePaths) {
            $resolved = Resolve-Path $p -ErrorAction SilentlyContinue
            if ($resolved) {
                $exe = Get-ChildItem -Path $resolved -Filter "acadlabs*" -ErrorAction SilentlyContinue
                if ($exe) {
                    Write-Info "Found acadlabs at: $($exe.FullName)"
                    Write-Host "    Add to PATH: " -ForegroundColor Yellow -NoNewline
                    Write-Host "`$env:Path += `";$($resolved.Path)`"" -ForegroundColor Cyan
                    break
                }
            }
        }

        return $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

function Main {
    if ($Version) {
        Write-Host "AcadLabs CLI Installer v$($Script:INSTALLER_VER)"
        return
    }

    Clear-Host
    Write-Banner

    if ($DryRun) {
        Write-Warn "[DRY RUN MODE] - No changes will be made"
        Write-Host ""
    }

    # Step 1: Check Python
    if (-not (Test-PythonInstalled)) {
        exit 1
    }

    # Step 2: Check pip
    if (-not (Test-PipInstalled)) {
        exit 1
    }

    # Step 3: Detect method
    $installMethod = Get-InstallMethod

    # Confirmation
    if (-not $NoPrompt) {
        Write-Host ""
        $confirm = Read-Host "  Proceed with installation? [Y/n]"
        if ($confirm -and $confirm.ToLower() -ne "y" -and $confirm.ToLower() -ne "yes" -and $confirm -ne "") {
            Write-Host ""
            Write-Warn "Installation cancelled."
            return
        }
        Write-Host ""
    }

    # Step 4: Install
    $success = Install-AcadLabsCLI -InstallMethod $installMethod
    if (-not $success) {
        Write-FailBanner
        exit 1
    }

    # Step 5: Verify
    Test-Installation | Out-Null

    # Show success
    Write-SuccessBanner
}

# Run
Main
