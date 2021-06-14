import argparse
import json
from urllib.request import urlopen

import bs4

from scraper import scrape_book

RATING_STARS_DICT = {'it was amazing': 5,
                     'really liked it': 4,
                     'liked it': 3,
                     'it was ok': 2,
                     'did not like it': 1,
                     '': None}


def create_url(user_id, shelf, page):
    return 'https://www.goodreads.com/review/list/' + user_id + '?shelf=' + shelf + '&page=' + str(page) + '&print=true'


def get_id(book_row):
    cell = book_row.find('td', {'class': 'field title'})
    title_href = cell.find('div', {'class': 'value'}).find('a')
    return title_href.attrs.get('href').split('/')[-1]


def get_rating(book_row):
    cell = book_row.find('td', {'class': 'field rating'})
    str_rating = cell.find('div', {'class': 'value'}).find('span').attrs.get('title')
    return RATING_STARS_DICT.get(str_rating)


def get_dates_read(book_row):
    cell = book_row.find('td', {'class': 'field date_read'})
    dates = cell.find('div', {'class': 'value'}).findChildren('div', {'class': 'date_row'})
    date_arr = []
    for date in dates:
        date_text = date.text.strip()
        if date_text != 'not set':
            date_arr += [date_text]
    return date_arr


def scrape_user(user_id):
    page = 1
    while True:
        url = create_url(user_id, 'read', page)
        source = urlopen(url)
        soup = bs4.BeautifulSoup(source, 'html.parser')

        no_content = soup.find('div', {'class': 'greyText nocontent stacked'})
        if no_content:
            break

        books_table = soup.find('tbody', {'id': 'booksBody'})
        book_rows = books_table.findChildren('tr', recursive=False)

        for book_row in book_rows:
            book_id = get_id(book_row)
            book = scrape_book.scrape_book(book_id)
            book['rating'] = get_rating(book_row)
            book['dates_read'] = get_dates_read(book_row)
            json.dump(book, open('books/read/' + book.get('book_id_title') + '.json', 'w'), indent=2)
            print("🎉 Scraped " + book.get('book_id_title'))

        page += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', type=str)
    args = parser.parse_args()

    scrape_user(args.user_id)


if __name__ == '__main__':
    main()
