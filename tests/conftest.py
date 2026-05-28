"""Shared test fixtures.

The suite runs entirely against saved Goodreads HTML in ``tests/fixtures/`` — no
network, no cookie. Every page type has a real captured fixture; the happy-path
profile/book/author pages are captured both logged-out (``*_anon.html``) and
logged-in, so parser tests pin both. Refresh them with
``scripts/capture_fixtures.py``.

Two helpers cover everything:

- ``soup(name)`` parses a fixture into BeautifulSoup — for testing pure parsers.
- ``mock_get_soup({url_substring: fixture_name})`` replaces ``http.get_soup`` so
  orchestrator functions receive fixture soups keyed by URL, with no network.
"""

from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from scraper import author

FIXTURES = Path(__file__).parent / "fixtures"


def _soup(name):
    return BeautifulSoup((FIXTURES / name).read_text(encoding="utf-8"), "html.parser")


@pytest.fixture
def soup():
    """Return a loader that parses a fixture file into BeautifulSoup."""
    return _soup


@pytest.fixture
def mock_get_soup(monkeypatch):
    """Map a URL substring to a fixture, returned in place of a real fetch."""

    def install(url_map):
        def fake(url):
            for substring, name in url_map.items():
                if substring in url:
                    return _soup(name)
            raise AssertionError(f"no fixture mapped for url: {url}")

        monkeypatch.setattr("scraper.http.get_soup", fake)

    return install


@pytest.fixture(autouse=True)
def _clear_author_cache():
    """scrape_author memoizes in a module global; reset it so tests stay isolated."""
    author._cache.clear()
