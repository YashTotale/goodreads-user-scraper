# Shelf Cookie Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore Goodreads shelf scraping by adding session-cookie authentication, switch the HTTP layer from `urllib` to `requests`, and fold in a set of bundled cleanups (#1–#10 from the spec).

**Architecture:** A new `scraper/http.py` module owns a single `requests.Session` configured once at startup. Cookie is resolved in `__main__.py` from `--cookie` > `GOODREADS_COOKIE` env var > `--cookie_file`. Shelf scraping is gated on `http.has_cookie()`; invalid cookies are detected via a `<div id="third_party_sign_in">` marker on the profile page and exit fast.

**Tech Stack:** Python 3.10+, `requests`, `beautifulsoup4`, argparse, pathlib.

**Spec:** `docs/superpowers/specs/2026-05-27-shelf-cookie-auth-design.md`

**No new test suite** — unit tests are tracked as a separate follow-up issue (out of scope here). Verification is via manual smoke tests through `scripts/test.sh`.

**Commit policy** — Per user preference, the executor does **not** commit during plan execution. Pause after the final task and let the user review the accumulated uncommitted diff. The user decides commit boundaries themselves.

---

## File Structure

**Files created:**
- `scraper/http.py` — single `requests.Session`, cookie-aware. Exports `init_session(cookie)`, `has_cookie()`, `get_soup(url)`.

**Files modified:**
- `scraper/__main__.py` — new `--cookie` and `--cookie_file` flags, cookie resolution, `init_session` call. `type=bool` flags fixed to `action="store_true"`. `--output_dir` becomes `type=Path`.
- `scraper/shelves.py` — `urlopen` → `http.get_soup`. Cookie-missing skip with verbose warning. Invalid-cookie detection. Per-book `try/except`. `get_shelf_url` renamed to `fetch_shelf_page`. Context managers for file I/O. `pathlib.Path` paths.
- `scraper/books.py` — `urlopen` → `http.get_soup`. Delete commented-out functions + stale source attribution. Return `None` (not `""`) for missing numeric fields.
- `scraper/user.py` — `urlopen` → `http.get_soup`. Context manager for file I/O. `pathlib.Path` paths.
- `scraper/author.py` — `urlopen` → `http.get_soup`.
- `setup.py` — add `requests` to `install_requires`; update `description`.
- `README.md` — new Authentication section, document new CLI flags, update Troubleshooting.

---

## Task 1: Create `scraper/http.py` and add `requests` dependency

**Files:**
- Create: `scraper/http.py`
- Modify: `setup.py`

- [ ] **Step 1.1: Create `scraper/http.py`**

```python
"""Shared HTTP session. Optionally carries a Goodreads cookie."""
from bs4 import BeautifulSoup
import requests

DEFAULT_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_session: requests.Session | None = None
_has_cookie: bool = False


def init_session(cookie: str | None) -> None:
    global _session, _has_cookie
    _session = requests.Session()
    _session.headers["User-Agent"] = USER_AGENT
    if cookie:
        _session.headers["Cookie"] = cookie
        _has_cookie = True


def has_cookie() -> bool:
    return _has_cookie


def get_soup(url: str) -> BeautifulSoup:
    assert _session is not None, "init_session() must be called first"
    response = _session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")
```

- [ ] **Step 1.2: Update `setup.py`** — add `requests` dependency and update description

Find at `setup.py:14`:
```python
    description="Scrape user data from Goodreads",
```
Replace with:
```python
    description="Scrape Goodreads User Data: Profile, Book Shelves, Books, Authors",
```

Find at `setup.py:42`:
```python
    install_requires=["beautifulsoup4"],
```
Replace with:
```python
    install_requires=["beautifulsoup4", "requests"],
```

- [ ] **Step 1.3: Install the new dependency into the venv**

Run: `source .venv/bin/activate && python -m pip install -e .`
Expected: `requests` installed without errors.

- [ ] **Step 1.4: Sanity-check the module imports**

Run: `source .venv/bin/activate && python -c "from scraper import http; http.init_session(None); print(http.has_cookie())"`
Expected: prints `False`.

---

## Task 2: Migrate all call sites from `urllib` to `http.get_soup`

**Files:**
- Modify: `scraper/user.py`
- Modify: `scraper/shelves.py`
- Modify: `scraper/books.py`
- Modify: `scraper/author.py`

