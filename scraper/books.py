"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from argparse import Namespace

from scraper import author


# def get_rating_distribution(soup: BeautifulSoup):
#     distribution = re.findall(r"renderRatingGraph\([\s]*\[[0-9,\s]+", str(soup))[0]
#     distribution = " ".join(distribution.split())
#     distribution = [int(c.strip()) for c in distribution.split("[")[1].split(",")]
#     distribution_dict = {
#         5: distribution[0],
#         4: distribution[1],
#         3: distribution[2],
#         2: distribution[3],
#         1: distribution[4],
#     }
#     return distribution_dict


def get_author_id(soup: BeautifulSoup):
    author = soup.find("div", {"class": "ContributorLinksList"}).find("a")
    author_url = author.attrs.get("href")
    return author_url.split("/")[-1]


def get_genres(soup: BeautifulSoup):
    genres = []
    genre_links = (
        soup.find("div", {"data-testid": "genresList"})
        .find("ul")
        .find("span")
        .find_all("a")
    )

    for link in genre_links:
        genre = link.find("span").text
        genres.append(genre)
    return genres


def get_average_rating(soup: BeautifulSoup):
    average_rating = soup.find(
        "div", {"class": "RatingStatistics__rating"}
    ).text.strip()

    if average_rating:
        return float(average_rating)
    return ""


def get_num_reviews(soup: BeautifulSoup):
    num_reviews = soup.find("span", {"data-testid": "reviewsCount"})

    if num_reviews:
        num_reviews = re.search(
            r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_reviews.text.strip()
        ).group(1)
        return int(num_reviews.replace(",", ""))
    return ""


def get_num_ratings(soup: BeautifulSoup):
    num_ratings = soup.find("span", {"data-testid": "ratingsCount"})

    if num_ratings:
        num_ratings = re.search(
            r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_ratings.text.strip()
        ).group(1)
        return int(num_ratings.replace(",", ""))
    return ""


def get_num_pages(soup: BeautifulSoup):
    num_pages_container = soup.find("p", {"data-testid": "pagesFormat"})
    num_pages = re.search(
        r"(\d{1,3}(,\d{3})*(\.\d+)?)", num_pages_container.text.strip()
    )

    if num_pages:
        num_pages = num_pages.group(1)
        return int(num_pages.replace(",", ""))
    return None


def get_year_first_published(soup: BeautifulSoup):
    year_first_published = soup.find("p", {"data-testid": "publicationInfo"})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search(r"([0-9]{3,4})", year_first_published).group(1)
    else:
        return None


def get_series_uri(soup: BeautifulSoup):
    title_section = soup.find("h1", {"data-testid": "bookTitle"}).parent
    series_container = title_section.find("h3")

    if series_container:
        return series_container.find("a").get("href")
    else:
        return None


# def get_series_name(soup: BeautifulSoup):
#     title_section = soup.find("h1", {"data-testid": "bookTitle"}).parent
#     series_container = title_section.find("h3")

#     if series_container:
#         series_name = re.search(r"\((.*?)\)", series_container.find("a").text).group(1)
#         return series_name
#     else:
#         return None


def get_image(soup: BeautifulSoup):
    return soup.find("img", {"class": "ResponsiveImage"}).attrs.get("src")


def get_description(soup: BeautifulSoup):
    return soup.find("div", {"data-testid": "description"}).findAll("span")[-1].text


def get_title(soup: BeautifulSoup):
    return " ".join(soup.find("h1", {"data-testid": "bookTitle"}).text.split())


def get_id(book_id: str):
    pattern = re.compile("([^.-]+)")
    return pattern.search(book_id).group()


def scrape_book(book_id: str, args: Namespace):
    url = "https://www.goodreads.com/book/show/" + book_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

    book = {
        "book_id_title": book_id,
        "book_id": get_id(book_id),
        "book_title": get_title(soup),
        "book_description": get_description(soup),
        "book_url": url,
        "book_image": get_image(soup),
        # "book_series": get_series_name(soup),
        "book_series_uri": get_series_uri(soup),
        "year_first_published": get_year_first_published(soup),
        "num_pages": get_num_pages(soup),
        "genres": get_genres(soup),
        "num_ratings": get_num_ratings(soup),
        "num_reviews": get_num_reviews(soup),
        "average_rating": get_average_rating(soup),
        # "rating_distribution": get_rating_distribution(soup),
    }

    if not args.skip_authors:
        book["author"] = author.scrape_author(get_author_id(soup))

    return book
