"""
This is where the cli is called.
We can run our save and other commands from this file
"""
import os
import logging
import click

from .scraper import shelves
from .scraper import user

LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}  #: a mapping of `verbose` option counts to logging levels


LOGGING_LEVELS_NAMES = {
    0: "NOT SET",
    1: "ERROR",
    2: "WARNING",
    3: "INFO",
    4: "DEBUG",
}


# Create the config object
class Config:  # pylint: disable=too-few-public-methods
    """
    This is a object used to store configs, we will
    eventually pass down via decorators.

    Verbose: Enables verbose mode, with extra "v"'s providing better verbose output
    """

    def __init__(self) -> None:
        self.verbose: int = 0


# Create the decorator to pass the config object down
pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "--verbose", "-v", count=True, help="Enable verbose output, (up to -vvvv)"
)
@pass_config
def cli(config: Config, verbose: int):
    """This runs the cli wrapper and is apart of the click library"""

    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logging.basicConfig(
            level=LOGGING_LEVELS[verbose]
            if verbose in LOGGING_LEVELS
            else logging.DEBUG
        )
        click.echo(
            click.style(
                f"Verbose logging is enabled \n"
                f"(LEVEL: {LOGGING_LEVELS_NAMES[verbose]})",
                fg="yellow",
            )
        )
    config.verbose = verbose


@cli.command()
@click.argument("user_id", required=True)
@click.argument("output_dir", type=click.Path(writable=True))
@click.option("--skip_user_info", is_flag=True, default=False)
@click.option("--skip_shelves", is_flag=True)
@click.option("--skip_authors", is_flag=True)
@pass_config
def getdata(
    config: Config, user_id, output_dir, skip_user_info, skip_shelves, skip_authors
):
    """Gets users goodreads library and outputs as a json file.

    Examples:
        >>> getdata 143957887 foo.json
        >>> getdata --shelve "toread" 143957887 bar.json
        >>> getdata -s "toread" -s "tobuy" 143957887 bar.json
        >>> getdata -vvvv 143957887

    Args:
        user_id (str): The user id of the user you wish to use.
        out (str optional): The output file.
            Defaults to Stdout.

    Returns:
        #TODO Fill this out when you know what it will look like
    """
    args = None
    os.makedirs(output_dir, exist_ok=True)
    scrape_user(
        user_id=user_id,
        skip_user_info=skip_user_info,
        output_dir=output_dir,
        skip_shelves=skip_shelves,
    )


def scrape_user(user_id, skip_user_info, output_dir, skip_shelves):
    if not skip_user_info:
        user.get_user_info(user_id=user_id, output_dir=output_dir)
        # TODO: Get this to work with click
        shelves.get_all_shelves(
            user_id=user_id, skip_shelves=skip_shelves, output_dir=output_dir
        )
