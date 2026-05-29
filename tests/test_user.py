import json
from argparse import Namespace

import pytest

from scraper import user

# Profile parsers must work on both the logged-out and logged-in page.
PROFILE = ["profile.html", "profile_anon.html"]


@pytest.mark.parametrize("fixture", PROFILE)
def test_get_user_name(soup, fixture):
    assert user.get_user_name(soup(fixture)) == "Yash Totale"


@pytest.mark.parametrize("fixture", PROFILE)
def test_get_num_ratings(soup, fixture):
    assert user.get_num_ratings(soup(fixture)) == 81


@pytest.mark.parametrize("fixture", PROFILE)
def test_get_avg_rating(soup, fixture):
    assert user.get_avg_rating(soup(fixture)) == 4.12


@pytest.mark.parametrize("fixture", PROFILE)
def test_get_num_reviews(soup, fixture):
    assert user.get_num_reviews(soup(fixture)) == 3


async def test_get_user_info_writes_user_json(tmp_path, mock_get_soup):
    mock_get_soup({"user/show": "profile.html"})
    args = Namespace(
        skip_user_info=False,
        skip_shelves=True,
        user_id="54739262",
        output_dir=tmp_path,
    )

    await user.get_user_info(args)

    data = json.loads((tmp_path / "user.json").read_text())
    assert data == {
        "user_id": "54739262",
        "user_name": "Yash Totale",
        "num_ratings": 81,
        "average_rating": 4.12,
        "num_reviews": 3,
    }
