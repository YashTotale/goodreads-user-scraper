import pytest

from scraper import author

AUTHOR_ID = "3137322.Fyodor_Dostoevsky"
AUTHOR_NAME = "Fyodor Dostoevsky"
# Author parsers must work on both the logged-out and logged-in page.
AUTHOR = ["author.html", "author_anon.html"]


def test_get_id_number():
    assert author.get_id_number(AUTHOR_ID) == "3137322"


@pytest.mark.parametrize("fixture", AUTHOR)
def test_get_author_image(soup, fixture):
    assert (
        author.get_author_image(soup(fixture), AUTHOR_NAME)
        == "https://images.gr-assets.com/authors/1754423588p5/3137322.jpg"
    )


@pytest.mark.parametrize("fixture", AUTHOR)
def test_get_author_description(soup, fixture):
    description = author.get_author_description(soup(fixture), "3137322")
    assert description and "Dostoevsky" in description


# An author with neither a photo nor a bio — both parsers must return None.
def test_get_author_image_missing(soup):
    assert (
        author.get_author_image(soup("author_no_image.html"), "Charles E. Bolton")
        is None
    )


def test_get_author_description_missing(soup):
    assert (
        author.get_author_description(soup("author_no_image.html"), "2814983") is None
    )


# scrape_author orchestrator


def test_scrape_author_builds_record(mock_get_soup):
    mock_get_soup({"author/show": "author.html"})
    record = author.scrape_author(AUTHOR_ID)

    assert record["author_id_title"] == AUTHOR_ID
    assert record["author_id"] == "3137322"
    assert record["author_name"] == AUTHOR_NAME
    assert record["author_url"].endswith("/author/show/" + AUTHOR_ID)
    assert record["author_image"].endswith("3137322.jpg")
    assert "Dostoevsky" in record["author_description"]


def test_scrape_author_caches_by_id(monkeypatch, soup):
    fetches = []

    def fake_get_soup(url):
        fetches.append(url)
        return soup("author.html")

    monkeypatch.setattr("scraper.http.get_soup", fake_get_soup)

    first = author.scrape_author(AUTHOR_ID)
    second = author.scrape_author(AUTHOR_ID)

    assert first is second  # same cached object
    assert len(fetches) == 1  # fetched only once
