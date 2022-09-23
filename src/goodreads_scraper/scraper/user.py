import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from pathlib import Path


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


def get_user_info(user_id, output_dir):

    print("Scraping user...")

    output_file = f"{output_dir}/user-{user_id}.json"
    if Path(output_file).is_file():
        print (f"User Data already exists for user: {user_id}...skipping")
        return
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