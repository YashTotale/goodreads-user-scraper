import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="goodreads-user-scraper",
    version="1.2.3",
    description="Scrape user data from Goodreads",
    long_description=README,
    long_description_content_type="text/markdown",
    project_urls={
        "Source Code": "https://github.com/YashTotale/goodreads-user-scraper",
        "Bug Tracker": "https://github.com/YashTotale/goodreads-user-scraper/issues",
        "Release Notes": "https://github.com/YashTotale/goodreads-user-scraper/releases",
    },
    author="Yash Totale",
    author_email="totaleyash@gmail.com",
    license="MIT",
    keywords=[
        "Goodreads",
        "Web Scraper",
        "CLI",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
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
