from argparse import Namespace
import json
import re

from bs4 import BeautifulSoup
from rich.console import Console

from scraper import http

console = Console()


def get_user_name(soup: BeautifulSoup):
    return soup.find(id="profileNameTopHeading").text.strip().split("\n")[0].strip()


def get_num_ratings(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return int(re.findall(r"\d+", container.find("a").text)[0])


def get_avg_rating(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return float(re.findall(r"\d*\.?\d+", container.find_all("a")[1].text)[0])


def get_num_reviews(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return int(re.findall(r"\d+", container.find_all("a")[2].text)[0])


async def get_user_info(args: Namespace):
    if args.skip_user_info:
        return

    user_id: str = args.user_id
    output_file = args.output_dir / "user.json"
    url = "https://www.goodreads.com/user/show/" + user_id
    soup = await http.get_soup(url)

    data = {
        "user_id": user_id,
        "user_name": get_user_name(soup),
        "num_ratings": get_num_ratings(soup),
        "average_rating": get_avg_rating(soup),
        "num_reviews": get_num_reviews(soup),
    }

    with open(output_file, "w") as file:
        json.dump(data, file, indent=2)

    # markup=False so a bracket in the user's name isn't parsed as rich markup.
    console.print(
        f"👤  {data['user_name']} · {data['num_ratings']} ratings · {data['num_reviews']} reviews",
        markup=False,
    )

    if not args.skip_shelves:
        print()
