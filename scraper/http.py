"""Shared async HTTP session. Optionally carries a Goodreads cookie."""

import asyncio
import email.utils
import random
import sys
from datetime import datetime, timezone

import aiohttp
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 30
MAX_CONCURRENCY = 32
MAX_RETRIES = 4
BACKOFF_BASE = 1.0  # seconds
MAX_BACKOFF = 30.0  # cap per sleep, also caps a server-sent Retry-After
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


class FetchError(Exception):
    def __init__(self, url: str):
        super().__init__(
            f"Failed to fetch {url} after {MAX_RETRIES} retries — "
            "Goodreads may be rate-limiting; try again later."
        )


def _is_transient_status(status: int) -> bool:
    return status == 429 or 500 <= status < 600


def _parse_retry_after(header: str | None) -> float | None:
    if not header:
        return None
    if header.isdigit():
        return int(header)
    try:  # Retry-After may instead be an HTTP-date
        retry_at = email.utils.parsedate_to_datetime(header)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


def _backoff(attempt: int) -> float:
    return random.uniform(0, min(MAX_BACKOFF, BACKOFF_BASE * 2**attempt))


async def get_html(url: str) -> str:
    assert (
        _session is not None and _semaphore is not None
    ), "init_session() must be called first"
    # Retries sleep while holding the semaphore so throttling collapses concurrency.
    async with _semaphore:
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with _session.get(url) as response:
                    if not _is_transient_status(response.status):
                        response.raise_for_status()
                        return await response.text()
                    delay = _parse_retry_after(response.headers.get("Retry-After"))
            except (
                asyncio.TimeoutError,
                aiohttp.ClientConnectionError,
                aiohttp.ClientPayloadError,
            ):
                delay = None
            if attempt == MAX_RETRIES:
                raise FetchError(url)
            await asyncio.sleep(
                min(delay, MAX_BACKOFF) if delay is not None else _backoff(attempt)
            )


async def get_soup(url: str) -> BeautifulSoup:
    html = await get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    if _has_cookie and _detect_auth_failure(soup, html):
        sys.exit(
            "❌ Cookie appears invalid or expired. Re-grab the Cookie header value from your browser DevTools and try again."
        )
    return soup