- [ ] **Step 2.1: `scraper/user.py` — replace urllib with http.get_soup**

Find at `scraper/user.py:1-6`:
```python
from argparse import Namespace
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
```
Replace with:
```python
from argparse import Namespace
import json
import re

from bs4 import BeautifulSoup

from scraper import http
```

Find at `scraper/user.py:35-37`:
```python
    url = "https://www.goodreads.com/user/show/" + user_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")
```
Replace with:
```python
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)
```

- [ ] **Step 2.2: `scraper/shelves.py` — replace urllib with http.get_soup**

Find at `scraper/shelves.py:1-6`:
```python
from argparse import Namespace
import json
from urllib.request import urlopen
import os
from bs4 import BeautifulSoup
import re
```
Replace with:
```python
from argparse import Namespace
import json
import os
import re

from scraper import books, http
```

Remove the existing `from scraper import books` line that becomes redundant after the merge above (currently at `scraper/shelves.py:8`).

Find in `get_shelf_url` (at `scraper/shelves.py:21-32`):
```python
def get_shelf_url(user_id, shelf, page):
    url = (
        "https://www.goodreads.com/review/list/"
        + user_id
        + "?shelf="
        + shelf
        + "&page="
        + str(page)
        + "&print=true"
    )
    source = urlopen(url)
    return BeautifulSoup(source, "html.parser")
```
Replace with:
```python
def get_shelf_url(user_id, shelf, page):
    url = (
        "https://www.goodreads.com/review/list/"
        + user_id
        + "?shelf="
        + shelf
        + "&page="
        + str(page)
        + "&print=true"
    )
    return http.get_soup(url)
```

Find in `get_all_shelves` (at `scraper/shelves.py:119-121`):
```python
    url = "https://www.goodreads.com/user/show/" + user_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")
```
Replace with:
```python
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)
```

- [ ] **Step 2.3: `scraper/books.py` — replace urllib with http.get_soup**

Find at `scraper/books.py:4-9`:
```python
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from argparse import Namespace

from scraper import author
```
Replace with:
```python
import re
from argparse import Namespace

from bs4 import BeautifulSoup

from scraper import author, http
```

Find at `scraper/books.py:144-146`:
```python
    url = "https://www.goodreads.com/book/show/" + book_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")
```
Replace with:
```python
    url = "https://www.goodreads.com/book/show/" + book_id
    soup = http.get_soup(url)
```

- [ ] **Step 2.4: `scraper/author.py` — replace urllib with http.get_soup**

Find at `scraper/author.py:1-3`:
```python
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
```
Replace with:
```python
import re

from bs4 import BeautifulSoup

from scraper import http
```

Find at `scraper/author.py:26-28`:
```python
    url = "https://www.goodreads.com/author/show/" + author_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")
```
Replace with:
```python
    url = "https://www.goodreads.com/author/show/" + author_id
    soup = http.get_soup(url)
```

- [ ] **Step 2.5: Grep for stragglers**

Run: `grep -rn "urlopen\|urllib" scraper/`
Expected: no matches.

---

## Task 3: Fix argparse `type=bool` bug and convert `--output_dir` to `Path`

**Files:**
- Modify: `scraper/__main__.py`
- Modify: `scraper/user.py`
- Modify: `scraper/shelves.py`

- [ ] **Step 3.1: Fix argparse flags and `--output_dir`** in `scraper/__main__.py`

Find at `scraper/__main__.py:1-3`:
```python
import argparse
import os

from scraper import shelves
from scraper import user
```
Replace with:
```python
import argparse
from pathlib import Path

from scraper import shelves, user
```

Find at `scraper/__main__.py:13-28`:
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="goodreads-data")
    parser.add_argument("--skip_user_info", type=bool, default=False)
    parser.add_argument("--skip_shelves", type=bool, default=False)
    parser.add_argument("--skip_authors", type=bool, default=False)

    args = parser.parse_args()

    args.output_dir = (
        args.output_dir if args.output_dir.endswith("/") else args.output_dir + "/"
    )

    os.makedirs(args.output_dir, exist_ok=True)
    scrape_user(args)
```
Replace with:
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=Path, default=Path("goodreads-data"))
    parser.add_argument("--skip_user_info", action="store_true")
    parser.add_argument("--skip_shelves", action="store_true")
    parser.add_argument("--skip_authors", action="store_true")

    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scrape_user(args)
```

