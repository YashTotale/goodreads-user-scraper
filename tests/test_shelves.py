import json
from argparse import Namespace

from bs4 import BeautifulSoup

from scraper import shelves

READ_BOOK_ID = "211721806-dungeon-crawler-carl"


def rows(soup, name):
    body = soup(name).find("tbody", {"id": "booksBody"})
    return body.find_all("tr", recursive=False)


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


def test_get_all_shelves_skips_without_cookie(tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.http.has_cookie", lambda: False)
    fetched = []
    monkeypatch.setattr("scraper.http.get_soup", lambda url: fetched.append(url))

    args = Namespace(skip_shelves=False, user_id="54739262", output_dir=tmp_path)
    shelves.get_all_shelves(args)

    assert fetched == []
    assert not (tmp_path / "books").exists()


def test_get_all_shelves_discovers_every_shelf(
    tmp_path, soup, mock_get_soup, monkeypatch
):
    monkeypatch.setattr("scraper.http.has_cookie", lambda: True)
    mock_get_soup({"user/show": "profile.html"})
    scraped = []
    monkeypatch.setattr(
        "scraper.shelves.get_shelf", lambda args, shelf: scraped.append(shelf)
    )

    args = Namespace(skip_shelves=False, user_id="54739262", output_dir=tmp_path)
    shelves.get_all_shelves(args)

    # One get_shelf call per shelf link in the profile, including the standard shelves.
    shelf_links = soup("profile.html").find("div", {"id": "shelves"}).find_all("a")
    assert len(scraped) == len(shelf_links)
    assert {"read", "to-read", "currently-reading"} <= set(scraped)
    assert (tmp_path / "books").exists()


def test_process_row_creates_book_file(tmp_path, soup, mock_get_soup):
    mock_get_soup({"book/show": "book.html"})
    row = rows(soup, "shelf_read.html")[0]

    shelves._process_row(row, Namespace(skip_authors=True), "read", tmp_path, 1)

    data = json.loads((tmp_path / f"{READ_BOOK_ID}.json").read_text())
    assert data["shelves"] == ["read"]
    assert data["rating"] == 4
    assert data["dates_read"] == ["May 19, 2026"]
    assert data["book_title"] == "Dungeon Crawler Carl"


def test_process_row_updates_existing_without_rescrape(tmp_path, soup, monkeypatch):
    book_file = tmp_path / f"{READ_BOOK_ID}.json"
    book_file.write_text(json.dumps({"shelves": ["read"], "book_title": "SEEDED"}))
    fetched = []
    monkeypatch.setattr("scraper.http.get_soup", lambda url: fetched.append(url))

    row = rows(soup, "shelf_read.html")[0]
    shelves._process_row(row, Namespace(skip_authors=True), "favorites", tmp_path, 1)

    data = json.loads(book_file.read_text())
    assert data["shelves"] == ["read", "favorites"]
    assert data["book_title"] == "SEEDED"  # not re-scraped
    assert fetched == []


def test_process_row_skips_unparseable_row(tmp_path):
    bad_row = BeautifulSoup("<tr></tr>", "html.parser")
    shelves._process_row(bad_row, Namespace(skip_authors=True), "read", tmp_path, 1)

    assert list(tmp_path.iterdir()) == []  # bad row swallowed, nothing written


def test_get_shelf_paginates_then_terminates(tmp_path, soup, mock_get_soup):
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    # Seed every row so each takes the cheap update path instead of re-scraping.
    book_ids = [shelves.get_id(row) for row in rows(soup, "shelf_read.html")]
    for book_id in book_ids:
        (books_dir / f"{book_id}.json").write_text(json.dumps({"shelves": ["seed"]}))

    # Only page 1 (content) and page 2 (empty) are mapped — a page 3 fetch would raise.
    mock_get_soup({"page=1": "shelf_read.html", "page=2": "shelf_empty.html"})
    args = Namespace(user_id="54739262", output_dir=tmp_path, skip_authors=True)
    shelves.get_shelf(args, "read")

    for book_id in book_ids:
        data = json.loads((books_dir / f"{book_id}.json").read_text())
        assert data["shelves"] == ["seed", "read"]
