import json
import sys
from argparse import Namespace

import pytest

from scraper import __main__, __version__

# resolve_cookie precedence: --cookie > GOODREADS_COOKIE env > --cookie_file.


def test_resolve_cookie_prefers_cli_arg(monkeypatch):
    monkeypatch.setenv("GOODREADS_COOKIE", "env-cookie")
    args = Namespace(cookie="cli-cookie", cookie_file=None)
    assert __main__.resolve_cookie(args) == "cli-cookie"


def test_resolve_cookie_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("GOODREADS_COOKIE", "env-cookie")
    args = Namespace(cookie=None, cookie_file=None)
    assert __main__.resolve_cookie(args) == "env-cookie"


def test_resolve_cookie_reads_file_and_strips(tmp_path, monkeypatch):
    monkeypatch.delenv("GOODREADS_COOKIE", raising=False)
    cookie_file = tmp_path / "cookie.txt"
    cookie_file.write_text("  file-cookie\n")
    args = Namespace(cookie=None, cookie_file=str(cookie_file))
    assert __main__.resolve_cookie(args) == "file-cookie"


def test_resolve_cookie_none_when_unset(monkeypatch):
    monkeypatch.delenv("GOODREADS_COOKIE", raising=False)
    args = Namespace(cookie=None, cookie_file=None)
    assert __main__.resolve_cookie(args) is None


def test_resolve_cookie_exits_when_file_missing(monkeypatch):
    monkeypatch.delenv("GOODREADS_COOKIE", raising=False)
    args = Namespace(cookie=None, cookie_file="/no/such/cookie/file")
    with pytest.raises(SystemExit):
        __main__.resolve_cookie(args)


# End-to-end CLI: argument parsing through file output.


def _run_cli(monkeypatch, *argv):
    monkeypatch.delenv("GOODREADS_COOKIE", raising=False)
    monkeypatch.setattr(sys, "argv", ["scraper", *argv])
    __main__.main()


def test_cli_version_prints_and_exits(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["goodreads-user-scraper", "--version"])
    with pytest.raises(SystemExit) as exc:
        __main__.main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip().endswith(__version__)


def test_cli_writes_user_json(tmp_path, monkeypatch, mock_get_soup):
    mock_get_soup({"user/show": "profile.html"})
    _run_cli(
        monkeypatch,
        "--user_id",
        "54739262",
        "--output_dir",
        str(tmp_path),
        "--skip_shelves",
    )

    data = json.loads((tmp_path / "user.json").read_text())
    assert data["user_id"] == "54739262"
    assert data["user_name"] == "Yash Totale"


def test_cli_skip_user_info_writes_nothing(tmp_path, monkeypatch):
    _run_cli(
        monkeypatch,
        "--user_id",
        "54739262",
        "--output_dir",
        str(tmp_path),
        "--skip_user_info",
        "--skip_shelves",
    )

    assert not (tmp_path / "user.json").exists()


def test_cli_full_run_writes_user_and_books(tmp_path, monkeypatch, mock_get_soup):
    # A cookie enables shelves. Only the "read" shelf has content; every other
    # shelf page resolves to the empty terminator.
    mock_get_soup(
        {
            "user/show": "profile.html",
            "shelf=read&page=1": "shelf_read.html",
            "page=": "shelf_empty.html",
            "book/show": "book.html",
        }
    )
    _run_cli(
        monkeypatch,
        "--user_id",
        "54739262",
        "--output_dir",
        str(tmp_path),
        "--cookie",
        "fake-cookie",
        "--skip_authors",
    )

    user_data = json.loads((tmp_path / "user.json").read_text())
    assert user_data["user_name"] == "Yash Totale"

    # Field-level parsing is pinned by the parser and process_book tests; here we
    # only confirm the pipeline produced the book record from the right shelf.
    book_path = tmp_path / "books" / "211721806-dungeon-crawler-carl.json"
    book = json.loads(book_path.read_text())
    assert book["book_title"] == "Dungeon Crawler Carl"
    assert book["shelves"] == ["read"]