- [ ] **Step 3.2: `scraper/user.py` — switch to Path operations**

Find at `scraper/user.py:34`:
```python
    output_file: str = args.output_dir + "user.json"
```
Replace with:
```python
    output_file = args.output_dir / "user.json"
```

- [ ] **Step 3.3: `scraper/shelves.py` — switch to Path operations**

Find at `scraper/shelves.py:62-63` (inside `get_shelf`):
```python
    user_id: str = args.user_id
    output_dir: str = args.output_dir + "books/"
```
Replace with:
```python
    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
```

Find at `scraper/shelves.py:79`:
```python
            file_path = output_dir + book_id + ".json"
```
Replace with:
```python
            file_path = output_dir / f"{book_id}.json"
```

Find at `scraper/shelves.py:117-118` (inside `get_all_shelves`):
```python
    user_id: str = args.user_id
    output_dir: str = args.output_dir + "books/"
```
Replace with:
```python
    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
```

Find at `scraper/shelves.py:123`:
```python
    os.makedirs(output_dir, exist_ok=True)
```
Replace with:
```python
    output_dir.mkdir(parents=True, exist_ok=True)
```

(The `os` import in `scraper/shelves.py` is still used by `os.path.exists(file_path)` at line 85. Replace that call too:)

Find at `scraper/shelves.py:85`:
```python
            if os.path.exists(file_path):
```
Replace with:
```python
            if file_path.exists():
```

Then remove `import os` from `scraper/shelves.py:3` since it is no longer needed.

- [ ] **Step 3.4: Sanity-check argparse behavior**

Run: `source .venv/bin/activate && python -m scraper --user_id 1 --skip_user_info --skip_shelves --skip_authors --output_dir /tmp/gr-test 2>&1 | head -5`
Expected: exits cleanly without errors (no actual scraping happens because all skip flags are set; only mkdir runs).

Run: `source .venv/bin/activate && python -m scraper --user_id 1 --skip_shelves True 2>&1 | head -5`
Expected: argparse error mentioning unrecognized arguments. (Demonstrates the breaking change is now in effect.)

---

## Task 4: Add cookie CLI flags and resolution logic

**Files:**
- Modify: `scraper/__main__.py`

- [ ] **Step 4.1: Add cookie flags, resolution, and `init_session` call**

Replace the entire contents of `scraper/__main__.py` (the current main + scrape_user) with:

```python
import argparse
import os
import sys
from pathlib import Path

from scraper import http, shelves, user


def scrape_user(args: argparse.Namespace):
    user.get_user_info(args)
    shelves.get_all_shelves(args)


def resolve_cookie(args: argparse.Namespace) -> str | None:
    if args.cookie:
        return args.cookie
    env = os.environ.get("GOODREADS_COOKIE")
    if env:
        return env
    if args.cookie_file:
        path = Path(args.cookie_file)
        if not path.exists():
            sys.exit(f"❌ --cookie_file path does not exist: {path}")
        return path.read_text().strip()
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=Path, default=Path("goodreads-data"))
    parser.add_argument("--skip_user_info", action="store_true")
    parser.add_argument("--skip_shelves", action="store_true")
    parser.add_argument("--skip_authors", action="store_true")
    parser.add_argument("--cookie", type=str, default=None)
    parser.add_argument("--cookie_file", type=str, default=None)

    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    cookie = resolve_cookie(args)
    http.init_session(cookie)

    scrape_user(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4.2: Verify resolution precedence manually**

Run (flag wins over env): `source .venv/bin/activate && GOODREADS_COOKIE=env-value python -c "
import argparse, os
os.environ['GOODREADS_COOKIE'] = 'env-value'
from scraper.__main__ import resolve_cookie
ns = argparse.Namespace(cookie='flag-value', cookie_file=None)
print(resolve_cookie(ns))
"`
Expected: prints `flag-value`.

Run (env wins over file when flag absent): `source .venv/bin/activate && echo 'file-value' > /tmp/gr-cookie.txt && GOODREADS_COOKIE=env-value python -c "
import argparse, os
os.environ['GOODREADS_COOKIE'] = 'env-value'
from scraper.__main__ import resolve_cookie
ns = argparse.Namespace(cookie=None, cookie_file='/tmp/gr-cookie.txt')
print(resolve_cookie(ns))
"`
Expected: prints `env-value`.

