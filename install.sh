#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🎓 AcadLabs CLI Installer v1.0.1                                        ║
# ║   AI-Powered Coding Assistant CLI                                         ║
# ║                                                                           ║
# ║   GitHub: https://github.com/Acadgacor/acadlabs-cli                       ║
# ║   Docs:   https://acadlabs.fun/docs                                       ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 COLORS & STYLES
# ═══════════════════════════════════════════════════════════════════════════
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly GRAY='\033[0;90m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
readonly REPO_URL="https://github.com/Acadgacor/acadlabs-cli.git"
readonly DOCS_URL="https://acadlabs.fun/docs"
readonly WEB_UI="https://acadlabs.fun"
readonly INSTALLER_VERSION="1.0.1"
readonly MIN_PYTHON_MAJOR=3
readonly MIN_PYTHON_MINOR=8

# Default values (can be overridden by env vars)
INSTALL_METHOD="${ACADLABS_INSTALL_METHOD:-auto}"
NO_PROMPT="${ACADLABS_NO_PROMPT:-false}"
VERBOSE="${ACADLABS_VERBOSE:-false}"
DRY_RUN=false

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# All log functions output to stderr so they don't interfere with stdout capture
log_info()    { echo -e "${BLUE}[INFO]${NC}  $1" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1" >&2; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_step()    { echo -e "${CYAN}[STEP]${NC}  ${BOLD}$1${NC}" >&2; }
log_success() { echo -e "${GREEN}[✓]${NC}    $1" >&2; }
log_debug()   { $VERBOSE && echo -e "${GRAY}[DBG]${NC}   $1" >&2 || true; }

print_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'BANNER'
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║    █████╗  ██████╗ █████╗ ██████╗                      ║
  ║   ██╔══██╗██╔════╝██╔══██╗██╔══██╗                     ║
  ║   ███████║██║     ███████║██║  ██║                     ║
  ║   ██╔══██║██║     ██╔══██║██║  ██║                     ║
  ║   ██║  ██║╚██████╗██║  ██║██████╔╝                     ║
  ║   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝                      ║
  ║                    L A B S                             ║
  ║                                                        ║
BANNER
    echo "  ║         ${WHITE}${BOLD}AI-Powered Coding Assistant${NC}${CYAN}                    ║"
    echo "  ║         ${DIM}Installer v${INSTALLER_VERSION}${NC}${CYAN}                           ║"
    echo "  ║                                                        ║"
    echo "  ╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    local title="$1"
    echo "" >&2
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2
    echo -e "${WHITE}${BOLD}  $title${NC}" >&2
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2
    echo "" >&2
}

check_command() {
    command -v "$1" &>/dev/null
}

confirm() {
    local message="$1"
    local default="${2:-y}"

    if [[ "$NO_PROMPT" == "true" ]] || [[ "$NO_PROMPT" == "1" ]]; then
        [[ "$default" == "y" ]]
        return $?
    fi

    local prompt="[Y/n]"
    [[ "$default" != "y" ]] && prompt="[y/N]"

    echo -en "${YELLOW}  $message $prompt: ${NC}" >&2
    read -r response
    response=${response:-$default}

    [[ "$response" =~ ^[yY](es)?$ ]]
}

# ═══════════════════════════════════════════════════════════════════════════
# 📋 ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════

