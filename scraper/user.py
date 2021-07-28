from argparse import Namespace
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup


def get_user_name(soup: BeautifulSoup):
    return soup.find(id="profileNameTopHeading").text.strip()


def get_user_info(args: Namespace):
    if args.skip_user_info:
        return

    print("Scraping user...")

    user_id: str = args.user_id
    output_file: str = args.output_dir + "user.json"
    url = "https://www.goodreads.com/user/show/" + user_id
    source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

    data = {"user_id": user_id, "user_name": get_user_name(soup)}

    file = open(output_file, "w")
    json.dump(data, file, indent=2)
    file.close()

    print("👤 Scraped user")
    print()
