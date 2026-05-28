from bs4 import BeautifulSoup

from scraper import http

# _detect_auth_failure only needs tiny hand-built HTML, so these tests skip fixtures.


def make_soup(html):
    return BeautifulSoup(html, "html.parser")


def test_detects_third_party_sign_in_by_id():
    assert http._detect_auth_failure(
        make_soup('<div id="third_party_sign_in"></div>'), ""
    )


def test_detects_third_party_sign_in_by_class():
    assert http._detect_auth_failure(
        make_soup('<div class="third_party_sign_in"></div>'), ""
    )


def test_detects_cookie_error_text():
    body = "Something is wrong with your Goodreads cookie"
    assert http._detect_auth_failure(make_soup(""), body)


def test_clean_page_is_not_auth_failure():
    assert not http._detect_auth_failure(
        make_soup("<div>normal page</div>"), "normal page"
    )