print_usage() {
    cat << EOF
${CYAN}${BOLD}AcadLabs CLI Installer v${INSTALLER_VERSION}${NC}

${WHITE}${BOLD}USAGE:${NC}
  $0 [OPTIONS]

${WHITE}${BOLD}OPTIONS:${NC}
  --method <auto|pipx|pip>   Installation method (default: auto)
                              • auto  - detect best method automatically
                              • pipx  - isolated environment (recommended)
                              • pip   - global pip install
  --no-prompt                Skip interactive prompts, use defaults
  --verbose                  Enable verbose/debug output
  --dry-run                  Show what would be done without executing
  -h, --help                 Show this help message
  --version                  Show installer version

${WHITE}${BOLD}ENVIRONMENT VARIABLES:${NC}
  ACADLABS_INSTALL_METHOD    Set installation method (auto|pipx|pip)
  ACADLABS_NO_PROMPT         Disable prompts (true/false or 1/0)
  ACADLABS_VERBOSE           Enable verbose mode (true/false or 1/0)

${WHITE}${BOLD}EXAMPLES:${NC}
  $0                                    # Interactive install
  $0 --method pipx --no-prompt          # Silent pipx install
  $0 --dry-run                          # Preview installation steps
  ACADLABS_INSTALL_METHOD=pip $0        # Force pip installation

${WHITE}${BOLD}AFTER INSTALLATION:${NC}
  acadlabs --help             Show all commands and usage
  acadlabs login              Login with email/password
  acadlabs login-google       Login with Google OAuth
  acadlabs chat               Start AI chat session
  acadlabs config init        Setup API keys and config

${WHITE}${BOLD}COMMAND GROUPS:${NC}
  acadlabs auth --help        Auth commands (login, logout, status)
  acadlabs chat --help        Chat commands (start session)
  acadlabs config --help      Config commands (init, show)

${WHITE}${BOLD}RESOURCES:${NC}
  Web:        ${CYAN}${WEB_UI}${NC}
  Docs:       ${CYAN}${DOCS_URL}${NC}
  GitHub:     ${CYAN}https://github.com/Acadgacor/acadlabs-cli${NC}
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --method)
                if [[ -z "$2" ]] || [[ "$2" == --* ]]; then
                    log_error "Missing value for --method. Expected: auto, pipx, or pip"
                    exit 1
                fi
                if [[ ! "$2" =~ ^(auto|pipx|pip)$ ]]; then
                    log_error "Invalid method '$2'. Must be: auto, pipx, or pip"
                    exit 1
                fi
                INSTALL_METHOD="$2"
                shift 2
                ;;
            --no-prompt)
                NO_PROMPT=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --version)
                echo "AcadLabs CLI Installer v${INSTALLER_VERSION}"
                exit 0
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "" >&2
                echo "  Run '$0 --help' for usage information." >&2
                exit 1
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════════════════════
# 🔍 SYSTEM CHECKS
# ═══════════════════════════════════════════════════════════════════════════

check_os() {
    local os_name
    os_name="$(uname -s)"
    case "$os_name" in
        Linux*)   log_debug "OS: Linux" ;;
        Darwin*)  log_debug "OS: macOS" ;;
        CYGWIN*|MINGW*|MSYS*)
            log_warn "Running on Windows (via $os_name)."
            log_warn "Consider using install.ps1 or install.cmd instead."
            ;;
        *)
            log_warn "Unknown OS: $os_name - proceeding anyway"
            ;;
    esac
}

check_git() {
    if ! check_command git; then
        log_error "git is not installed!"
        echo "" >&2
        echo -e "  ${WHITE}Please install git:${NC}" >&2
        echo -e "  ${CYAN}  https://git-scm.com/downloads${NC}" >&2
        echo "" >&2
        echo -e "  ${DIM}On Ubuntu/Debian: sudo apt install git${NC}" >&2
        echo -e "  ${DIM}On macOS:         brew install git${NC}" >&2
        echo "" >&2
        return 1
    fi
    log_success "git is available ✓"
}

check_python() {
    print_section "🐍 Step 1/4: Checking Python Environment"

    # Try python3 first, then python
    local py_cmd=""
    if check_command python3; then
        py_cmd="python3"
    elif check_command python; then
        # Verify it's Python 3
        local py_ver
        py_ver=$(python --version 2>&1 | cut -d' ' -f2)
        local py_major
        py_major=$(echo "$py_ver" | cut -d. -f1)
        if [[ "$py_major" -ge 3 ]]; then
            py_cmd="python"
        fi
    fi

    if [[ -z "$py_cmd" ]]; then
        log_error "Python 3 not found!"
        echo "" >&2
        echo -e "  ${WHITE}Please install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ from:${NC}" >&2
        echo -e "  ${CYAN}  https://www.python.org/downloads/${NC}" >&2
        echo "" >&2
        echo -e "  ${DIM}On Ubuntu/Debian: sudo apt install python3 python3-pip${NC}" >&2
        echo -e "  ${DIM}On macOS:         brew install python3${NC}" >&2
        echo "" >&2
        return 1
    fi

    local version
    version=$($py_cmd --version 2>&1 | cut -d' ' -f2)
    local major minor
    IFS='.' read -r major minor _ <<< "$version"

    if [[ $major -lt $MIN_PYTHON_MAJOR ]] || [[ $major -eq $MIN_PYTHON_MAJOR && $minor -lt $MIN_PYTHON_MINOR ]]; then
        log_error "Python $version detected, but ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required"
        echo -e "  ${WHITE}Please update Python: ${CYAN}https://www.python.org/downloads/${NC}" >&2
        return 1
    fi

    log_success "Python $version detected ✓"

    # Check pip
    if ! $py_cmd -m pip --version &>/dev/null; then
        log_warn "pip not found, attempting to bootstrap..."
        if check_command curl; then
            curl -sS https://bootstrap.pypa.io/get-pip.py | $py_cmd - || {
                log_error "Failed to install pip"
                echo -e "  ${DIM}On Ubuntu/Debian: sudo apt install python3-pip${NC}" >&2
                return 1
            }
        else
            $py_cmd -m ensurepip --default-pip 2>/dev/null || {
                log_error "Failed to install pip"
                return 1
            }
        fi
        log_success "pip installed ✓"
    else
        log_success "pip is available ✓"
    fi

    # Export python command for later use
    PYTHON_CMD="$py_cmd"
    return 0
}

