import json
from argparse import Namespace

from bs4 import BeautifulSoup

from scraper import shelves

READ_BOOK_ID = "211721806-dungeon-crawler-carl"


def rows(soup, name):
    body = soup(name).find("tbody", {"id": "booksBody"})
    return body.find_all("tr", recursive=False)


# Row parsers


def test_get_id(soup):
    assert shelves.get_id(rows(soup, "shelf_read.html")[0]) == READ_BOOK_ID


def test_get_rating_when_rated(soup):
    assert shelves.get_rating(rows(soup, "shelf_read.html")[0]) == 4


def test_get_rating_when_unrated(soup):
    assert shelves.get_rating(rows(soup, "shelf_to_read.html")[0]) is None


def test_get_dates_read_when_present(soup):
    assert shelves.get_dates_read(rows(soup, "shelf_read.html")[0]) == ["May 19, 2026"]


def test_get_dates_read_when_missing(soup):
    assert shelves.get_dates_read(rows(soup, "shelf_to_read.html")[0]) == []


# fetch_shelf_page


async def test_fetch_shelf_page_requests_100_per_page(monkeypatch):
    captured = []

    async def fake(url):
        captured.append(url)

    monkeypatch.setattr("scraper.http.get_soup", fake)
    await shelves.fetch_shelf_page("54739262", "read", 1)

    # Larger pages mean fewer paginations per shelf.
    assert "per_page=100" in captured[0]


# collect_shelf_rows pagination


async def test_collect_shelf_rows_stops_on_short_page(mock_get_soup):
    # shelf_read's 30 rows < PER_PAGE, so a short page 1 ends pagination.
    # Only page 1 is mapped; a page 2 fetch would raise (no fixture).
    mock_get_soup({"&page=1&": "shelf_read.html"})
    collected = await shelves.collect_shelf_rows("54739262", "read")
    assert len(collected) == 30


async def test_collect_shelf_rows_accumulates_across_pages(monkeypatch, mock_get_soup):
    # PER_PAGE=1 forces full pages, so pagination accumulates page 1 + page 2 and
    # stops on the empty page 3. mock keys use "&page=N&" to avoid matching "per_page".
    monkeypatch.setattr(shelves, "PER_PAGE", 1)
    mock_get_soup(
        {
            "&page=1&": "shelf_read.html",
            "&page=2&": "shelf_to_read.html",
            "&page=3&": "shelf_empty.html",
        }
    )
    collected = await shelves.collect_shelf_rows("54739262", "read")
    assert len(collected) == 40  # 30 from page 1 + 10 from page 2


# _dedupe_books


def test_dedupe_merges_book_across_shelves(soup):
    row = rows(soup, "shelf_read.html")[0]
    books = shelves._dedupe_books([("read", [row]), ("favorites", [row])])
    assert list(books) == [READ_BOOK_ID]
    assert books[READ_BOOK_ID]["shelves"] == ["read", "favorites"]


def test_dedupe_extracts_rating_and_dates(soup):
    row = rows(soup, "shelf_read.html")[0]
    books = shelves._dedupe_books([("read", [row])])
    assert books[READ_BOOK_ID]["rating"] == 4
    assert books[READ_BOOK_ID]["dates_read"] == ["May 19, 2026"]


def test_dedupe_skips_unparseable_row(soup):
    good = rows(soup, "shelf_read.html")[0]
    bad = BeautifulSoup("<tr></tr>", "html.parser").find("tr")
    books = shelves._dedupe_books([("read", [good, bad])])
    assert list(books) == [READ_BOOK_ID]  # malformed row dropped


# process_book


async def test_process_book_scrapes_new(tmp_path, mock_get_soup):
    mock_get_soup({"book/show": "book.html"})
    info = {"shelves": ["read"], "rating": 4, "dates_read": ["May 19, 2026"]}
    await shelves.process_book(
        READ_BOOK_ID, info, Namespace(skip_authors=True), tmp_path
    )

    data = json.loads((tmp_path / f"{READ_BOOK_ID}.json").read_text())
    assert data["shelves"] == ["read"]
    assert data["rating"] == 4
    assert data["dates_read"] == ["May 19, 2026"]
    assert data["book_title"] == "Dungeon Crawler Carl"


async def test_process_book_merges_into_existing_without_rescrape(
    tmp_path, monkeypatch
):
    book_file = tmp_path / f"{READ_BOOK_ID}.json"
    book_file.write_text(json.dumps({"shelves": ["read"], "book_title": "SEEDED"}))
    fetched = []
    monkeypatch.setattr("scraper.http.get_soup", lambda url: fetched.append(url))

    info = {"shelves": ["read", "favorites"], "rating": 4, "dates_read": []}
    await shelves.process_book(
        READ_BOOK_ID, info, Namespace(skip_authors=True), tmp_path
    )

    data = json.loads(book_file.read_text())
    assert data["shelves"] == ["read", "favorites"]
    assert data["book_title"] == "SEEDED"  # not re-scraped
    assert fetched == []


# get_all_shelves orchestrator


async def test_get_all_shelves_skips_without_cookie(tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.http.has_cookie", lambda: False)
    fetched = []
    monkeypatch.setattr("scraper.http.get_soup", lambda url: fetched.append(url))

    args = Namespace(skip_shelves=False, user_id="54739262", output_dir=tmp_path)
    await shelves.get_all_shelves(args)

    assert fetched == []
    assert not (tmp_path / "books").exists()


async def test_get_all_shelves_dedupes_and_scrapes(
    tmp_path, soup, mock_get_soup, monkeypatch
):
    monkeypatch.setattr("scraper.http.has_cookie", lambda: True)
    # read + to-read have content; every other shelf resolves to the empty page.
    mock_get_soup(
        {
            "user/show": "profile.html",
            "shelf=read&": "shelf_read.html",
            "shelf=to-read&": "shelf_to_read.html",
            "review/list": "shelf_empty.html",
            "book/show": "book.html",
        }
    )
    args = Namespace(
        skip_shelves=False, user_id="54739262", output_dir=tmp_path, skip_authors=True
    )
    await shelves.get_all_shelves(args)

    books_dir = tmp_path / "books"
    assert books_dir.exists()
    # Every unique book across the two non-empty shelves is scraped exactly once.
    expected = {shelves.get_id(r) for r in rows(soup, "shelf_read.html")} | {
        shelves.get_id(r) for r in rows(soup, "shelf_to_read.html")
    }
    assert {p.stem for p in books_dir.glob("*.json")} == expected
    read_book = json.loads((books_dir / f"{READ_BOOK_ID}.json").read_text())
    assert "read" in read_book["shelves"]
