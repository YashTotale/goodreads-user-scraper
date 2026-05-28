from argparse import Namespace

import pytest

from scraper import books

BOOK_ID = "211721806-dungeon-crawler-carl"
# Book parsers must work on both the logged-out and logged-in page.
BOOK = ["book.html", "book_anon.html"]


@pytest.mark.parametrize("fixture", BOOK)
def test_get_title(soup, fixture):
    assert books.get_title(soup(fixture)) == "Dungeon Crawler Carl"


@pytest.mark.parametrize("fixture", BOOK)
def test_get_description(soup, fixture):
    assert books.get_description(soup(fixture)).startswith(
        "The apocalypse will be televised!"
    )


@pytest.mark.parametrize("fixture", BOOK)
def test_get_image(soup, fixture):
    assert (
        books.get_image(soup(fixture))
        == "https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/1715780755i/211721806.jpg"
    )


@pytest.mark.parametrize("fixture", BOOK)
def test_get_series_uri(soup, fixture):
    assert (
        books.get_series_uri(soup(fixture))
        == "https://www.goodreads.com/series/309211-dungeon-crawler-carl"
    )


@pytest.mark.parametrize("fixture", BOOK)
def test_get_year_first_published(soup, fixture):
    assert books.get_year_first_published(soup(fixture)) == "2020"


@pytest.mark.parametrize("fixture", BOOK)
def test_get_num_pages(soup, fixture):
    assert books.get_num_pages(soup(fixture)) == 450


@pytest.mark.parametrize("fixture", BOOK)
def test_get_genres(soup, fixture):
    assert books.get_genres(soup(fixture)) == [
        "Fantasy",
        "Science Fiction",
        "Audiobook",
        "Fiction",
        "Humor",
        "Dystopia",
        "Adventure",
    ]


@pytest.mark.parametrize("fixture", BOOK)
def test_get_num_ratings(soup, fixture):
    assert books.get_num_ratings(soup(fixture)) == 396420


@pytest.mark.parametrize("fixture", BOOK)
def test_get_num_reviews(soup, fixture):
    assert books.get_num_reviews(soup(fixture)) == 53589


@pytest.mark.parametrize("fixture", BOOK)
def test_get_average_rating(soup, fixture):
    assert books.get_average_rating(soup(fixture)) == 4.46


@pytest.mark.parametrize("fixture", BOOK)
def test_get_author_id(soup, fixture):
    assert books.get_author_id(soup(fixture)) == "999015.Matt_Dinniman"


def test_get_id():
    assert books.get_id(BOOK_ID) == "211721806"


def test_scrape_book_skips_author_fetch(mock_get_soup):
    mock_get_soup({"book/show": "book.html"})
    book = books.scrape_book(BOOK_ID, Namespace(skip_authors=True))

    assert "author" not in book
    assert book["book_id_title"] == BOOK_ID
    assert book["book_id"] == "211721806"
    assert book["book_title"] == "Dungeon Crawler Carl"
    assert book["num_pages"] == 450


def test_scrape_book_fetches_author(mock_get_soup):
    mock_get_soup({"book/show": "book.html", "author/show": "author.html"})
    book = books.scrape_book(BOOK_ID, Namespace(skip_authors=False))

    # The author id comes from the book page; the record is fetched and embedded.
    assert book["author"]["author_id_title"] == "999015.Matt_Dinniman"
    assert book["author"]["author_name"]


# A sparse book exercising the empty/None/zero branches.
MINIMAL = "book_minimal.html"


def test_get_description_when_empty(soup):
    assert books.get_description(soup(MINIMAL)) == ""


def test_get_genres_when_missing(soup):
    assert books.get_genres(soup(MINIMAL)) is None


def test_get_series_uri_when_missing(soup):
    assert books.get_series_uri(soup(MINIMAL)) is None


def test_zero_engagement_counts(soup):
    s = soup(MINIMAL)
    assert books.get_num_ratings(s) == 0
    assert books.get_num_reviews(s) == 0
    assert books.get_average_rating(s) == 0.0
