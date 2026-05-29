import asyncio
import re

from scraper import http

# Concurrent callers wanting the same author await one shared fetch task.
_tasks: dict = {}


def get_id_number(author_id):
    pattern = re.compile("([^.-]+)")
    return pattern.search(author_id).group()


def get_author_description(soup, id_number):
    cell = soup.find("span", {"id": "freeTextauthor" + id_number})
    if cell:
        return cell.text.strip()
    return None


def get_author_image(soup, author_name):
    cell = soup.find("img", {"alt": author_name, "itemprop": "image"})
    if cell:
        return cell.attrs.get("src")
    return None


async def scrape_author(author_id):
    task = _tasks.get(author_id)
    if task is None:
        task = asyncio.create_task(_scrape_author(author_id))
        _tasks[author_id] = task
    try:
        return await task
    except Exception:
        _tasks.pop(author_id, None)  # don't cache a failed fetch; allow a retry
        raise


async def _scrape_author(author_id):
    url = "https://www.goodreads.com/author/show/" + author_id
    soup = await http.get_soup(url)

    author_name = soup.find("span", {"itemprop": "name"}).text.strip()
    id_number = get_id_number(author_id)

    return {
        "author_id_title": author_id,
        "author_id": id_number,
        "author_name": author_name,
        "author_url": url,
        "author_image": get_author_image(soup, author_name),
        "author_description": get_author_description(soup, id_number),
    }
