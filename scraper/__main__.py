import argparse
import json
from urllib.request import urlopen
import os
import bs4

from scraper import scrape_book
from scraper import shelf


def scrape_user(args):
    shelf.get_all_shelves(args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="goodreads-data")
    args = parser.parse_args()

    args.output_dir = (
        args.output_dir if args.output_dir.endswith("/") else args.output_dir + "/"
    )

    os.makedirs(args.output_dir, exist_ok=True)
    scrape_user(args)


if __name__ == "__main__":
    main()
