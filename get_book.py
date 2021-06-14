"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""
import re
from urllib.request import urlopen
import bs4


def get_genres(soup):
    genres = []
    for node in soup.find_all('div', {'class': 'left'}):
        current_genres = node.find_all('a', {'class': 'actionLinkLite bookPageGenreLink'})
        current_genre = ' > '.join([g.text for g in current_genres])
        if current_genre.strip():
            genres.append(current_genre)
    return genres


def get_series_name(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_name = re.search(r'\((.*?)\)', series.text).group(1)
        return series_name
    else:
        return None


def get_series_uri(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_uri = series.get("href")
        return series_uri
    else:
        return None


def get_rating_distribution(soup):
    distribution = re.findall(r'renderRatingGraph\([\s]*\[[0-9,\s]+', str(soup))[0]
    distribution = ' '.join(distribution.split())
    distribution = [int(c.strip()) for c in distribution.split('[')[1].split(',')]
    distribution_dict = {5: distribution[0],
                         4: distribution[1],
                         3: distribution[2],
                         2: distribution[3],
                         1: distribution[4]}
    return distribution_dict


def get_num_pages(soup):
    if soup.find('span', {'itemprop': 'numberOfPages'}):
        num_pages = soup.find('span', {'itemprop': 'numberOfPages'}).text.strip()
        return int(num_pages.split()[0])
    return ''


def get_year_first_published(soup):
    year_first_published = soup.find('nobr', attrs={'class': 'greyText'})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search('([0-9]{3,4})', year_first_published).group(1)
    else:
        return None


def get_description(soup):
    return soup.find('div', {'id': 'description'}).findAll('span')[-1].text


def get_id(book_id):
    pattern = re.compile("([^.-]+)")
    return pattern.search(book_id).group()


def scrape_book(book_id):
    url = 'https://www.goodreads.com/book/show/' + book_id
    source = urlopen(url)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    return {'book_id_title': book_id,
            'book_id': get_id(book_id),
            'book_title': ' '.join(soup.find('h1', {'id': 'bookTitle'}).text.split()),
            'book_description': get_description(soup),
            'book_url': url,
            'book_image': soup.find('img', {'id': 'coverImage'}).attrs.get('src'),
            'book_series': get_series_name(soup),
            'book_series_uri': get_series_uri(soup),
            'year_first_published': get_year_first_published(soup),
            'author': ' '.join(soup.find('span', {'itemprop': 'name'}).text.split()),
            'author_url': soup.find('a', {'class': 'authorName'}).attrs.get('href'),
            'num_pages': get_num_pages(soup),
            'genres': get_genres(soup),
            'num_ratings': int(soup.find('meta', {'itemprop': 'ratingCount'})['content'].strip()),
            'num_reviews': int(soup.find('meta', {'itemprop': 'reviewCount'})['content'].strip()),
            'average_rating': float(soup.find('span', {'itemprop': 'ratingValue'}).text.strip()),
            'rating_distribution': get_rating_distribution(soup)}
