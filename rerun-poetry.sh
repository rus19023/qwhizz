#!/bin/bash

###############################################################################
# rerun-poetry.sh
# QWhizz startup script with Poetry, linting, and security checks
# Usage: ./rerun-poetry.sh [--skip-checks] [--dev]
###############################################################################

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"
POETRY_LOCK_PATH="${PROJECT_ROOT}/poetry.lock"
LAST_CHECK_FILE="${PROJECT_ROOT}/.last_check"
CHECK_INTERVAL_SECONDS=$((24 * 3600))  # 24 hours
SKIP_CHECKS=false
DEV_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_poetry_installed() {
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry is not installed"
        echo "Install it with: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    log_success "Poetry found: $(poetry --version)"
}

check_python_version() {
    local required_major=3
    local required_minor=12
    local current_version=$(python3 --version 2>&1 | awk '{print $2}')
    local current_major=$(echo "$current_version" | cut -d. -f1)
    local current_minor=$(echo "$current_version" | cut -d. -f2)
    
    if [[ $current_major -lt $required_major ]] || \
       [[ $current_major -eq $required_major && $current_minor -lt $required_minor ]]; then
        log_error "Python ${required_major}.${required_minor}+ required (found $current_version)"
        log_error "See PYTHON_UPGRADE.md for upgrade instructions"
        exit 1
    fi
    log_success "Python $current_version (required: ${required_major}.${required_minor}+)"
}

check_secrets_leaks() {
    log_info "Checking for hardcoded secrets..."
    
    if grep -r "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|MONGODB_URI\|password.*=" \
        --include="*.py" "${PROJECT_ROOT}/app" 2>/dev/null | grep -v ".example" | grep -v "secrets.toml.example" > /dev/null; then
        log_warn "Potential hardcoded secrets detected in source files"
        log_warn "Ensure all secrets are in secrets.toml (not committed)"
    else
        log_success "No obvious hardcoded secrets found"
    fi
}

should_run_checks() {
    if [[ "$SKIP_CHECKS" == "true" ]]; then
        log_warn "Skipping dependency and security checks (--skip-checks)"
        return 1
    fi
    
    if [[ ! -f "$LAST_CHECK_FILE" ]]; then
        return 0
    fi
    
    local last_check=$(cat "$LAST_CHECK_FILE")
    local current_time=$(date +%s)
    local time_elapsed=$((current_time - last_check))
    
    if [[ $time_elapsed -gt $CHECK_INTERVAL_SECONDS ]]; then
        return 0
    fi
    
    log_info "Checks run recently (last check: $((time_elapsed / 3600))h ago). Use --skip-checks to skip."
    return 1
}

run_checks() {
    log_info "Running dependency and security checks..."
    
    # deptry: find unused/missing dependencies
    if command -v deptry &> /dev/null; then
        log_info "Running deptry (dependency analysis)..."
        if deptry check --fail-exit-code 1 2>/dev/null; then
            log_success "Dependency check passed"
        else
            log_warn "Deptry found issues (review above)"
        fi
    else
        log_warn "deptry not installed (install with: poetry add --group dev deptry)"
    fi
    
    # pip-audit: scan for known CVEs
    if command -v pip-audit &> /dev/null; then
        log_info "Running pip-audit (CVE scan)..."
        if pip-audit --skip-editable 2>/dev/null; then
            log_success "CVE scan passed"
        else
            log_warn "pip-audit found vulnerabilities (review above)"
        fi
    else
        log_warn "pip-audit not installed (install with: poetry add --group dev pip-audit)"
    fi
    
    # Check for secrets
    check_secrets_leaks
    
    # Update timestamp
    date +%s > "$LAST_CHECK_FILE"
    log_success "Checks complete"
}

install_dependencies() {
    log_info "Installing dependencies with Poetry..."
    
    if [[ "$DEV_MODE" == "true" ]]; then
        poetry install --with dev
        log_success "Installed all dependencies (dev mode)"
    else
        poetry install --without dev
        log_success "Installed production dependencies"
    fi
}

run_app() {
    local app="${1:-}"
    
    if [[ -z "$app" ]]; then
        echo ""
        log_info "Available apps:"
        for d in "${PROJECT_ROOT}/apps"/*/; do
            echo "  - $(basename "$d")"
        done
        echo ""
        log_error "Usage: ./rerun-poetry.sh --app gesci205"
        exit 1
    fi
    
    local app_path="${PROJECT_ROOT}/apps/${app}"
    
    if [[ ! -d "$app_path" ]]; then
        log_error "App '${app}' not found in apps/"
        exit 1
    fi
    
    # Find the entry point
    local entry=""
    for f in runapp.py main.py "${app}.py"; do
        if [[ -f "${app_path}/${f}" ]]; then
            entry="${app_path}/${f}"
            break
        fi
    done
    
    if [[ -z "$entry" ]]; then
        log_error "No entry point found in apps/${app}/ (tried runapp.py, main.py, ${app}.py)"
        exit 1
    fi
    
    log_info "Starting ${app} from ${entry}..."
    cd "${PROJECT_ROOT}"
    poetry run streamlit run "$entry"
}

###############################################################################
# Parse Arguments
###############################################################################

APP_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --app)
            APP_NAME="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Usage: ./rerun-poetry.sh [OPTIONS]

Options:
  --app NAME       App to run (required). Must match a folder name inside apps/
  --skip-checks    Skip dependency and security checks
  --dev            Install dev dependencies
  --help           Show this help message

Examples:
  ./rerun-poetry.sh --app gesci205
  ./rerun-poetry.sh --app mandarin --skip-checks
  ./rerun-poetry.sh --app qwhizz --dev
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

###############################################################################
# Main Flow
###############################################################################

echo ""
log_info "QWhizz Startup Script"
log_info "====================="
echo ""

check_poetry_installed
check_python_version

# Run periodic checks if due
if should_run_checks; then
    run_checks
fi

# Install or update dependencies
if [[ ! -d "$VENV_PATH" ]] || [[ "$DEV_MODE" == "true" ]]; then
    install_dependencies
else
    log_info "Virtual environment already exists, skipping install"
    log_info "(Run with --dev to update/add dev dependencies)"
fi

echo ""
log_success "Setup complete!"
echo ""

# Run the app
run_app "$APP_NAME"