Run (file wins when flag + env absent): `source .venv/bin/activate && echo 'file-value' > /tmp/gr-cookie.txt && unset GOODREADS_COOKIE && python -c "
import argparse, os
os.environ.pop('GOODREADS_COOKIE', None)
from scraper.__main__ import resolve_cookie
ns = argparse.Namespace(cookie=None, cookie_file='/tmp/gr-cookie.txt')
print(resolve_cookie(ns))
"`
Expected: prints `file-value`.

Run (missing file errors): `source .venv/bin/activate && unset GOODREADS_COOKIE && python -c "
import argparse, os
os.environ.pop('GOODREADS_COOKIE', None)
from scraper.__main__ import resolve_cookie
ns = argparse.Namespace(cookie=None, cookie_file='/tmp/does-not-exist.txt')
print(resolve_cookie(ns))
"`
Expected: exits with `❌ --cookie_file path does not exist: /tmp/does-not-exist.txt` on stderr.

---

## Task 5: Gate shelf scraping on `http.has_cookie()` with verbose warning

**Files:**
- Modify: `scraper/shelves.py`

- [ ] **Step 5.1: Add cookie-missing warning in `get_all_shelves`**

Find at `scraper/shelves.py` `get_all_shelves` (the version after Task 3, starting at the current `if args.skip_shelves: return`):
```python
def get_all_shelves(args: Namespace):
    if args.skip_shelves:
        return

    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)

    output_dir.mkdir(parents=True, exist_ok=True)
```
Replace with:
```python
def get_all_shelves(args: Namespace):
    if args.skip_shelves:
        return

    if not http.has_cookie():
        print(
            "⚠️  Skipping shelves: Goodreads now requires login to view shelf data.\n"
            "   To scrape shelves, provide your Goodreads session cookie via one of:\n"
            "     --cookie \"<cookie string>\"\n"
            "     GOODREADS_COOKIE=<cookie string>   (environment variable)\n"
            "     --cookie_file <path-to-file>\n"
            "   See the README for how to grab the cookie from your browser.\n"
            "   Pass --skip_shelves to suppress this message."
        )
        return

    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)

    output_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 5.2: Smoke check the warning fires**

Run: `source .venv/bin/activate && unset GOODREADS_COOKIE && python -m scraper --user_id 54739262 --output_dir /tmp/gr-test --skip_user_info --skip_authors 2>&1 | tail -10`
Expected: the `⚠️ Skipping shelves` block prints; process exits 0.

---

## Task 6: Detect invalid/expired cookie and exit fast

**Files:**
- Modify: `scraper/shelves.py`

- [ ] **Step 6.1: Add `detect_logged_out` helper and exit on detection**

Find at the top of `scraper/shelves.py` (after the existing imports) the `RATING_STARS_DICT` definition. Add `sys` to the top-of-file imports:

Find at `scraper/shelves.py:1-5` (after Task 2's import rewrite):
```python
from argparse import Namespace
import json
import re

from scraper import books, http
```
Replace with:
```python
from argparse import Namespace
import json
import re
import sys

from bs4 import BeautifulSoup

from scraper import books, http
```

Add this helper near the top of `scraper/shelves.py` (immediately after `RATING_STARS_DICT`):

```python
def detect_logged_out(soup: BeautifulSoup) -> bool:
    return soup.find("div", {"id": "third_party_sign_in"}) is not None
```

Find in `get_all_shelves` (the version after Task 5):
```python
    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)

    output_dir.mkdir(parents=True, exist_ok=True)
