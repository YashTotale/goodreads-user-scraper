"""Re-runnable capture of the Goodreads HTML fixtures the test suite asserts against.

Run after Goodreads markup changes, or to add a new fixture, then re-check the
parser tests. Reuses the production cookie resolution + session so the fetched
HTML matches what the scraper itself sees. CSRF/session tokens are scrubbed
before writing (the reading data itself is already public on the profile).

    python scripts/capture_fixtures.py [--cookie ... | --cookie_file ...]

Profile/book/author pages are captured both anonymously and with the cookie, so
the parser tests pin both the logged-out and logged-in paths (Goodreads serves
different markup to each). Shelf pages require a cookie.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

from scraper import http
from scraper.__main__ import resolve_cookie

USER_ID = "54739262"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def book_url(book_id):
    return "https://www.goodreads.com/book/show/" + book_id


def author_url(author_id):
    return "https://www.goodreads.com/author/show/" + author_id


def shelf_url(shelf, page=1):
    return (
        "https://www.goodreads.com/review/list/"
        + USER_ID
        + f"?shelf={shelf}&page={page}&print=true"
    )


# (fixture_name, url, mode). mode is "anon" (logged-out), "auth" (logged-in), or
# "shelf" (logged-in, skipped when no cookie). Edit the book/author ids to real
# pages that exhibit each variant; leave an entry out if no real example exists
# rather than fabricating one.
PROFILE_URL = "https://www.goodreads.com/user/show/" + USER_ID
BOOK_ID = "211721806-dungeon-crawler-carl"
AUTHOR_ID = "3137322.Fyodor_Dostoevsky"
FIXTURES = [
    # Happy-path pages, captured both logged-out and logged-in.
    ("profile.html", PROFILE_URL, "auth"),
    ("profile_anon.html", PROFILE_URL, "anon"),
    ("book.html", book_url(BOOK_ID), "auth"),
    ("book_anon.html", book_url(BOOK_ID), "anon"),
    ("author.html", author_url(AUTHOR_ID), "auth"),
    ("author_anon.html", author_url(AUTHOR_ID), "anon"),
    # Edge-case pages exercising the None/empty parser branches.
    # Sparse book: no description, no genres, no series, zero ratings/reviews.
    ("book_minimal.html", book_url("130679210-the-harris-ingram-experiment"), "anon"),
    # Author with neither a photo nor a bio.
    ("author_no_image.html", author_url("2814983.Charles_E_Bolton"), "anon"),
    # Shelf pages are deterministic given the user id.
    ("shelf_read.html", shelf_url("read"), "shelf"),
    ("shelf_to_read.html", shelf_url("to-read"), "shelf"),
    ("shelf_empty.html", shelf_url("read", page=9999), "shelf"),
]

_SCRUB = [
    (re.compile(r'(<meta[^>]*name="csrf-token"[^>]*content=")[^"]*'), r"\1REDACTED"),
    (re.compile(r'(name="authenticity_token"[^>]*value=")[^"]*'), r"\1REDACTED"),
    (
        re.compile(r'(value="[^"]*"[^>]*name="authenticity_token")'),
        r'value="REDACTED" name="authenticity_token"',
    ),
    # Inline-JS CSRF token: authenticity_token=' + encodeURIComponent('<token>') (HTML-escaped).
    (
        re.compile(r"(authenticity_token=&#39; \+ encodeURIComponent\(&#39;)[^&]*"),
        r"\1REDACTED",
    ),
    (re.compile(r'("csrfToken"\s*:\s*")[^"]*'), r"\1REDACTED"),
    # Amazon UE analytics session/request ids (ue_mid is a public marketplace id).
    (re.compile(r'(\bue_sid\s*=\s*")[^"]*'), r"\1REDACTED"),
    (re.compile(r'(\bue_id\s*=\s*")[^"]*'), r"\1REDACTED"),
    # Goodreads RSS feed access key (account-scoped, not carried in the cookie).
    (re.compile(r'(_rss/[^"<>\s]*?[?&](?:amp;)?key=)[A-Za-z0-9_\-]+'), r"\1REDACTED"),
]


# Cookie values shorter than this are skipped — too generic to redact safely.
MIN_COOKIE_VALUE_LEN = 12


def scrub(html, cookie=None):
    for pattern, repl in _SCRUB:
        html = pattern.sub(repl, html)
    # Redact any session value that leaked from the cookie into the page (e.g. ccsid as ue_sid).
    for pair in (cookie or "").split(";"):
        value = pair.partition("=")[2].strip()
        if len(value) >= MIN_COOKIE_VALUE_LEN:
            html = html.replace(value, "REDACTED")
    return html


async def _capture(cookie):
    # Anonymous pass first, then the cookie-bearing pass. dict.fromkeys collapses
    # the passes to one when no cookie is given (both would be the anon pass).
    for session_cookie in dict.fromkeys((None, cookie)):
        http.init_session(session_cookie)
        try:
            wants_cookie = session_cookie is not None
            for name, url, mode in FIXTURES:
                if (mode == "anon") == wants_cookie:
                    continue
                if mode == "shelf" and not http.has_cookie():
                    print(f"⏭️  {name}: needs a cookie (skipped)")
                    continue
                html = await http.get_html(url)
                # Goodreads serves login/error pages with a 200, so apply the same
                # auth-failure check production does before overwriting a fixture.
                if http.has_cookie() and http._detect_auth_failure(
                    BeautifulSoup(html, "html.parser"), html
                ):
                    sys.exit(
                        f"❌ {name}: got an auth-failure page — cookie may be expired. Re-grab it and retry."
                    )
                (FIXTURES_DIR / name).write_text(
                    scrub(html, session_cookie), encoding="utf-8"
                )
                print(f"✅ {name}")
        finally:
            await http.close_session()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cookie", type=str, default=None)
    default_cookie_file = Path(".goodreads-cookie")
    parser.add_argument(
        "--cookie_file",
        type=str,
        default=str(default_cookie_file) if default_cookie_file.exists() else None,
    )
    args = parser.parse_args()

    cookie = resolve_cookie(args)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    asyncio.run(_capture(cookie))


if __name__ == "__main__":
    main()
