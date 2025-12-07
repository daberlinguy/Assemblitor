#!/usr/bin/env bash
set -euo pipefail

# Simple packager for the Qt app. It prefers uv if available, otherwise falls back to python -m pip.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if command -v uv >/dev/null 2>&1; then
  echo "Using uv to install build dependencies"
  INSTALL_CMD=(uv pip install)
  PYTHON_BIN="python3"
else
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python not found in PATH" >&2
    exit 1
  fi
  INSTALL_CMD=($PYTHON_BIN -m pip install)
fi

"${INSTALL_CMD[@]}" --upgrade pyinstaller

"${PYTHON_BIN}" -m PyInstaller --noconfirm --windowed --clean \
  --name Assemblitor \
  --add-data "program:program" \
  --add-data "profile:profile" \
  --add-data "fonts:fonts" \
  Assemblitor.pyw

echo "\nBuild complete. Binaries are in dist/Assemblitor/"

# Ensure launcher path is available and sourced for current shell.
ensure_path() {
  local shell_rc="$1"
  local line='export PATH="$HOME/.local/bin:$PATH"'
  if [ -f "$shell_rc" ]; then
    if ! grep -F "$line" "$shell_rc" >/dev/null 2>&1; then
      printf '\n# Assemblitor launcher\n%s\n' "$line" >> "$shell_rc"
    fi
  else
    printf '# Assemblitor launcher\n%s\n' "$line" > "$shell_rc"
  fi
}

ensure_path "$HOME/.bashrc"
ensure_path "$HOME/.zshrc"

# Source common shells so the PATH change is active immediately when run interactively.
if [ -n "${BASH_SOURCE:-}" ] && [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.bashrc"
fi
if command -v zsh >/dev/null 2>&1 && [ -f "$HOME/.zshrc" ]; then
  # shellcheck disable=SC1090
  zsh -c "source $HOME/.zshrc; :"
fi
