import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="goodreads-user-scraper",
    version="0.0.7",
    description="Scrape user data from Goodreads",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/YashTotale/goodreads-user-scraper",
    author="Yash Totale",
    author_email="totaleyash@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["scraper"],
    include_package_data=True,
    install_requires=["beautifulsoup4"],
    entry_points={
        "console_scripts": [
            "goodreads-user-scraper=scraper.__main__:main",
        ]
    },
)
