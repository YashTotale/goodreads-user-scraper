# Contributing to Goodreads User Scraper

Thanks for your interest in contributing!

## Development Setup

You'll need [Python](https://www.python.org/) 3.10 or newer.

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/<your-username>/goodreads-user-scraper.git
   cd goodreads-user-scraper
   ```

2. Run the [install script](/scripts/install.sh) — it creates a virtualenv, installs the package with its dev dependencies, and sets up the pre-commit hooks:

   ```bash
   bash scripts/install.sh
   source .venv/bin/activate
   ```

3. Make your changes. [black](https://github.com/psf/black) and [mypy](https://mypy-lang.org/) run automatically on every commit via pre-commit; run them across the whole repo any time with:

   ```bash
   pre-commit run --all-files
   ```

4. Run the unit tests:

   ```bash
   pytest
   ```

   These run against saved Goodreads HTML in `tests/fixtures/` — no network, no cookie. This is the CI gate on every push and PR.

   When Goodreads changes its markup, refresh the fixtures with [`scripts/capture_fixtures.py`](/scripts/capture_fixtures.py) (reads your cookie from `.goodreads-cookie` if present), then re-run `pytest`.

5. Optionally run the live smoke test:

   ```bash
   bash scripts/test.sh
   ```

   This scrapes the real Goodreads site end to end against a sample profile; set `GOODREADS_USER_ID` to scrape your own instead. To include shelf scraping, save your Goodreads cookie to a gitignored `.goodreads-cookie` file in the repo root — the test script picks it up automatically. CI runs this monthly (see [`integration.yml`](/.github/workflows/integration.yml)) to catch Goodreads markup changes.

6. Optionally regenerate the demo GIFs:

   ```bash
   bash scripts/render_demos.sh
   ```

   Re-renders the `assets/demo*.gif` catalog with [vhs](https://github.com/charmbracelet/vhs). The live demos hit Goodreads (space out re-renders to avoid rate limiting); the full-scrape hero also needs a `.goodreads-cookie` file.

## Publishing

Releases are fully automated; cutting one is a single command:

```bash
bash scripts/publish.sh <patch|minor|major>
```

The script bumps the version, commits, and pushes the tag. Pushing a `v*` tag triggers the [publish workflow](/.github/workflows/publish.yml), which builds the distribution and uploads it to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) so no API tokens live in the repo or CI.

## Reporting Bugs & Requesting Features

Search [existing issues](https://github.com/YashTotale/goodreads-user-scraper/issues) first. If nothing matches, open a [new issue](https://github.com/YashTotale/goodreads-user-scraper/issues/new/choose) and include:

- Your OS and Python version
- The command you ran
- What you expected versus what actually happened

## Asking Questions

For usage questions, start a thread in [Discussions Q&A](https://github.com/YashTotale/goodreads-user-scraper/discussions/categories/q-a) rather than opening an issue.
