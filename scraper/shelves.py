from argparse import Namespace
import asyncio
import json
import re

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from scraper import books, http

PER_PAGE = 100
console = Console()


async def fetch_shelf_page(user_id, shelf, page):
    url = (
        f"https://www.goodreads.com/review/list/{user_id}"
        f"?shelf={shelf}&page={page}&per_page={PER_PAGE}&print=true"
    )
    return await http.get_soup(url)


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
    dates = cell.find("div", {"class": "value"}).find_all("div", {"class": "date_row"})
    date_arr = []
    for date in dates:
        date_text = date.text.strip().split("\n")[0].strip()
        if date_text and date_text != "not set":
            date_arr += [date_text]
    return date_arr


async def collect_shelf_rows(user_id, shelf):
    rows = []
    page = 1
    while True:
        soup = await fetch_shelf_page(user_id, shelf, page)
        if soup.find("div", {"class": "greyText nocontent stacked"}):
            break
        body = soup.find("tbody", {"id": "booksBody"})
        page_rows = body.find_all("tr", recursive=False)
        rows.extend(page_rows)
        # A short page is the last one — no need to fetch an empty terminator page.
        if len(page_rows) < PER_PAGE:
            break
        page += 1
    return rows


def _dedupe_books(shelf_rows):
    books_by_id = {}
    for shelf, page_rows in shelf_rows:
        for row in page_rows:
            try:
                book_id = get_id(row)
            except Exception:
                continue  # skip a malformed row
            entry = books_by_id.get(book_id)
            if entry is None:
                entry = {
                    "shelves": [],
                    "rating": get_rating(row),
                    "dates_read": get_dates_read(row),
                }
                books_by_id[book_id] = entry
            if shelf not in entry["shelves"]:
                entry["shelves"].append(shelf)
    return books_by_id


async def process_book(book_id, info, args, output_dir):
    try:
        file_path = output_dir / f"{book_id}.json"
        if file_path.exists():
            with open(file_path, "r") as file:
                book = json.load(file)
            new_shelves = [s for s in info["shelves"] if s not in book["shelves"]]
            if not new_shelves:
                return
            book["shelves"].extend(new_shelves)
        else:
            book = await books.scrape_book(book_id, args)
            book["rating"] = info["rating"]
            book["dates_read"] = info["dates_read"]
            book["shelves"] = info["shelves"]

        with open(file_path, "w") as file:
            json.dump(book, file, indent=2)
    except Exception as e:
        console.print(f"⚠️  Skipped {book_id}: {e}")


async def get_all_shelves(args: Namespace):
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
    profile = await http.get_soup(url)
    output_dir.mkdir(parents=True, exist_ok=True)

    shelf_links = profile.find("div", {"id": "shelves"}).find_all("a")
    shelf_names = [
        re.search(r"\?shelf=([^&]+)", link.attrs.get("href")).group(1)
        for link in shelf_links
    ]

    with console.status("Discovering shelves…"):
        per_shelf = await asyncio.gather(
            *(collect_shelf_rows(user_id, shelf) for shelf in shelf_names)
        )
    books_by_id = _dedupe_books(list(zip(shelf_names, per_shelf)))
    console.print(f"Found {len(books_by_id)} books across {len(shelf_names)} shelves")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping books", total=len(books_by_id))

        async def run(book_id, info):
            await process_book(book_id, info, args, output_dir)
            progress.advance(task)

        await asyncio.gather(
            *(run(book_id, info) for book_id, info in books_by_id.items())
        )

    console.print(f"✅ {len(books_by_id)} books · {len(shelf_names)} shelves")
