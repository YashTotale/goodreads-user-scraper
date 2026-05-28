"""Shared HTTP session. Optionally carries a Goodreads cookie."""

import sys

from bs4 import BeautifulSoup
import requests

DEFAULT_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_session: requests.Session | None = None
_has_cookie: bool = False


def init_session(cookie: str | None) -> None:
    global _session, _has_cookie
    _session = requests.Session()
    _session.headers["User-Agent"] = USER_AGENT
    if cookie:
        _session.headers["Cookie"] = cookie
        _has_cookie = True


def has_cookie() -> bool:
    return _has_cookie


def _detect_auth_failure(soup: BeautifulSoup, body: str) -> bool:
    if soup.select_one("div#third_party_sign_in, div.third_party_sign_in"):
        return True
    if "wrong with your Goodreads cookie" in body:
        return True
    return False


def get_soup(url: str) -> BeautifulSoup:
    assert _session is not None, "init_session() must be called first"
    response = _session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    if _has_cookie and _detect_auth_failure(soup, response.text):
        sys.exit(
            "❌ Cookie appears invalid or expired. Re-grab the Cookie header value from your browser DevTools and try again."
        )
    return soup