# Detect the best install method and output the method name to stdout
detect_install_method() {
    print_section "🔍 Step 2/4: Detecting Install Method"

    local method="$INSTALL_METHOD"

    if [[ "$method" == "auto" ]]; then
        if check_command pipx; then
            log_success "pipx detected - using isolated environment (recommended)"
            method="pipx"
        else
            log_info "pipx not found - falling back to pip"
            log_debug "Tip: Install pipx for better isolation: python3 -m pip install --user pipx"
            method="pip"
        fi
    else
        log_info "Using specified method: $method"
    fi

    # Only the method name goes to stdout (for variable capture)
    echo "$method"
}

# ═══════════════════════════════════════════════════════════════════════════
# 📦 INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════

install_with_pipx() {
    print_section "📦 Step 3/4: Installing via pipx"

    log_step "Installing AcadLabs CLI with pipx..."

    if $DRY_RUN; then
        echo -e "  ${GRAY}[DRY RUN] pipx install git+${REPO_URL} --force${NC}" >&2
        return 0
    fi

    local cmd=(pipx install "git+${REPO_URL}" --force)
    $VERBOSE && cmd+=(--verbose)

    "${cmd[@]}" || {
        log_error "pipx installation failed"
        return 1
    }

    log_success "Installed via pipx ✓"
    return 0
}

