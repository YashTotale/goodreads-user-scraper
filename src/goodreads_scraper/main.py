import argparse
import os

from .scraper import shelves
from .scraper import user



def scrape_user(args: argparse.Namespace):
    user.get_user_info(args)
    shelves.get_all_shelves(args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="goodreads-data")
    parser.add_argument("--skip_user_info", type=bool, default=False)
    parser.add_argument("--skip_shelves", type=bool, default=False)
    parser.add_argument("--skip_authors", type=bool, default=False)

    args = parser.parse_args()

    args.output_dir = (
        args.output_dir if args.output_dir.endswith("/") else args.output_dir + "/"
    )

    os.makedirs(args.output_dir, exist_ok=True)
    scrape_user(args)


if __name__ == "__main__":
    main()
