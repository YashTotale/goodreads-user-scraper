import re
from argparse import Namespace
from typing import Any

from bs4 import BeautifulSoup

from scraper import author, http
from scraper.parse import find_tag, find_tag_opt


def get_author_id(soup: BeautifulSoup) -> str:
    container = find_tag(soup, "div", {"class": "ContributorLinksList"})
    href = find_tag(container, "a").get("href")
    assert isinstance(href, str)
    return href.split("/")[-1]


def get_genres(soup: BeautifulSoup) -> list[str] | None:
    genres_container = find_tag_opt(soup, "div", {"data-testid": "genresList"})
    if genres_container is None:
        return None
    genre_links = find_tag(find_tag(genres_container, "ul"), "span").find_all("a")
    return [find_tag(link, "span").text for link in genre_links]


def get_average_rating(soup: BeautifulSoup) -> float | None:
    average_rating = find_tag(
        soup, "div", {"class": "RatingStatistics__rating"}
    ).text.strip()
    return float(average_rating) if average_rating else None


def get_num_reviews(soup: BeautifulSoup) -> int | None:
    num_reviews = find_tag_opt(soup, "span", {"data-testid": "reviewsCount"})
    if num_reviews is None:
        return None
    match = re.search(r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_reviews.text.strip())
    assert match is not None
    return int(match.group(1).replace(",", ""))


def get_num_ratings(soup: BeautifulSoup) -> int | None:
    num_ratings = find_tag_opt(soup, "span", {"data-testid": "ratingsCount"})
    if num_ratings is None:
        return None
    match = re.search(r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_ratings.text.strip())
    assert match is not None
    return int(match.group(1).replace(",", ""))


def get_num_pages(soup: BeautifulSoup) -> int | None:
    container = find_tag_opt(soup, "p", {"data-testid": "pagesFormat"})
    if container is None:
        return None
    match = re.search(r"(\d{1,3}(,\d{3})*(\.\d+)?)", container.text.strip())
    return int(match.group(1).replace(",", "")) if match else None


def get_year_first_published(soup: BeautifulSoup) -> str | None:
    info = find_tag_opt(soup, "p", {"data-testid": "publicationInfo"})
    if info is None:
        return None
    text = info.string
    assert text is not None
    match = re.search(r"([0-9]{3,4})", text)
    assert match is not None
    return match.group(1)


def get_series_uri(soup: BeautifulSoup) -> str | None:
    title_section = find_tag(soup, "h1", {"data-testid": "bookTitle"}).parent
    assert title_section is not None
    series_container = find_tag_opt(title_section, "h3")
    if series_container is None:
        return None
    href = find_tag(series_container, "a").get("href")
    return href if isinstance(href, str) else None


def get_image(soup: BeautifulSoup) -> str | None:
    src = find_tag(soup, "img", {"class": "ResponsiveImage"}).get("src")
    return src if isinstance(src, str) else None


def get_description(soup: BeautifulSoup) -> str | None:
    description = find_tag_opt(
        find_tag(soup, "div", {"data-testid": "description"}), "span"
    )
    return description.text if description else None


def get_title(soup: BeautifulSoup) -> str:
    return " ".join(find_tag(soup, "h1", {"data-testid": "bookTitle"}).text.split())


def get_id(book_id: str) -> str:
    match = re.compile("([^.-]+)").search(book_id)
    assert match is not None
    return match.group()


async def scrape_book(book_id: str, args: Namespace) -> dict[str, Any]:
    url = "https://www.goodreads.com/book/show/" + book_id
    soup = await http.get_soup(url)

    book: dict[str, Any] = {
        "book_id_title": book_id,
        "book_id": get_id(book_id),
        "book_title": get_title(soup),
        "book_description": get_description(soup),
        "book_url": url,
        "book_image": get_image(soup),
        "book_series_uri": get_series_uri(soup),
        "year_first_published": get_year_first_published(soup),
        "num_pages": get_num_pages(soup),
        "genres": get_genres(soup),
        "num_ratings": get_num_ratings(soup),
        "num_reviews": get_num_reviews(soup),
        "average_rating": get_average_rating(soup),
    }

    if not args.skip_authors:
        book["author"] = await author.scrape_author(get_author_id(soup))

    return book
