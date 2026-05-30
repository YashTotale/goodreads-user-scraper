import asyncio

import aiohttp
import pytest
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


# get_html retry/backoff — driven by a fake session so no network or real sleeps run.


class _FakeResponse:
    def __init__(self, status, body="<html>ok</html>", headers=None, text_exc=None):
        self.status = status
        self._body = body
        self.headers = headers or {}
        self._text_exc = text_exc

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientResponseError(None, (), status=self.status)

    async def text(self):
        if self._text_exc is not None:
            raise self._text_exc
        return self._body


class _FakeGet:
    def __init__(self, step):
        self._step = step

    async def __aenter__(self):
        if isinstance(self._step, Exception):
            raise self._step
        return self._step

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    """Yields one queued step (a response or an exception to raise) per get()."""

    def __init__(self, steps):
        self._steps = list(steps)
        self.calls = 0

    def get(self, url):
        self.calls += 1
        return _FakeGet(self._steps.pop(0))


@pytest.fixture
def fake_http(monkeypatch):
    """Install a fake session + recorded, instant sleep; return a setup helper."""
    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(http.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(http, "_semaphore", asyncio.Semaphore(http.MAX_CONCURRENCY))

    def install(steps):
        session = _FakeSession(steps)
        monkeypatch.setattr(http, "_session", session)
        return session, sleeps

    return install


def test_parse_retry_after_reads_integer_seconds():
    assert http._parse_retry_after("5") == 5


def test_parse_retry_after_ignores_missing_or_non_integer():
    assert http._parse_retry_after(None) is None
    assert http._parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") is None


def test_backoff_is_capped_and_non_negative():
    assert 0 <= http._backoff(0) <= http.BACKOFF_BASE
    assert http._backoff(100) <= http.MAX_BACKOFF


def test_is_transient_status():
    assert http._is_transient_status(429)
    assert http._is_transient_status(503)
    assert not http._is_transient_status(404)
    assert not http._is_transient_status(200)


async def test_get_html_retries_transient_status_then_succeeds(fake_http):
    session, sleeps = fake_http([_FakeResponse(503), _FakeResponse(200)])

    assert await http.get_html("https://x") == "<html>ok</html>"
    assert session.calls == 2
    assert len(sleeps) == 1


async def test_get_html_retries_on_timeout_then_succeeds(fake_http):
    session, sleeps = fake_http([asyncio.TimeoutError(), _FakeResponse(200)])

    assert await http.get_html("https://x") == "<html>ok</html>"
    assert session.calls == 2


async def test_get_html_retries_on_payload_error_mid_body(fake_http):
    broken = _FakeResponse(200, text_exc=aiohttp.ClientPayloadError("connection lost"))
    session, sleeps = fake_http([broken, _FakeResponse(200)])

    assert await http.get_html("https://x") == "<html>ok</html>"
    assert session.calls == 2


async def test_get_html_raises_fetcherror_after_exhausting_retries(fake_http):
    session, sleeps = fake_http([_FakeResponse(503)] * (http.MAX_RETRIES + 1))

    with pytest.raises(http.FetchError):
        await http.get_html("https://x")
    assert session.calls == http.MAX_RETRIES + 1
    assert len(sleeps) == http.MAX_RETRIES


async def test_get_html_does_not_retry_non_transient_4xx(fake_http):
    session, sleeps = fake_http([_FakeResponse(404)])

    with pytest.raises(aiohttp.ClientResponseError):
        await http.get_html("https://x")
    assert session.calls == 1
    assert sleeps == []


async def test_get_html_honors_and_caps_retry_after(fake_http):
    session, sleeps = fake_http(
        [_FakeResponse(429, headers={"Retry-After": "999"}), _FakeResponse(200)]
    )

    await http.get_html("https://x")
    assert sleeps == [http.MAX_BACKOFF]
