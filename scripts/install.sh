#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: $PYTHON not found."
  echo "Install Python first, e.g. with: brew install python"
  exit 1
fi

"$PYTHON" -m venv .venv

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip setuptools
python -m pip install -e ".[dev]"

pre-commit install

echo "Installed successfully."
echo "Activate the environment with: source .venv/bin/activate"
echo "Then run: goodreads-user-scraper --help"
