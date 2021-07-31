from argparse import Namespace
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re


def get_user_name(soup: BeautifulSoup):
    return soup.find(id="profileNameTopHeading").text.strip()


def get_num_ratings(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return int(re.findall(r"\d+", container.find("a").text)[0])


def get_avg_rating(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return float(re.findall(r"\d*\.?\d+", container.find_all("a")[1].text)[0])


def get_num_reviews(soup: BeautifulSoup):
    container = soup.find("div", attrs={"class": "profilePageUserStatsInfo"})
    return int(re.findall(r"\d+", container.find_all("a")[2].text)[0])


def get_user_info(args: Namespace):
    if args.skip_user_info:
        return

    print("Scraping user...")

    user_id: str = args.user_id
    output_file: str = args.output_dir + "user.json"
    url = "https://www.goodreads.com/user/show/" + user_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

    data = {
        "user_id": user_id,
        "user_name": get_user_name(soup),
        "num_ratings": get_num_ratings(soup),
        "average_rating": get_avg_rating(soup),
        "num_reviews": get_num_reviews(soup),
    }

    file = open(output_file, "w")
    json.dump(data, file, indent=2)
    file.close()

    print("👤 Scraped user")

    if not args.skip_shelves:
        print()
