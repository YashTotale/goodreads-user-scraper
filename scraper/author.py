import asyncio
import re
from typing import Any

from bs4 import BeautifulSoup

from scraper import http
from scraper.parse import find_tag, find_tag_opt

# Concurrent callers wanting the same author await one shared fetch task.
_tasks: dict[str, asyncio.Task[dict[str, Any]]] = {}


def get_id_number(author_id: str) -> str:
    match = re.compile("([^.-]+)").search(author_id)
    assert match is not None
    return match.group()


def get_author_description(soup: BeautifulSoup, id_number: str) -> str | None:
    cell = find_tag_opt(soup, "span", {"id": "freeTextauthor" + id_number})
    return cell.text.strip() if cell else None


def get_author_image(soup: BeautifulSoup, author_name: str) -> str | None:
    cell = find_tag_opt(soup, "img", {"alt": author_name, "itemprop": "image"})
    if cell is None:
        return None
    src = cell.get("src")
    return src if isinstance(src, str) else None


async def scrape_author(author_id: str) -> dict[str, Any]:
    task = _tasks.get(author_id)
    if task is None:
        task = asyncio.create_task(_scrape_author(author_id))
        _tasks[author_id] = task
    try:
        return await task
    except Exception:
        _tasks.pop(author_id, None)  # don't cache a failed fetch; allow a retry
        raise


async def _scrape_author(author_id: str) -> dict[str, Any]:
    url = "https://www.goodreads.com/author/show/" + author_id
    soup = await http.get_soup(url)

    author_name = find_tag(soup, "span", {"itemprop": "name"}).text.strip()
    id_number = get_id_number(author_id)

    return {
        "author_id_title": author_id,
        "author_id": id_number,
        "author_name": author_name,
        "author_url": url,
        "author_image": get_author_image(soup, author_name),
        "author_description": get_author_description(soup, id_number),
    }
