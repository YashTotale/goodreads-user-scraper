# Goodreads Shelf Cookie Authentication

**Status:** Approved
**Date:** 2026-05-27
**Target version:** 2.0.0

## Context

The package was created in 2021, when Goodreads served shelf data
(`/review/list/<user_id>?shelf=...&print=true`) without authentication.
Goodreads has since walled shelf data behind login, breaking
`scraper/shelves.py` and the smoke-test script.

What still works anonymously:

- User profile (`/user/show/<id>`) — `scraper/user.py`
- Individual book pages (`/book/show/<id>`) — `scraper/books.py`
- Author pages (`/author/show/<id>`) — `scraper/author.py`

What's broken:

- Shelf index and per-shelf book listings — `scraper/shelves.py`

The official Goodreads API was retired in December 2020 — no OAuth or
sanctioned mechanism is available. Username/password automation is
unreliable because most accounts authenticate via "Sign in with Amazon"
SSO and Goodreads frequently presents captcha/MFA challenges. A
session cookie copied from a browser is the most resilient option.

## Goals

- Restore shelf scraping by adding session-cookie authentication.
- Keep anonymous fetching for endpoints that still work without login.
- Improve the request layer and fix latent bugs while touching this code.

## Non-Goals

- Username/password login automation.
- Unit tests, type hints, parameterized smoke-test script (tracked as
  separate follow-up issues — see [Out of scope](#out-of-scope)).

## Architecture

### New module: `scraper/http.py`

Owns a single `requests.Session` configured once at startup. Exports:

- `init_session(cookie: str | None) -> None` — sets `User-Agent`, attaches
  the `Cookie` header if `cookie` is provided, and records whether a
  cookie was attached.
- `has_cookie() -> bool` — returns whether `init_session` was called
  with a non-empty cookie. Used by `shelves.py` to decide between the
  skip-with-warning path and the fetch-and-detect path.
- `get_soup(url: str) -> BeautifulSoup` — `session.get(url, timeout=15)`,
  returns parsed soup.

A module-level `DEFAULT_TIMEOUT = 15` constant is applied to every
request. The `User-Agent` is a current desktop-browser string.

Every existing `urlopen(url)` call in `scraper/user.py`,
`scraper/shelves.py`, `scraper/books.py`, and `scraper/author.py` is
replaced by `http.get_soup(url)`. The `BeautifulSoup(source, "html.parser")`
boilerplate at each site is removed.

### Cookie resolution

In `scraper/__main__.py`, before calling `scrape_user`:

```
cookie = (
    args.cookie
    or os.environ.get("GOODREADS_COOKIE")
    or read_cookie_file(args.cookie_file)
)
http.init_session(cookie)
```

Precedence is `--cookie` flag > `GOODREADS_COOKIE` env var >
`--cookie_file` path. `read_cookie_file` returns `None` if the path arg
is unset; if the path is set but the file does not exist, it raises so
typos surface immediately. Contents are `.strip()`ed to tolerate
trailing newlines.

The cookie value is the full `Cookie:` request-header string (e.g.
`_session_id2=abc; csm-hit=xyz; ...`), not just the session token.

### Shelf-scraping flow

`scraper/shelves.py::get_all_shelves` becomes:

```
if args.skip_shelves:
    return

if no cookie was provided to http.init_session:
    print verbose warning (see below) and return

soup = http.get_soup(profile_url)
if detect_logged_out(soup):
    print error and sys.exit(1)

# proceed with normal shelf iteration
```

**Cookie-missing warning** (kept verbose — explains all three input
mechanisms and how to suppress):

```
⚠️  Skipping shelves: Goodreads now requires login to view shelf data.
   To scrape shelves, provide your Goodreads session cookie via one of:
     --cookie "<cookie string>"
     GOODREADS_COOKIE=<cookie string>   (environment variable)
     --cookie_file <path-to-file>
   See the README for how to grab the cookie from your browser.
   Pass --skip_shelves to suppress this message.
```

**`detect_logged_out` heuristic:** `soup.find("div", {"id":
"third_party_sign_in"}) is not None`. The `third_party_sign_in` div is
present on the sign-in page Goodreads redirects to when the cookie is
invalid or expired. No extra request is needed — detection runs on the
profile-page fetch that the shelf loop already needs.

On detection, print a clear error and `sys.exit(1)`:

```
❌ Cookie appears invalid or expired. Re-grab the Cookie header
   value from your browser DevTools and try again.
```

### Per-book resilience

The row loop inside `scraper/shelves.py::get_shelf` is wrapped in
`try/except Exception as e: print(f"⚠️  Skipped book on page {page}: {e}")`.
A single broken row (layout change, private book, transient error) no
longer kills the entire run.

## CLI changes — `scraper/__main__.py`

### New flags

- `--cookie <string>` — Goodreads session cookie (full `Cookie:` header
  value).
- `--cookie_file <path>` — path to a text file containing the cookie
  string.

`GOODREADS_COOKIE` is read automatically; no new flag for it.

### Fixed flags (breaking)

The three boolean flags currently use `type=bool`, which is broken:
`bool("False")` is `True`, so `--skip_shelves False` *still* skips
shelves. They become `action="store_true"`:

- `--skip_user_info`
- `--skip_shelves`
- `--skip_authors`

After the change, `--skip_shelves True` raises an argparse error — this
is the intended breaking change.

### `--output_dir`

Changes to `type=Path`. The `endswith("/")` hack at lines 23-25 is
removed; downstream code uses `output_dir / "books"` etc.

## Bundled cleanups

Beyond auth + HTTP-layer changes, these land in the same PR:

1. **Delete commented-out code** — `get_rating_distribution` (books.py:12-23),
   `get_series_name` (books.py:110-118), and the matching commented-out
   keys in `scrape_book` (lines 155, 163).
2. **Delete stale attribution** — top-of-file `Source:` reference in
   `books.py` (lines 1-3). File has long since diverged.
3. **Consistent `None` returns** — `get_num_reviews`, `get_num_ratings`,
   `get_average_rating` in `books.py` return `None` instead of `""` when
   the field is missing. JSON consumers can `is None`-check cleanly.
   (Semver-breaking; consumer-visible.)
4. **Context managers for file I/O** — `with open(...) as f:` replaces
   the manual `open` / `close` in `shelves.py:86-92, 104-106` and
   `user.py:47-49`.
5. **Rename `get_shelf_url` → `fetch_shelf_page`** in `shelves.py`. The
   function fetches and parses HTML, not just builds a URL.

## README updates

- New "Authentication" section between "Arguments" and "Troubleshooting",
  explaining shelf scraping now requires a session cookie. Step-by-step:
  1. Sign in to Goodreads in a browser.
  2. Open DevTools → Network tab.
  3. Click any `goodreads.com` request → Headers → copy the `Cookie:`
     request-header value.
  4. Pass it via `--cookie "..."`, `GOODREADS_COOKIE=...`, or
     `--cookie_file path.txt`.
  5. Cookies typically last weeks; re-grab when you see a "cookie
     invalid" error.
- "Arguments" section gets entries for `--cookie` and `--cookie_file`,
  with a note that `GOODREADS_COOKIE` is read automatically.
- "Troubleshooting" keeps the "make profile viewable" note (still
  relevant for user-info / book / author endpoints) and adds a
  sub-bullet noting that shelf scraping requires the cookie regardless
  of profile visibility.

## Versioning and release

Target: **1.2.5 → 2.0.0** (major bump). Three semver-breaking changes
justify it:

- `--skip_*` flag semantics changed (`type=bool` → `store_true`).
- New required dependency (`requests`).
- JSON-output change (`""` → `null` for some optional numeric fields in
  `books.py`).

**Release ordering:**

- PR ships only code changes — `setup.py` stays at `1.2.5`.
- After merge to `main`, run `bash scripts/publish.sh major` locally on
  `main`. The script bumps to `2.0.0`, creates the tag, and pushes both;
  GitHub Actions publishes to PyPI on the pushed `v*` tag.

## `setup.py`

Add `requests` to `install_requires`:

```
install_requires=["beautifulsoup4", "requests"],
```

Update the `description` field to match the README tagline:

```
description="Scrape Goodreads User Data: Profile, Book Shelves, Books, Authors",
```

## Out of scope

Tracked as separate GitHub issues to create after this spec is committed:

- **Add a real test suite** — pytest + saved HTML fixtures from real
  Goodreads pages, mock `requests` so CI does not hit live Goodreads.
- **Add type hints across `scraper/*.py`** — function signatures and
  return types.
- **Parameterize `scripts/test.sh`** — `--user_id` from env var with a
  sensible default.
