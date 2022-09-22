import re
from urllib.request import urlopen
from bs4 import BeautifulSoup


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


def scrape_author(author_id):
    url = "https://www.goodreads.com/author/show/" + author_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

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
