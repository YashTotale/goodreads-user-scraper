<h1 align="center">
  <img alt="Goodreads Icon" width="200" src="https://raw.githubusercontent.com/YashTotale/goodreads-user-scraper/main/static/goodreads-icon.png"></img>
  <p></p>
  <b>Goodreads User Scraper</b>
</h1>

<p align="center"><strong>Scrape Goodreads User Data: Profile, Book Shelves, Books, Authors</strong></p>

<p align="center">
  <!-- Version -->
  <a href="https://pypi.org/project/goodreads-user-scraper/"><img src="https://img.shields.io/pypi/v/goodreads-user-scraper?style=for-the-badge&labelColor=000000&label=Version" alt="Version"></a>&nbsp;
  <!-- Downloads -->
  <a href="https://pypi.org/project/goodreads-user-scraper/"><img src="https://img.shields.io/pepy/dt/goodreads-user-scraper?style=for-the-badge&labelColor=000000&label=Downloads&logo=pypi&logoColor=FFFFFF" alt="Downloads"></a>&nbsp;
</p>

## Contents <!-- omit in toc -->

- [Usage](#usage)
  - [Install once, then run](#install-once-then-run)
  - [Run once without installing](#run-once-without-installing)
- [Arguments](#arguments)
  - [`--user_id`](#--user_id)
  - [`--output_dir`](#--output_dir)
  - [`--skip_user_info`](#--skip_user_info)
  - [`--skip_shelves`](#--skip_shelves)
  - [`--skip_authors`](#--skip_authors)
  - [`--cookie`](#--cookie)
  - [`--cookie_file`](#--cookie_file)
- [Authentication](#authentication)
  - [Getting your session cookie](#getting-your-session-cookie)
  - [Passing the cookie](#passing-the-cookie)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Publishing](#publishing)

## Usage

### Install once, then run

Best for repeat use. Installs the CLI into an isolated environment and adds the `goodreads-user-scraper` command to your shell.

Using [pipx](https://pipx.pypa.io/):

```bash
pipx install goodreads-user-scraper
goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install goodreads-user-scraper
goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
```

### Run once without installing

Best for one-off use. Downloads and runs the CLI in a temporary environment: no install step, no `$PATH` changes.

Using `pipx`:

```bash
pipx run goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
```

Or with `uvx` (ships with `uv`):

```bash
uvx goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
```

## Arguments

### `--user_id`

- **Description**: The user whose data should be scraped. Find your user id using [these directions](https://help.goodreads.com/s/article/Where-can-I-find-my-user-ID).
- **Required**: Yes

### `--output_dir`

- **Description**: The directory where all scraped data will be output.
- **Required**: No
- **Default**: `goodreads-data`

### `--skip_user_info`

- **Description**: If passed, skip scraping user information.
- **Required**: No

### `--skip_shelves`

- **Description**: If passed, skip scraping shelves.
- **Required**: No

### `--skip_authors`

- **Description**: If passed, skip scraping authors.
- **Required**: No

### `--cookie`

- **Description**: Your Goodreads session cookie (the full `Cookie:` request-header value). Required for shelf scraping — see [Authentication](#authentication).
- **Required**: No
- **Default**: None

### `--cookie_file`

- **Description**: Path to a text file containing your Goodreads session cookie. Used only if `--cookie` is not passed and `GOODREADS_COOKIE` is not set.
- **Required**: No
- **Default**: None

## Authentication

Shelf scraping requires authentication — Goodreads hides shelf data behind login. The other endpoints (profile, individual books, authors) work anonymously.

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

Ensure that your profile is viewable by anyone:

1. Navigate to the [Goodreads Account Settings](https://www.goodreads.com/user/edit) page
2. Click on the `Account & notifications` tab
3. In the `Privacy` section, under **Who Can View My Profile**, select "anyone". Save your account settings.

Shelf scraping requires a session cookie regardless of profile visibility — see [Authentication](#authentication).

## Development

1. Clone the [GitHub repository](https://github.com/YashTotale/goodreads-user-scraper)

   ```shell
   git clone https://github.com/YashTotale/goodreads-user-scraper.git
   ```

2. Run the [install script](/scripts/install.sh)

   ```shell
   bash scripts/install.sh
   ```

3. Make changes

4. Run the unit tests

   ```shell
   pytest
   ```

   These run against saved Goodreads HTML in `tests/fixtures/` — no network, no cookie. This is the CI gate on every push and PR.

   When Goodreads changes its markup, refresh the fixtures with [`scripts/capture_fixtures.py`](/scripts/capture_fixtures.py) (reads your cookie from `.goodreads-cookie` if present), then re-run `pytest`.

5. Optionally run the live smoke test

   ```shell
   bash scripts/test.sh
   ```

   This scrapes the real Goodreads site end to end. To include shelf scraping, save your Goodreads cookie to a gitignored `.goodreads-cookie` file in the repo root — the test script picks it up automatically. CI runs this monthly (see [`integration.yml`](/.github/workflows/integration.yml)) to catch Goodreads markup changes.

## Publishing

Publishing is automated via GitHub Actions using PyPI [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API tokens are stored.

Run the [publish script](/scripts/publish.sh) with the version bump type:

```shell
bash scripts/publish.sh <patch|minor|major>
```

The script bumps the version, creates a git tag, and pushes it. The [publish workflow](/.github/workflows/publish.yml) builds the distribution and uploads it to PyPI on any pushed `v*` tag.