```
Replace with:
```python
    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)

    if detect_logged_out(soup):
        sys.exit(
            "❌ Cookie appears invalid or expired. Re-grab the Cookie header "
            "value from your browser DevTools and try again."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 6.2: Smoke check invalid-cookie path**

Run: `source .venv/bin/activate && GOODREADS_COOKIE='bogus=value' python -m scraper --user_id 54739262 --output_dir /tmp/gr-test --skip_user_info --skip_authors; echo "exit=$?"`
Expected: prints the `❌ Cookie appears invalid or expired` message; `exit=1`.

(If Goodreads instead serves the profile page even with a bogus cookie — i.e., doesn't redirect to sign-in — this smoke test won't trip detection. That's acceptable; the real verification is that a known-expired cookie reproduces it.)

---

## Task 7: Context managers for file I/O in `shelves.py` and `user.py`

**Files:**
- Modify: `scraper/shelves.py`
- Modify: `scraper/user.py`

- [ ] **Step 7.1: `scraper/shelves.py` — file read in `get_shelf`**

Find in `get_shelf` (state after Task 3):
```python
            if file_path.exists():
                file = open(file_path, "r")
                book = json.load(file)
                if shelf not in book["shelves"]:
                    book["shelves"].append(shelf)
                    print("✅ Updated " + book_id)
                    changed = True
                file.close()
```
Replace with:
```python
            if file_path.exists():
                with open(file_path, "r") as file:
                    book = json.load(file)
                if shelf not in book["shelves"]:
                    book["shelves"].append(shelf)
                    print("✅ Updated " + book_id)
                    changed = True
```

- [ ] **Step 7.2: `scraper/shelves.py` — file write in `get_shelf`**

Find:
```python
            if changed:
                # Write the json file for the book
                file = open(file_path, "w")
                json.dump(book, file, indent=2)
                file.close()
```
Replace with:
```python
            if changed:
                with open(file_path, "w") as file:
                    json.dump(book, file, indent=2)
```

- [ ] **Step 7.3: `scraper/user.py` — file write**

Find at `scraper/user.py:47-49`:
```python
    file = open(output_file, "w")
    json.dump(data, file, indent=2)
    file.close()
```
Replace with:
```python
    with open(output_file, "w") as file:
        json.dump(data, file, indent=2)
```

---

## Task 8: Per-book `try/except` in `get_shelf`

**Files:**
- Modify: `scraper/shelves.py`

- [ ] **Step 8.1: Wrap row loop with resilience**

Find the entire `for book_row in book_rows:` block in `get_shelf` (state after Tasks 2, 3, and 7):
```python
        # Loop through all books in the page
        for book_row in book_rows:
            book_id = get_id(book_row)
            file_path = output_dir / f"{book_id}.json"

            book = None
            changed = False

            # If the book has already been scraped, just add the shelf
            if file_path.exists():
                with open(file_path, "r") as file:
                    book = json.load(file)
                if shelf not in book["shelves"]:
                    book["shelves"].append(shelf)
                    print("✅ Updated " + book_id)
                    changed = True
            # If not already scraped, scrape the book and add the shelf
            else:
                book = books.scrape_book(book_id, args)
                book["rating"] = get_rating(book_row)
                book["dates_read"] = get_dates_read(book_row)
                book["shelves"] = [shelf]
                print("🎉 Scraped " + book_id)
                changed = True

            if changed:
                with open(file_path, "w") as file:
                    json.dump(book, file, indent=2)
```
Replace with the same body wrapped in `try/except Exception as e`:
```python
        # Loop through all books in the page
        for book_row in book_rows:
            try:
                book_id = get_id(book_row)
                file_path = output_dir / f"{book_id}.json"

                book = None
                changed = False

                # If the book has already been scraped, just add the shelf
                if file_path.exists():
                    with open(file_path, "r") as file:
                        book = json.load(file)
                    if shelf not in book["shelves"]:
                        book["shelves"].append(shelf)
                        print("✅ Updated " + book_id)
                        changed = True
                # If not already scraped, scrape the book and add the shelf
                else:
                    book = books.scrape_book(book_id, args)
                    book["rating"] = get_rating(book_row)
                    book["dates_read"] = get_dates_read(book_row)
                    book["shelves"] = [shelf]
                    print("🎉 Scraped " + book_id)
                    changed = True

                if changed:
                    with open(file_path, "w") as file:
                        json.dump(book, file, indent=2)
            except Exception as e:
                print(f"⚠️  Skipped book on page {page}: {e}")
```

---

## Task 9: Books cleanup — dead code + consistent `None` returns + stale attribution

**Files:**
- Modify: `scraper/books.py`

- [ ] **Step 9.1: Delete stale source attribution at top of file**

Find at `scraper/books.py:1-3`:
```python
"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""
```
Delete those three lines entirely (so the file starts at the next `import` line).

- [ ] **Step 9.2: Delete commented-out `get_rating_distribution`**

Find at `scraper/books.py:12-23`:
```python
# def get_rating_distribution(soup: BeautifulSoup):
#     distribution = re.findall(r"renderRatingGraph\([\s]*\[[0-9,\s]+", str(soup))[0]
#     distribution = " ".join(distribution.split())
#     distribution = [int(c.strip()) for c in distribution.split("[")[1].split(",")]
#     distribution_dict = {
#         5: distribution[0],
#         4: distribution[1],
#         3: distribution[2],
#         2: distribution[3],
#         1: distribution[4],
#     }
#     return distribution_dict
```
Delete those lines entirely.

- [ ] **Step 9.3: Delete commented-out `get_series_name`**

Find at `scraper/books.py:110-118`:
```python
# def get_series_name(soup: BeautifulSoup):
#     title_section = soup.find("h1", {"data-testid": "bookTitle"}).parent
#     series_container = title_section.find("h3")

#     if series_container:
#         series_name = re.search(r"\((.*?)\)", series_container.find("a").text).group(1)
#         return series_name
#     else:
#         return None
```
Delete those lines entirely.

- [ ] **Step 9.4: Remove commented-out keys in `scrape_book` return dict**

Find in `scrape_book`:
```python
        "book_image": get_image(soup),
        # "book_series": get_series_name(soup),
        "book_series_uri": get_series_uri(soup),
```
Replace with:
```python
        "book_image": get_image(soup),
        "book_series_uri": get_series_uri(soup),
```

Find:
```python
        "average_rating": get_average_rating(soup),
        # "rating_distribution": get_rating_distribution(soup),
    }
```
Replace with:
```python
        "average_rating": get_average_rating(soup),
    }
```

- [ ] **Step 9.5: Return `None` (not `""`) for missing numeric fields**

Find at `scraper/books.py:47-54` (`get_average_rating`):
```python
def get_average_rating(soup: BeautifulSoup):
    average_rating = soup.find(
        "div", {"class": "RatingStatistics__rating"}
    ).text.strip()

    if average_rating:
        return float(average_rating)
    return ""
```
Replace with:
```python
def get_average_rating(soup: BeautifulSoup):
    average_rating = soup.find(
        "div", {"class": "RatingStatistics__rating"}
    ).text.strip()

    if average_rating:
        return float(average_rating)
    return None
```

Find at `scraper/books.py:57-65` (`get_num_reviews`):
```python
def get_num_reviews(soup: BeautifulSoup):
    num_reviews = soup.find("span", {"data-testid": "reviewsCount"})

    if num_reviews:
        num_reviews = re.search(
            r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_reviews.text.strip()
        ).group(1)
        return int(num_reviews.replace(",", ""))
    return ""
```
Replace the final `return ""` with `return None`.

Find at `scraper/books.py:68-76` (`get_num_ratings`):
```python
def get_num_ratings(soup: BeautifulSoup):
    num_ratings = soup.find("span", {"data-testid": "ratingsCount"})

    if num_ratings:
        num_ratings = re.search(
            r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_ratings.text.strip()
        ).group(1)
        return int(num_ratings.replace(",", ""))
    return ""
```
Replace the final `return ""` with `return None`.

---

## Task 10: Rename `get_shelf_url` → `fetch_shelf_page`

**Files:**
- Modify: `scraper/shelves.py`

- [ ] **Step 10.1: Rename the function and its single call site**

In `scraper/shelves.py`, change the function definition:

Find:
```python
def get_shelf_url(user_id, shelf, page):
```
Replace with:
```python
def fetch_shelf_page(user_id, shelf, page):
```

Find in `get_shelf`:
```python
        soup = get_shelf_url(user_id, shelf, page)
```
Replace with:
```python
        soup = fetch_shelf_page(user_id, shelf, page)
```

Run: `grep -n "get_shelf_url" scraper/`
Expected: no matches.

---

## Task 11: README updates

**Files:**
- Modify: `README.md`

- [ ] **Step 11.1: Update the Contents table-of-contents**

Find in `README.md` the Contents block:
```markdown
## Contents <!-- omit in toc -->

- [Usage](#usage)
- [Arguments](#arguments)
  - [`--user_id`](#--user_id)
  - [`--output_dir`](#--output_dir)
  - [`--skip_user_info`](#--skip_user_info)
  - [`--skip_shelves`](#--skip_shelves)
  - [`--skip_authors`](#--skip_authors)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Publishing](#publishing)
```
Replace with:
```markdown
## Contents <!-- omit in toc -->

- [Usage](#usage)
- [Arguments](#arguments)
  - [`--user_id`](#--user_id)
  - [`--output_dir`](#--output_dir)
  - [`--skip_user_info`](#--skip_user_info)
  - [`--skip_shelves`](#--skip_shelves)
  - [`--skip_authors`](#--skip_authors)
  - [`--cookie`](#--cookie)
  - [`--cookie_file`](#--cookie_file)
- [Authentication](#authentication)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Publishing](#publishing)
```

- [ ] **Step 11.2: Add `--cookie` and `--cookie_file` argument entries**

Find at the end of the Arguments section (after `--skip_authors`):
```markdown
### `--skip_authors`

- **Description**: Whether the script should skip scraping authors.
- **Required**: No
- **Default**: `False`

## Troubleshooting
```
Replace with:
```markdown
### `--skip_authors`

- **Description**: Whether the script should skip scraping authors.
- **Required**: No
- **Default**: `False`

### `--cookie`

- **Description**: Your Goodreads session cookie (the full `Cookie:` request-header value). Required for shelf scraping — see [Authentication](#authentication).
- **Required**: No
- **Default**: None

### `--cookie_file`

- **Description**: Path to a text file containing your Goodreads session cookie. Used only if `--cookie` is not passed and `GOODREADS_COOKIE` is not set.
- **Required**: No
- **Default**: None

## Authentication

Shelf scraping requires authentication — Goodreads now hides shelf data behind login. The other endpoints (profile, individual books, authors) still work anonymously.

### Getting your session cookie

1. Sign in to Goodreads in your browser.
2. Open DevTools (Cmd/Ctrl+Shift+I) and switch to the Network tab.
3. Refresh the page, then click any `goodreads.com` request in the list.
4. In the request Headers, find the `Cookie:` header and copy its full value.

### Passing the cookie

In order of precedence (first one set wins):

1. `--cookie "<cookie string>"`
2. `GOODREADS_COOKIE` environment variable
3. `--cookie_file <path-to-file>`

Cookies typically last several weeks. If you see a "Cookie appears invalid or expired" error, re-grab the cookie from your browser.

If no cookie is provided, shelf scraping is skipped with a warning. Pass `--skip_shelves` to suppress the warning.

## Troubleshooting
```

- [ ] **Step 11.3: Add a sub-bullet about cookie auth in Troubleshooting**

Find:
```markdown
## Troubleshooting

Ensure that your profile is viewable by anyone:

1. Navigate to the [Goodreads Account Settings](https://www.goodreads.com/user/edit) page
2. Click on the `Account & notifications` tab
3. In the `Privacy` section, under **Who Can View My Profile**, select "anyone". Save your account settings.
```
Replace with:
```markdown
## Troubleshooting

Ensure that your profile is viewable by anyone:

1. Navigate to the [Goodreads Account Settings](https://www.goodreads.com/user/edit) page
2. Click on the `Account & notifications` tab
3. In the `Privacy` section, under **Who Can View My Profile**, select "anyone". Save your account settings.

Shelf scraping requires a session cookie regardless of profile visibility — see [Authentication](#authentication).
```

---

## Task 12: Manual smoke test

**Files:** none (verification only)

- [ ] **Step 12.1: Run without cookie — anonymous path**

Run: `source .venv/bin/activate && unset GOODREADS_COOKIE && rm -rf goodreads-data && bash scripts/test.sh 2>&1 | tail -20`
Expected:
- User scrape succeeds (`👤 Scraped user`).
- Shelves block prints the verbose `⚠️  Skipping shelves...` warning.
- Process exits 0.
- `goodreads-data/user.json` exists; `goodreads-data/books/` does not.

- [ ] **Step 12.2: Run with valid cookie — full path**

Set `GOODREADS_COOKIE` to a freshly grabbed valid cookie (manual step — open DevTools → Network → copy `Cookie:` header value from a logged-in `goodreads.com` request).

Run: `source .venv/bin/activate && rm -rf goodreads-data && bash scripts/test.sh 2>&1 | tail -30`
Expected:
- User scrape succeeds.
- Each shelf prints `Scraping '<shelf>' shelf...`.
- Book pages get scraped (`🎉 Scraped <book_id>`).
- `goodreads-data/books/*.json` files exist; each contains `shelves`, `rating`, `dates_read` keys.

- [ ] **Step 12.3: Run with bogus cookie — invalid-cookie path**

Run: `source .venv/bin/activate && rm -rf goodreads-data && GOODREADS_COOKIE='_session_id2=clearly-invalid' bash scripts/test.sh; echo "exit=$?"`
Expected: prints `❌ Cookie appears invalid or expired...`; exit code `1`. (If Goodreads happens to serve the profile page even with the bogus cookie, detection won't trip — verify the path more reliably by clearing all cookies in your browser, signing out, and copying *those* cookies.)

---

## Task 13: Create follow-up GitHub issues

**Files:** none (GitHub work)

- [ ] **Step 13.1: Draft issue bodies and confirm with the user before pushing**

Per user preference (review before any push), do **not** run `gh issue create` automatically. Present the three issue titles + bodies below to the user and ask whether to push them.

**Issue 1: Add unit-test suite with HTML fixtures**

> Title: `Add unit tests with saved Goodreads HTML fixtures`
>
> Body:
> The current `scripts/test.sh` is a smoke test that hits live Goodreads — useful but doesn't catch parser regressions deterministically. Add a `pytest` suite that:
> - Saves real Goodreads HTML pages (profile, book, author, shelf) as fixtures under `tests/fixtures/`.
> - Mocks `requests` (e.g. via `responses` or a thin fake) so tests never hit the network.
> - Exercises each parser (`scraper/user.py`, `scraper/books.py`, `scraper/author.py`, `scraper/shelves.py`) against the fixtures.
> - Runs in CI via the existing `.github/workflows/integrate.yml`.

**Issue 2: Add type hints across `scraper/*.py`**

> Title: `Add type hints across scraper modules`
>
> Body:
> Most functions have unannotated parameters and return types. Add complete signatures (`def foo(soup: BeautifulSoup) -> str | None:`) across `scraper/user.py`, `scraper/books.py`, `scraper/author.py`, `scraper/shelves.py`, and `scraper/http.py`. Wire `mypy` (or `pyright`) into the pre-commit config so type drift is caught.

**Issue 3: Parameterize `scripts/test.sh` user_id**

> Title: `Parameterize scripts/test.sh user_id via env var`
>
> Body:
> `scripts/test.sh` currently hardcodes `--user_id 54739262`. Read it from an env var (e.g. `GOODREADS_USER_ID`) with the current hardcoded value as the default, so contributors can run the smoke test against their own profile without editing the script.

- [ ] **Step 13.2: After user approval, push the issues**

If the user approves, run (one issue at a time, confirming the URL each time):

```bash
gh issue create --title "Add unit tests with saved Goodreads HTML fixtures" --body-file <(cat <<'EOF'
The current `scripts/test.sh` is a smoke test that hits live Goodreads — useful but doesn't catch parser regressions deterministically. Add a `pytest` suite that:
- Saves real Goodreads HTML pages (profile, book, author, shelf) as fixtures under `tests/fixtures/`.
- Mocks `requests` (e.g. via `responses` or a thin fake) so tests never hit the network.
- Exercises each parser (`scraper/user.py`, `scraper/books.py`, `scraper/author.py`, `scraper/shelves.py`) against the fixtures.
- Runs in CI via the existing `.github/workflows/integrate.yml`.
EOF
)
```

Repeat similarly for Issues 2 and 3.

---

## Task 14: Final review (no commits)

**Files:** none (review only)

- [ ] **Step 14.1: Print the full uncommitted diff for the user**

Run: `git status && git diff`
Expected: shows all changes from Tasks 1–11. Confirm the file set matches the [File Structure](#file-structure) section.

- [ ] **Step 14.2: Hand off to the user for review and commit decisions**

Per user preference, the executor does not commit. Present a summary of what changed and let the user decide commit boundaries.

---

## Post-merge release (out of plan execution)

After the user merges the PR to `main`:

```bash
git checkout main && git pull
bash scripts/publish.sh major
```

This bumps `setup.py` to `2.0.0`, creates a `v2.0.0` tag, and pushes both. The `.github/workflows/publish.yml` workflow publishes to PyPI on the pushed tag via Trusted Publishing.
