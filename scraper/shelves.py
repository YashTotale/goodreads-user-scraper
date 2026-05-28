from argparse import Namespace
import json
import re

from scraper import books, http


def fetch_shelf_page(user_id, shelf, page):
    url = (
        "https://www.goodreads.com/review/list/"
        + user_id
        + "?shelf="
        + shelf
        + "&page="
        + str(page)
        + "&print=true"
    )
    return http.get_soup(url)


def get_id(book_row):
    cell = book_row.find("td", {"class": "field title"})
    title_href = cell.find("div", {"class": "value"}).find("a")
    return title_href.attrs.get("href").split("/")[-1]


def get_rating(book_row):
    stars = book_row.find("td", {"class": "field rating"}).find(
        "div", {"class": "stars"}
    )
    rating = int(stars.get("data-rating", 0)) if stars else 0
    return rating or None


def get_dates_read(book_row):
    cell = book_row.find("td", {"class": "field date_read"})
    dates = cell.find("div", {"class": "value"}).findChildren(
        "div", {"class": "date_row"}
    )
    date_arr = []
    for date in dates:
        date_text = date.text.split("\n")[0].strip()
        if date_text and date_text != "not set":
            date_arr += [date_text]
    return date_arr


def get_shelf(args: Namespace, shelf: str):
    print("Scraping '" + shelf + "' shelf...")
    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    page = 1

    while True:
        soup = fetch_shelf_page(user_id, shelf, page)

        no_content = soup.find("div", {"class": "greyText nocontent stacked"})
        if no_content:
            break

        books_table = soup.find("tbody", {"id": "booksBody"})
        book_rows = books_table.findChildren("tr", recursive=False)

        # Loop through all books in the page
        for book_row in book_rows:
            try:
                book_id = get_id(book_row)
                file_path = output_dir / f"{book_id}.json"

                book = None
                changed = False

                # If the book has already been scraped, just add the shelf
                if file_path.exists():
                    with open(file_path, "r") as file:
                        book = json.load(file)
                    if shelf not in book["shelves"]:
                        book["shelves"].append(shelf)
                        print("✅ Updated " + book_id)
                        changed = True
                # If not already scraped, scrape the book and add the shelf
                else:
                    book = books.scrape_book(book_id, args)
                    book["rating"] = get_rating(book_row)
                    book["dates_read"] = get_dates_read(book_row)
                    book["shelves"] = [shelf]
                    print("🎉 Scraped " + book_id)
                    changed = True

                if changed:
                    with open(file_path, "w") as file:
                        json.dump(book, file, indent=2)
            except Exception as e:
                print(f"⚠️  Skipped book on page {page}: {e}")

        page += 1

    print()


def get_all_shelves(args: Namespace):
    if args.skip_shelves:
        return

    if not http.has_cookie():
        print(
            "⚠️  Skipping shelves: Goodreads requires login to view shelf data.\n"
            "   To scrape shelves, provide your Goodreads session cookie via one of:\n"
            '     --cookie "<cookie string>"\n'
            "     GOODREADS_COOKIE=<cookie string>   (environment variable)\n"
            "     --cookie_file <path-to-file>\n"
            "   See the README for how to grab the cookie from your browser.\n"
            "   Pass --skip_shelves to suppress this message."
        )
        return

    user_id: str = args.user_id
    output_dir = args.output_dir / "books"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = http.get_soup(url)

    output_dir.mkdir(parents=True, exist_ok=True)

    shelves_div = soup.find("div", {"id": "shelves"})
    shelf_links = shelves_div.findChildren("a")

    for link in shelf_links:
        base_url = link.attrs.get("href")
        shelf: str = re.search(r"\?shelf=([^&]+)", base_url).group(1)
        get_shelf(args, shelf)
