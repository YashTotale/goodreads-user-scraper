import argparse
import asyncio
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.text import Text

from scraper import http, shelves, user

console = Console()


async def scrape_user(args: argparse.Namespace, cookie: str | None):
    http.init_session(cookie)
    try:
        profile = await user.get_user_info(args)
        await shelves.get_all_shelves(args, profile)
        path = str(args.output_dir.resolve())
        line = Text("📁  Saved to ")
        line.append(path, style=f"link file://{path}")
        console.print(line)
    finally:
        await http.close_session()


def resolve_cookie(args: argparse.Namespace) -> str | None:
    if args.cookie:
        return args.cookie
    env = os.environ.get("GOODREADS_COOKIE")
    if env:
        return env
    if args.cookie_file:
        path = Path(args.cookie_file)
        if not path.exists():
            sys.exit(f"❌ --cookie_file path does not exist: {path}")
        return path.read_text().strip()
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, required=True)
    parser.add_argument("--output_dir", type=Path, default=Path("goodreads-data"))
    parser.add_argument("--skip_user_info", action="store_true")
    parser.add_argument("--skip_shelves", action="store_true")
    parser.add_argument("--skip_authors", action="store_true")
    parser.add_argument("--cookie", type=str, default=None)
    parser.add_argument("--cookie_file", type=str, default=None)

    args = parser.parse_args()

    if args.skip_user_info and args.skip_shelves:
        console.print(
            "⚠️  Nothing to do: --skip_user_info and --skip_shelves are both set."
        )
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    cookie = resolve_cookie(args)

    asyncio.run(scrape_user(args, cookie))


if __name__ == "__main__":
    main()