install_with_pip() {
    print_section "📦 Step 3/4: Installing via pip"

    log_step "Installing AcadLabs CLI with pip..."
    log_warn "Using --break-system-packages flag for system Python"

    if $DRY_RUN; then
        echo -e "  ${GRAY}[DRY RUN] $PYTHON_CMD -m pip install git+${REPO_URL} --break-system-packages --force-reinstall${NC}" >&2
        return 0
    fi

    local cmd=($PYTHON_CMD -m pip install "git+${REPO_URL}" --break-system-packages --force-reinstall)
    $VERBOSE && cmd+=(--verbose) || cmd+=(--quiet)

    "${cmd[@]}" || {
        log_error "pip installation failed"
        return 1
    }

    log_success "Installed via pip ✓"
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════
# ✅ VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

verify_installation() {
    print_section "✅ Step 4/4: Verifying Installation"

    # Refresh shell hash table
    hash -r 2>/dev/null || true

    if check_command acadlabs; then
        local version
        version=$(acadlabs --version 2>/dev/null || echo "unknown")
        log_success "Command 'acadlabs' is ready! (v${version})"
        return 0
    fi

    log_warn "'acadlabs' command not found in current PATH"
    echo "" >&2

    # Search common locations
    local locations=("$HOME/.local/bin" "/usr/local/bin" "$HOME/.local/pipx/bin" "$HOME/.local/pipx/venvs/acadlabs-cli/bin")
    for loc in "${locations[@]}"; do
        if [[ -x "$loc/acadlabs" ]]; then
            log_info "Found acadlabs at: $loc/acadlabs"
            echo "" >&2
            echo -e "  ${YELLOW}Add to your PATH (add to ~/.bashrc or ~/.zshrc):${NC}" >&2
            echo -e "  ${CYAN}  export PATH=\"\$PATH:$loc\"${NC}" >&2
            echo "" >&2
            echo -e "  ${DIM}Then restart your terminal or run: source ~/.bashrc${NC}" >&2
            echo "" >&2
            return 0
        fi
    done

    log_error "Could not find acadlabs binary. Installation may have failed."
    echo "" >&2
    echo -e "  ${YELLOW}Troubleshooting:${NC}" >&2
    echo -e "  ${DIM}  1. Restart your terminal and try again${NC}" >&2
    echo -e "  ${DIM}  2. Run: pip show acadlabs-cli${NC}" >&2
    echo -e "  ${DIM}  3. Check pip install output above for errors${NC}" >&2
    echo "" >&2
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎉 SUCCESS BANNER
# ═══════════════════════════════════════════════════════════════════════════

print_success() {
    echo ""
    echo -e "${GREEN}"
    echo "  ╔════════════════════════════════════════════════════════════╗"
    echo "  ║                                                            ║"
    echo "  ║           ✅ Installation Complete!                        ║"
    echo "  ║                                                            ║"
    echo "  ╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "  ${WHITE}${BOLD}Quick Start:${NC}"
    echo -e "  ──────────────────────────────────────────────────────────"
    echo -e "    ${CYAN}acadlabs --help${NC}             Show all commands and usage"
    echo -e "    ${CYAN}acadlabs login${NC}              Login with email/password"
    echo -e "    ${CYAN}acadlabs login-google${NC}       Login with Google OAuth"
    echo -e "    ${CYAN}acadlabs chat${NC}               Start AI chat session"
    echo -e "    ${CYAN}acadlabs config init${NC}        Setup API keys and config"
    echo ""

    echo -e "  ${WHITE}${BOLD}Command Groups:${NC}"
    echo -e "  ──────────────────────────────────────────────────────────"
    echo -e "    ${CYAN}acadlabs auth --help${NC}        Auth commands (login, logout, status)"
    echo -e "    ${CYAN}acadlabs chat --help${NC}        Chat commands (start session)"
    echo -e "    ${CYAN}acadlabs config --help${NC}      Config commands (init, show)"
    echo ""

    echo -e "  ${WHITE}${BOLD}In-Chat Commands:${NC}"
    echo -e "  ──────────────────────────────────────────────────────────"
    echo -e "    ${GRAY}tools${NC}                       Show available AI tools"
    echo -e "    ${GRAY}tokens${NC}                      Show token usage status"
    echo -e "    ${GRAY}clear${NC}                       Clear chat context"
    echo -e "    ${GRAY}exit${NC}                        End chat session"
    echo ""

    echo -e "  ${WHITE}${BOLD}Resources:${NC}"
    echo -e "  ──────────────────────────────────────────────────────────"
    echo -e "    ${GRAY}Web:${NC}    ${CYAN}${WEB_UI}${NC}"
    echo -e "    ${GRAY}Docs:${NC}   ${CYAN}${DOCS_URL}${NC}"
    echo -e "    ${GRAY}GitHub:${NC} ${CYAN}https://github.com/Acadgacor/acadlabs-cli${NC}"
    echo ""
}

print_failure() {
    echo ""
    echo -e "${RED}"
    echo "  ╔════════════════════════════════════════════════════════════╗"
    echo "  ║           ❌ Installation Failed!                          ║"
    echo "  ╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "  ${YELLOW}Possible solutions:${NC}"
    echo -e "    1. Check your internet connection"
    echo -e "    2. Make sure git is installed: ${CYAN}https://git-scm.com${NC}"
    echo -e "    3. Try manual install:"
    echo -e "       ${GRAY}pip install git+${REPO_URL}${NC}"
    echo -e "    4. Check if you have permission issues (try with sudo)"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

main() {
    parse_args "$@"

    print_banner

    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY RUN MODE]${NC} - No changes will be made" >&2
        echo "" >&2
    fi

    # OS Check
    check_os

    # Step 1: Python
    if ! check_python; then
        exit 1
    fi

    # Check git
    check_git || exit 1

    # Step 2: Detect method (only method name goes to stdout)
    local method
    method=$(detect_install_method)

    echo -e "${BLUE}[METHOD]${NC}  Using: ${BOLD}${method}${NC}" >&2
    echo "" >&2

    # Confirmation
    if ! $NO_PROMPT && [[ "$NO_PROMPT" != "1" ]]; then
        if ! confirm "Proceed with installation?"; then
            echo -e "\n${YELLOW}Installation cancelled.${NC}" >&2
            exit 0
        fi
        echo "" >&2
    fi

    # Step 3: Install
    case "$method" in
        pipx)  install_with_pipx || { print_failure; exit 1; } ;;
        pip)   install_with_pip  || { print_failure; exit 1; } ;;
        *)     log_error "Unknown method: $method"; exit 1 ;;
    esac

    # Step 4: Verify
    verify_installation

    # Success
    print_success
}

# ═══════════════════════════════════════════════════════════════════════════
# 🏁 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

trap 'echo -e "\n${RED}Installation interrupted.${NC}\n" >&2; exit 130' INT TERM

main "$@"