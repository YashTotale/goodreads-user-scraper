"""Shared async HTTP session. Optionally carries a Goodreads cookie."""

import asyncio
import sys

import aiohttp
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 30
MAX_CONCURRENCY = 32
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_session: aiohttp.ClientSession | None = None
_semaphore: asyncio.Semaphore | None = None
_has_cookie: bool = False


def init_session(cookie: str | None) -> None:
    global _session, _semaphore, _has_cookie
    headers = {"User-Agent": USER_AGENT}
    _has_cookie = bool(cookie)
    if cookie:
        headers["Cookie"] = cookie
    _session = aiohttp.ClientSession(
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
        cookie_jar=aiohttp.DummyCookieJar(),
    )
    _semaphore = asyncio.Semaphore(MAX_CONCURRENCY)


async def close_session() -> None:
    global _session
    if _session is not None:
        await _session.close()
        _session = None


def has_cookie() -> bool:
    return _has_cookie


def _detect_auth_failure(soup: BeautifulSoup, body: str) -> bool:
    if soup.select_one("div#third_party_sign_in, div.third_party_sign_in"):
        return True
    if "wrong with your Goodreads cookie" in body:
        return True
    return False


async def get_html(url: str) -> str:
    assert (
        _session is not None and _semaphore is not None
    ), "init_session() must be called first"
    async with _semaphore, _session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def get_soup(url: str) -> BeautifulSoup:
    html = await get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    if _has_cookie and _detect_auth_failure(soup, html):
        sys.exit(
            "❌ Cookie appears invalid or expired. Re-grab the Cookie header value from your browser DevTools and try again."
        )
    return soup
