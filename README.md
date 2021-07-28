<p align="center"><img alt="Goodreads Icon" width="150" src="https://raw.githubusercontent.com/YashTotale/goodreads-user-scraper/main/static/goodreads-icon.png"></img></p>

<h1 align="center">Goodreads User Scraper</h1>

<p align="center">
<a href="https://pypi.org/project/goodreads-user-scraper/"><img alt="Version Badge" src="https://img.shields.io/pypi/v/goodreads-user-scraper?style=flat-square&labelColor=000000&logo=pypi&logoColor=FFFFFF&label=Version"></img></a>
<a href="https://pypi.org/project/goodreads-user-scraper/"><img alt="Downloads Badge" src="https://img.shields.io/pypi/dm/goodreads-user-scraper?style=flat-square&labelColor=000000&logo=pypi&logoColor=FFFFFF&label=Downloads"></img></a>
<a href="https://github.com/YashTotale/goodreads-user-scraper/blob/main/LICENSE.md"><img alt="License Badge" src="https://img.shields.io/pypi/l/goodreads-user-scraper?style=flat-square&labelColor=000000&label=License"></img></a>
</p>

## Contents <!-- omit in toc -->

- [Usage](#usage)
- [Arguments](#arguments)
  - [`--user-id`](#--user-id)
  - [`--output-dir`](#--output-dir)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Publishing](#publishing)

## Usage

Using [pip](https://pypi.org/project/pip/):

```bash
pip install goodreads-user-scraper
goodreads-user-scraper --user_id 54739262 --output_dir books
```

Using [pipx](https://pypi.org/project/pipx/):

```bash
pipx run goodreads-user-scraper --user_id 54739262 --output_dir books
```

## Arguments

### `--user-id`

- **Description**: The user whose data should be scraped. Find your user id using [these directions](https://help.goodreads.com/s/article/Where-can-I-find-my-user-ID).
- **Required**: Yes

### `--output-dir`

- **Description**: The directory where all scraped data will be output.
- **Required**: No
- **Default**: goodreads-data

## Troubleshooting

Ensure that your profile is viewable by anyone:

1. Navigate to the [Goodreads Account Settings](https://www.goodreads.com/user/edit) page
2. Click on the `Settings` tab
3. In the `Privacy` section, under the **Who Can View My Profile** question, select "anyone"

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
   sh scripts/publish.sh
   ```
