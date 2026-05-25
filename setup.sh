#!/usr/bin/env bash
set -euo pipefail

MIN_PYTHON_VERSION="3.10"
VENV_DIR=".venv"
SKIP_PYTHON_INSTALL=0
FORCE_RECREATE_VENV=0
DRY_RUN=0

log_step() {
  echo "[setup] $1"
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log_step "[dry-run] $*"
    return 0
  fi
  "$@"
}

version_ge() {
  local current="$1"
  local minimum="$2"
  local py_cmd="${3:-python3}"
  "$py_cmd" - <<'PY' "$current" "$minimum"
import sys

def normalize(v):
    parts = []
    for p in v.split('.'):
        try:
            parts.append(int(p))
        except ValueError:
            # Keep only numeric prefix like "3rc1" -> 3
            num = ''.join(ch for ch in p if ch.isdigit())
            parts.append(int(num) if num else 0)
    return tuple(parts)

current = normalize(sys.argv[1])
minimum = normalize(sys.argv[2])
sys.exit(0 if current >= minimum else 1)
PY
}

get_python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  return 1
}

install_python_linux() {
  log_step "Python not found or version too low. Trying package manager install..."

  local sudo_cmd=""
  if [[ "${EUID:-$(id -u)}" -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
    sudo_cmd="sudo"
  fi

  if command -v apt-get >/dev/null 2>&1; then
    run_cmd ${sudo_cmd:+$sudo_cmd} apt-get update
    run_cmd ${sudo_cmd:+$sudo_cmd} apt-get install -y python3 python3-venv python3-pip
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    run_cmd ${sudo_cmd:+$sudo_cmd} dnf install -y python3 python3-pip
    return 0
  fi

  if command -v yum >/dev/null 2>&1; then
    run_cmd ${sudo_cmd:+$sudo_cmd} yum install -y python3 python3-pip
    return 0
  fi

  if command -v zypper >/dev/null 2>&1; then
    run_cmd ${sudo_cmd:+$sudo_cmd} zypper --non-interactive install python3 python3-pip
    return 0
  fi

  if command -v pacman >/dev/null 2>&1; then
    run_cmd ${sudo_cmd:+$sudo_cmd} pacman -Sy --noconfirm python python-pip
    return 0
  fi

  echo "No supported package manager found. Please install Python >= ${MIN_PYTHON_VERSION} manually." >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-python-version)
      MIN_PYTHON_VERSION="$2"
      shift 2
      ;;
    --venv-dir)
      VENV_DIR="$2"
      shift 2
      ;;
    --skip-python-install)
      SKIP_PYTHON_INSTALL=1
      shift
      ;;
    --force-recreate-venv)
      FORCE_RECREATE_VENV=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./setup.sh [options]

Options:
  --min-python-version <version>   Minimum Python version (default: 3.10)
  --venv-dir <dir>                 Virtualenv directory (default: .venv)
  --skip-python-install            Do not auto-install Python
  --force-recreate-venv            Recreate virtualenv if exists
  --dry-run                        Print commands only
  -h, --help                       Show help
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
log_step "Working directory: $SCRIPT_DIR"

PY_CMD=""
if PY_CMD="$(get_python_cmd)"; then
  PY_VER="$($PY_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
  if ! version_ge "$PY_VER" "$MIN_PYTHON_VERSION" "$PY_CMD"; then
    PY_CMD=""
  fi
fi

if [[ -z "$PY_CMD" ]]; then
  if [[ "$SKIP_PYTHON_INSTALL" -eq 1 ]]; then
    echo "Python >= ${MIN_PYTHON_VERSION} is required, but was not found." >&2
    exit 1
  fi

  install_python_linux
  PY_CMD="$(get_python_cmd)"
  PY_VER="$($PY_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
  if ! version_ge "$PY_VER" "$MIN_PYTHON_VERSION" "$PY_CMD"; then
    echo "Python install did not meet minimum version ${MIN_PYTHON_VERSION}." >&2
    exit 1
  fi
fi

log_step "Using Python: ${PY_CMD} (version ${PY_VER})"

VENV_PATH="${SCRIPT_DIR}/${VENV_DIR}"
if [[ -d "$VENV_PATH" && "$FORCE_RECREATE_VENV" -eq 1 ]]; then
  log_step "Removing old virtual environment: $VENV_PATH"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    rm -rf "$VENV_PATH"
  fi
fi

if [[ ! -d "$VENV_PATH" ]]; then
  log_step "Creating virtual environment at $VENV_PATH"
  run_cmd "$PY_CMD" -m venv "$VENV_PATH"
else
  log_step "Virtual environment already exists: $VENV_PATH"
fi

VENV_PYTHON="${VENV_PATH}/bin/python"
if [[ "$DRY_RUN" -eq 0 && ! -x "$VENV_PYTHON" ]]; then
  echo "Virtual environment python not found: $VENV_PYTHON" >&2
  exit 1
fi

REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "requirements.txt not found in project root: $REQUIREMENTS_FILE" >&2
  exit 1
fi

log_step "Upgrading pip/setuptools/wheel"
run_cmd "$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

log_step "Installing dependencies from requirements.txt"
run_cmd "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"

log_step "Setup complete."
log_step "Activate venv with: source ${VENV_DIR}/bin/activate"
log_step "Run tests with: pytest '@tests_to_run.txt'"
