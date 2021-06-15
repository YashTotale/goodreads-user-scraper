import argparse
import json
from urllib.request import urlopen
import os
import bs4

from scraper import scrape_book

RATING_STARS_DICT = {
    "it was amazing": 5,
    "really liked it": 4,
    "liked it": 3,
    "it was ok": 2,
    "did not like it": 1,
    "": None,
}


def get_shelf(user_id, shelf, page):
    url = (
        "https://www.goodreads.com/review/list/"
        + user_id
        + "?shelf="
        + shelf
        + "&page="
        + str(page)
        + "&print=true"
    )
    source = urlopen(url)
    return bs4.BeautifulSoup(source, "html.parser")


def get_id(book_row):
    cell = book_row.find("td", {"class": "field title"})
    title_href = cell.find("div", {"class": "value"}).find("a")
    return title_href.attrs.get("href").split("/")[-1]


def get_rating(book_row):
    cell = book_row.find("td", {"class": "field rating"})
    str_rating = cell.find("div", {"class": "value"}).find("span").attrs.get("title")
    return RATING_STARS_DICT.get(str_rating)


def get_dates_read(book_row):
    cell = book_row.find("td", {"class": "field date_read"})
    dates = cell.find("div", {"class": "value"}).findChildren(
        "div", {"class": "date_row"}
    )
    date_arr = []
    for date in dates:
        date_text = date.text.strip()
        if date_text != "not set":
            date_arr += [date_text]
    return date_arr


def get_read_books(args):
    user_id = args.user_id
    output_dir = args.output_dir + "read/"
    page = 1

    os.mkdir(output_dir)

    while True:
        soup = get_shelf(user_id, "read", page)

        no_content = soup.find("div", {"class": "greyText nocontent stacked"})
        if no_content:
            break

        books_table = soup.find("tbody", {"id": "booksBody"})
        book_rows = books_table.findChildren("tr", recursive=False)

        for book_row in book_rows:
            book_id = get_id(book_row)
            book = scrape_book.scrape_book(book_id)
            book["rating"] = get_rating(book_row)
            book["dates_read"] = get_dates_read(book_row)

            file_path = output_dir + book.get("book_id_title") + ".json"
            json.dump(book, open(file_path, "w"), indent=2)

            print("🎉 Scraped " + book.get("book_id_title"))

        page += 1


def scrape_user(args):
    get_read_books(args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="books")
    args = parser.parse_args()

    args.output_dir = (
        args.output_dir if args.output_dir.endswith("/") else args.output_dir + "/"
    )

    os.mkdir(args.output_dir)
    scrape_user(args)


if __name__ == "__main__":
    main()
