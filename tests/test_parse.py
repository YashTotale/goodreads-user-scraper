from bs4 import BeautifulSoup
import pytest

from scraper.parse import ElementNotFound, find_tag, find_tag_opt


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def test_find_tag_returns_matching_tag():
    soup = _soup("<div><span id='x'>hi</span></div>")
    assert find_tag(soup, "span").text == "hi"


def test_find_tag_raises_when_missing():
    soup = _soup("<div></div>")
    with pytest.raises(ElementNotFound):
        find_tag(soup, "span")


def test_find_tag_opt_returns_none_when_missing():
    assert find_tag_opt(_soup("<div></div>"), "span") is None


def test_find_tag_opt_returns_tag_when_present():
    tag = find_tag_opt(_soup("<div><a href='/x'>y</a></div>"), "a")
    assert tag is not None and tag.get("href") == "/x"
