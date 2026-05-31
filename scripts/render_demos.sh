#!/usr/bin/env bash
# Re-render the demo catalog GIFs in assets/ via vhs. Run from anywhere — paths are repo-relative.
set -euo pipefail
cd "$(dirname "$0")/.."

# Pin Python so uvx resolves the latest published release cleanly, not a stale cached env on the default interpreter.
export UV_PYTHON=3.13
uvx goodreads-user-scraper --help >/dev/null 2>&1   # warm the env so recordings don't capture a first-run download

echo "Rendering deterministic demo (no network)…"
vhs assets/demo-nothing-to-do.tape

echo "Rendering live demos (these hit Goodreads — space out re-renders to avoid rate limiting)…"
vhs assets/demo-no-cookie.tape
echo "demo-invalid-cookie is non-deterministic (depends on Goodreads' response to a junk cookie) — verify the GIF."
vhs assets/demo-invalid-cookie.tape

if [ -f .goodreads-cookie ]; then
  echo "Rendering the hero full-scrape demo (uses .goodreads-cookie)…"
  vhs assets/demo-full.tape
else
  echo "Skipping demo-full.tape (full scrape): no .goodreads-cookie in the repo root."
fi
