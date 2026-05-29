import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="goodreads-user-scraper",
    version="1.2.5",
    description="Scrape Goodreads User Data: Profile, Book Shelves, Books, Authors",
    long_description=README,
    long_description_content_type="text/markdown",
    project_urls={
        "Homepage": "https://github.com/YashTotale/goodreads-user-scraper",
        "Source Code": "https://github.com/YashTotale/goodreads-user-scraper",
        "Bug Tracker": "https://github.com/YashTotale/goodreads-user-scraper/issues",
        "Release Notes": "https://github.com/YashTotale/goodreads-user-scraper/releases",
    },
    author="Yash Totale",
    author_email="totaleyash@gmail.com",
    license="MIT",
    keywords=[
        "Goodreads",
        "books",
        "reading",
        "Web Scraper",
        "CLI",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Utilities",
    ],
    python_requires=">=3.13",
    packages=["scraper"],
    include_package_data=True,
    install_requires=["beautifulsoup4", "requests"],
    extras_require={
        "dev": [
            "black",
            "bump-my-version",
            "pre-commit",
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "goodreads-user-scraper=scraper.__main__:main",
        ]
    },
)
