#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: $PYTHON not found."
  echo "Run scripts/install.sh first."
  exit 1
fi

if [ -f .goodreads-cookie ]; then
  "$PYTHON" -m scraper --user_id 54739262 --output_dir goodreads-data --cookie_file .goodreads-cookie
else
  "$PYTHON" -m scraper --user_id 54739262 --output_dir goodreads-data
fi
