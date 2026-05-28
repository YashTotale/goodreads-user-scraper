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

## Usage

Using [pip](https://pypi.org/project/pip/):

```bash
pip install goodreads-user-scraper
goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
```

Using [pipx](https://pypi.org/project/pipx/):

```bash
pipx run goodreads-user-scraper --user_id <your id> --output_dir goodreads-data
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

- **Description**: Whether the script should skip scraping user information.
- **Required**: No
- **Default**: `False`

### `--skip_shelves`

- **Description**: Whether the script should skip scraping shelves.
- **Required**: No
- **Default**: `False`

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

4. Run the [test script](/scripts/test.sh)

   ```shell
   bash scripts/test.sh
   ```

   To test shelf scraping, save your Goodreads cookie to a gitignored `.goodreads-cookie` file in the repo root — the test script picks it up automatically.

## Publishing

Publishing is automated via GitHub Actions using PyPI [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API tokens are stored.

Run the [publish script](/scripts/publish.sh) with the version bump type:

```shell
bash scripts/publish.sh <patch|minor|major>
```

The script bumps the version, creates a git tag, and pushes it. The [publish workflow](/.github/workflows/publish.yml) builds the distribution and uploads it to PyPI on any pushed `v*` tag.
