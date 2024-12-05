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
  <!-- Build -->
  <a href="https://github.com/YashTotale/goodreads-user-scraper/actions/workflows/integrate.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/YashTotale/goodreads-user-scraper/integrate.yml?branch=main&style=for-the-badge&label=Build&logo=github&logoColor=FFFFFF&labelColor=000000" alt="Build"/></a>&nbsp;
</p>

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

## Troubleshooting

Ensure that your profile is viewable by anyone:

1. Navigate to the [Goodreads Account Settings](https://www.goodreads.com/user/edit) page
2. Click on the `Account & notifications` tab
3. In the `Privacy` section, under **Who Can View My Profile**, select "anyone". Save your account settings.

## Development

1. Clone the [GitHub repository](https://github.com/YashTotale/goodreads-user-scraper)

   ```shell
   git clone https://github.com/YashTotale/goodreads-user-scraper.git
   ```

2. Run the [install script](/scripts/install.sh)

   ```shell
   sh scripts/install.sh
   ```

3. Make changes

4. Run the [test script](/scripts/test.sh)

   ```shell
   sh scripts/test.sh
   ```

## Publishing

1. Create `.env`

   ```text
   TWINE_USERNAME=<foo>
   TWINE_PASSWORD=<bar>
   ```

2. Run the [publish script](/scripts/publish.sh)

   ```shell
   sh scripts/publish.sh <patch|minor|major>
   ```
