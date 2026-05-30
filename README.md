<h1 align="center">
  <img alt="Goodreads Icon" width="200" src="https://raw.githubusercontent.com/YashTotale/goodreads-user-scraper/main/assets/goodreads-icon.png"></img>
  <p></p>
  <b>Goodreads User Scraper</b>
</h1>

<p align="center"><strong>Export Goodreads profile, shelves, books, and authors to JSON</strong></p>

<p align="center">
  <!-- Version -->
  <a href="https://pypi.org/project/goodreads-user-scraper/"><img src="https://img.shields.io/pypi/v/goodreads-user-scraper?style=for-the-badge&labelColor=000000&label=Version" alt="Version"></a>&nbsp;
  <!-- Downloads -->
  <a href="https://pypi.org/project/goodreads-user-scraper/"><img src="https://img.shields.io/pepy/dt/goodreads-user-scraper?style=for-the-badge&labelColor=000000&label=Downloads&logo=pypi&logoColor=FFFFFF" alt="Downloads"></a>&nbsp;
</p>

<p align="center">
  <img alt="CLI Demo" width="800" src="https://raw.githubusercontent.com/YashTotale/goodreads-user-scraper/main/assets/demo.gif"></img>
</p>

## Contents <!-- omit in toc -->

- [Usage](#usage)
  - [Install once, then run](#install-once-then-run)
  - [Run once without installing](#run-once-without-installing)
- [Output](#output)
- [Arguments](#arguments)
  - [`--user_id`](#--user_id)
  - [`--output_dir`](#--output_dir)
  - [`--cookie`](#--cookie)
  - [`--cookie_file`](#--cookie_file)
  - [`--skip_user_info`](#--skip_user_info)
  - [`--skip_shelves`](#--skip_shelves)
  - [`--skip_authors`](#--skip_authors)
- [Authentication](#authentication)
  - [Getting your session cookie](#getting-your-session-cookie)
  - [Passing the cookie](#passing-the-cookie)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Publishing](#publishing)

## Usage

Use [pipx](https://pipx.pypa.io/) or [uv](https://docs.astral.sh/uv/) — both install the CLI from PyPI.

### Install once, then run

Best for repeat use. Installs the CLI into an isolated environment and adds the `goodreads-user-scraper` command to your shell.

```bash
pipx install goodreads-user-scraper      # or: uv tool install goodreads-user-scraper
goodreads-user-scraper --user_id <your id>
```

### Run once without installing

Best for one-off use. Downloads and runs the CLI in a temporary environment: no install step, no `$PATH` changes.

```bash
pipx run goodreads-user-scraper --user_id <your id>
# or: uvx goodreads-user-scraper --user_id <your id>
```

## Output

Data is written to `--output_dir` (default `goodreads-data/`):

```text
goodreads-data/
├── user.json                          # profile: name, average rating, rating/review counts
└── books/
    ├── 4395.The_Grapes_of_Wrath.json  # one JSON file per book
    └── …
```

Each `books/*.json` looks like this — your `rating`, `dates_read`, and `shelves` come from your library; the author is nested:

```json
{
  "book_id_title": "4395.The_Grapes_of_Wrath",
  "book_id": "4395",
  "book_title": "The Grapes of Wrath",
  "book_description": "The Grapes of Wrath is a landmark of American literature. A portrait of the conflict between the powerful and the powerless…",
  "book_url": "https://www.goodreads.com/book/show/4395.The_Grapes_of_Wrath",
  "book_image": "https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/1511302892i/4395.jpg",
  "book_series_uri": null,
  "year_first_published": "1939",
  "num_pages": 455,
  "genres": ["Classics", "Fiction", "Historical Fiction", "Literature", "Novels", "School", "Historical"],
  "num_ratings": 1011464,
  "num_reviews": 31088,
  "average_rating": 4.03,
  "author": {
    "author_id_title": "585.John_Steinbeck",
    "author_id": "585",
    "author_name": "John Steinbeck",
    "author_url": "https://www.goodreads.com/author/show/585.John_Steinbeck",
    "author_image": "https://images.gr-assets.com/authors/1182118389p5/585.jpg",
    "author_description": "John Ernst Steinbeck was an American writer. He won the 1962 Nobel Prize in Literature…"
  },
  "rating": 5,
  "dates_read": ["May 03, 2020"],
  "shelves": ["read", "2020", "2020s-favorites"]
}
```

The two description fields are truncated here; the rest is real output. Without a cookie only `user.json` is written (see [Authentication](#authentication)); `--skip_authors` omits the nested `author`.

## Arguments

### `--user_id`

- **Description**: The user whose data should be scraped. Find your user id using [these directions](https://help.goodreads.com/s/article/Where-can-I-find-my-user-ID).
- **Required**: Yes

### `--output_dir`

- **Description**: The directory where all scraped data will be output.
- **Required**: No
- **Default**: `goodreads-data`

### `--cookie`

- **Description**: Your Goodreads session cookie (the full `Cookie:` request-header value). Required for shelf scraping — see [Authentication](#authentication).
- **Required**: No
- **Default**: None

### `--cookie_file`

- **Description**: Path to a text file containing your Goodreads session cookie.
- **Required**: No
- **Default**: None

### `--skip_user_info`

- **Description**: If passed, skip scraping user information.
- **Required**: No

### `--skip_shelves`

- **Description**: If passed, skip scraping shelves. Books (and their authors) are scraped from your shelves, so this skips them too.
- **Required**: No

### `--skip_authors`

- **Description**: If passed, skip scraping authors.
- **Required**: No

## Authentication

Shelf scraping requires a cookie — Goodreads hides shelf data behind login. Without one you get the profile only; with one you also get shelves, books, and authors.

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

**Missing profile or shelf data?**

- **Your own account:** pass your session cookie (see [Authentication](#authentication)) — your profile, shelves, and books all scrape, even on a private profile.
- **Another user's account:** what you can scrape depends on their profile privacy setting. Shelves always require your cookie (see [Authentication](#authentication)).
  - **Anyone:** the profile scrapes even without a cookie.
  - **Goodreads members only:** pass your cookie — any signed-in account works.
  - **Friends only:** pass your cookie, and your account must be their friend.

## Development

1. Run the [install script](/scripts/install.sh)

   ```bash
   bash scripts/install.sh
   ```

2. Make changes

3. Run the unit tests

   ```bash
   pytest
   ```

   These run against saved Goodreads HTML in `tests/fixtures/` — no network, no cookie. This is the CI gate on every push and PR.

   When Goodreads changes its markup, refresh the fixtures with [`scripts/capture_fixtures.py`](/scripts/capture_fixtures.py) (reads your cookie from `.goodreads-cookie` if present), then re-run `pytest`.

4. Optionally run the live smoke test

   ```bash
   bash scripts/test.sh
   ```

   This scrapes the real Goodreads site end to end against a sample profile; set `GOODREADS_USER_ID` to scrape your own instead. To include shelf scraping, save your Goodreads cookie to a gitignored `.goodreads-cookie` file in the repo root — the test script picks it up automatically. CI runs this monthly (see [`integration.yml`](/.github/workflows/integration.yml)) to catch Goodreads markup changes.

## Publishing

Notes for future maintainers (me). Releases are fully automated; cutting one is a single command:

```bash
bash scripts/publish.sh <patch|minor|major>
```

The script bumps the version, commits, and pushes the tag. Pushing a `v*` tag triggers the [publish workflow](/.github/workflows/publish.yml), which builds the distribution and uploads it to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) so no API tokens live in the repo or CI.
